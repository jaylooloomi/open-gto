"""Vectorized CFR over the public preflop betting tree.

Each player carries a per-hand *range vector* (length n). At a decision node the
acting player keeps a per-hand regret/strategy matrix over that node's actions.
Terminal values are computed against the opponent's reach vector via the equity
matrix ``A = 2E - 1`` (antisymmetric), exactly like the push/fold solver — so the
whole iteration is a handful of matrix-vector products per node.

This is the "public tree + private ranges" architecture real solvers use, and it
is reusable for postflop later. Cross-validated against the generic ``CFRSolver``
on a tiny instance (see tests).
"""
from __future__ import annotations

import numpy as np

from engine.equity import COMBO_WEIGHTS, HANDS_169, get_equity_matrix
from engine.preflop.realization import DEFAULT_IP_PREMIUM, DEFAULT_REALIZATION
from engine.preflop.tree import BB, SB, Node, build_tree


class PreflopSolver:
    def __init__(
        self,
        stack_bb: float,
        probs=None,
        equity=None,
        sizes=None,
        realization: float = DEFAULT_REALIZATION,
        ip_premium: float = DEFAULT_IP_PREMIUM,
        allow_limp: bool = False,
        variant: str = "cfr_plus",
    ):
        self.E = get_equity_matrix() if equity is None else np.asarray(equity, dtype=float)
        weights = COMBO_WEIGHTS if probs is None else np.asarray(probs, dtype=float)
        self.p = weights / weights.sum()
        self.n = len(self.p)
        self.A = 2.0 * self.E - 1.0
        self.R = float(realization)
        self.ip_premium = float(ip_premium)
        self.root = build_tree(stack_bb, sizes, allow_limp=allow_limp)
        self.variant = variant
        self._iter = 0
        self.regret: dict[str, np.ndarray] = {}
        self.strat_sum: dict[str, np.ndarray] = {}
        for node in self.root.decision_nodes():
            shape = (self.n, len(node.actions))
            self.regret[node.path] = np.zeros(shape)
            self.strat_sum[node.path] = np.zeros(shape)

    def _sigma(self, node: Node) -> np.ndarray:
        regret = self.regret[node.path]
        pos = np.maximum(regret, 0.0)
        total = pos.sum(axis=1, keepdims=True)
        safe = np.where(total > 0, total, 1.0)
        uniform = np.full_like(regret, 1.0 / regret.shape[1])
        return np.where(total > 0, pos / safe, uniform)

    def _terminal_value(self, node: Node, reach_opp: np.ndarray, player: int) -> np.ndarray:
        if node.kind == "fold":
            net_sb = -node.contrib[0] if node.folder == SB else node.contrib[1]
            const = net_sb if player == SB else -net_sb
            return np.full(self.n, const * reach_opp.sum())
        stake = node.contrib[0]
        if node.kind == "seeflop":
            value = stake * self.R * (self.A @ reach_opp)
            sign = 1.0 if player == SB else -1.0  # IP premium goes to the SB (button)
            return value + sign * self.ip_premium * stake * reach_opp.sum()
        # showdown
        return stake * (self.A @ reach_opp)

    def _walk(self, node: Node, reach_p: np.ndarray, reach_opp: np.ndarray, player: int) -> np.ndarray:
        if node.is_terminal:
            return self._terminal_value(node, reach_opp, player)

        if node.player == player:
            sigma = self._sigma(node)
            action_vals = [
                self._walk(node.children[a], reach_p * sigma[:, k], reach_opp, player)
                for k, a in enumerate(node.actions)
            ]
            value = np.zeros(self.n)
            for k in range(len(node.actions)):
                value += sigma[:, k] * action_vals[k]
            regret = self.regret[node.path]
            for k in range(len(node.actions)):
                regret[:, k] += action_vals[k] - value
            if self.variant == "cfr_plus":
                np.maximum(regret, 0.0, out=regret)
                weight = self._iter
            else:
                weight = 1.0
            self.strat_sum[node.path] += (reach_p[:, None] * sigma) * weight
            return value

        # Opponent node: split opponent reach by their strategy.
        osigma = self._sigma(node)
        value = np.zeros(self.n)
        for k, a in enumerate(node.actions):
            value += self._walk(node.children[a], reach_p, reach_opp * osigma[:, k], player)
        return value

    def run(self, iterations: int) -> None:
        for _ in range(iterations):
            self._iter += 1
            for player in (SB, BB):
                self._walk(self.root, self.p.copy(), self.p.copy(), player)

    def sb_ev(self) -> float:
        """Expected value to the SB under the current strategies (clean pass)."""
        total = 0.0

        def walk(node: Node, reach_sb: np.ndarray, reach_bb: np.ndarray) -> None:
            nonlocal total
            if node.is_terminal:
                if node.kind == "fold":
                    net_sb = -node.contrib[0] if node.folder == SB else node.contrib[1]
                    total += net_sb * reach_sb.sum() * reach_bb.sum()
                else:
                    stake = node.contrib[0]
                    if node.kind == "seeflop":
                        total += stake * self.R * (reach_sb @ self.A @ reach_bb)
                        total += self.ip_premium * stake * reach_sb.sum() * reach_bb.sum()
                    else:
                        total += stake * (reach_sb @ self.A @ reach_bb)
                return
            sigma = self._sigma(node)
            for k, a in enumerate(node.actions):
                if node.player == SB:
                    walk(node.children[a], reach_sb * sigma[:, k], reach_bb)
                else:
                    walk(node.children[a], reach_sb, reach_bb * sigma[:, k])

        walk(self.root, self.p.copy(), self.p.copy())
        return total

    def node_strategy(self, node: Node) -> np.ndarray:
        """Per-hand strategy (n, num_actions) for a decision node."""
        if self.variant == "cfr":
            ssum = self.strat_sum[node.path]
            total = ssum.sum(axis=1, keepdims=True)
            safe = np.where(total > 0, total, 1.0)
            uniform = np.full_like(ssum, 1.0 / ssum.shape[1])
            return np.where(total > 0, ssum / safe, uniform)
        return self._sigma(node)

    def node_chart(self, node: Node) -> dict:
        """{hand_label: {action: freq}} for a decision node (169-class only)."""
        strat = self.node_strategy(node)
        labels = HANDS_169 if self.n == len(HANDS_169) else [str(i) for i in range(self.n)]
        return {
            labels[h]: {a: float(strat[h, k]) for k, a in enumerate(node.actions)}
            for h in range(self.n)
        }


def _serialize(node: Node) -> dict:
    return {
        "path": node.path,
        "player": node.player,
        "is_terminal": node.is_terminal,
        "kind": node.kind,
        "actions": list(node.actions),
        "contrib": list(node.contrib),
        "children": {a: c.path for a, c in node.children.items()},
    }


def solve_preflop_hu(stack_bb: float, iterations: int = 1000, variant: str = "cfr_plus") -> dict:
    """Solve full 169-class HU preflop; return the tree + per-node charts.

    Returns ``{stack_bb, sb_ev, root, nodes}`` where ``nodes`` maps each node's
    path to its serialized form (decision nodes also carry a ``chart``).
    """
    solver = PreflopSolver(stack_bb, variant=variant)
    solver.run(iterations)
    nodes: dict[str, dict] = {}

    def walk(node: Node) -> None:
        info = _serialize(node)
        if not node.is_terminal:
            info["chart"] = solver.node_chart(node)
        nodes[node.path] = info
        for child in node.children.values():
            walk(child)

    walk(solver.root)
    return {
        "stack_bb": stack_bb,
        "sb_ev": solver.sb_ev(),
        "root": solver.root.path,
        "nodes": nodes,
    }
