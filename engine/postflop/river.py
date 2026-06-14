"""Exact heads-up river solver.

On the river there are no more cards to come, so the spot is a finite 2-player
zero-sum game with *no approximation*: showdowns are decided exactly by
:func:`engine.eval7.evaluate7`. Each player holds a range over the 2-card combos
that don't use a board card; the solver carries a per-hand range vector and runs
vectorized CFR over the betting tree (like the preflop solver), with:

  - ``W[a, b]``  = +1 if hand a beats hand b at showdown, -1 if it loses, 0 tie
                   or if the two hands share a card (impossible matchup),
  - ``M[a, b]``  = 1 if hands a and b are card-disjoint, else 0 (card removal).

This is the same "public tree + private ranges" machinery, so it cross-validates
against the generic CFRSolver. Turn/flop (multi-street, needs card abstraction)
are deferred.
"""
from __future__ import annotations

import numpy as np

from engine.eval7 import evaluate7
from engine.preflop.tree import Node, _assign_paths

OOP, IP = 0, 1
_RANKS = "23456789TJQKA"
_SUITS = "shdc"


def card_str(card: int) -> str:
    return _RANKS[card % 13] + _SUITS[card // 13]


def parse_card(text: str) -> int:
    return _SUITS.index(text[1]) * 13 + _RANKS.index(text[0])


def enumerate_hands(board: list[int]) -> list[tuple[int, int]]:
    """All 2-card combos that avoid the board (C(47,2) = 1081 for a 5-card board)."""
    deck = [c for c in range(52) if c not in set(board)]
    hands = []
    for i in range(len(deck)):
        for j in range(i + 1, len(deck)):
            hands.append((deck[i], deck[j]))
    return hands


def showdown_matrices(board: list[int], hands: list[tuple[int, int]]):
    """Return (W, M): win-sign matrix and card-disjoint mask over ``hands``."""
    n = len(hands)
    # evaluate7 returns a comparable tuple; map distinct tuples to an int strength.
    tuples = [evaluate7([a, b, *board]) for a, b in hands]
    order = {t: i for i, t in enumerate(sorted(set(tuples)))}
    strength = np.array([order[t] for t in tuples])

    cards = np.array(hands)  # (n, 2)
    W = np.sign(strength[:, None] - strength[None, :]).astype(np.float64)
    # card-disjoint mask
    a0, a1 = cards[:, 0][:, None], cards[:, 1][:, None]
    b0, b1 = cards[:, 0][None, :], cards[:, 1][None, :]
    conflict = (a0 == b0) | (a0 == b1) | (a1 == b0) | (a1 == b1)
    M = (~conflict).astype(np.float64)
    W = W * M  # impossible matchups contribute nothing
    return W, M


def build_river_tree(pot: float, stack: float) -> Node:
    """OOP acts first. Single pot-sized bet, raise = all-in. Terminals: fold/showdown."""
    bet = pot

    def fold(c, folder):
        return Node(None, (c[0], c[1]), is_terminal=True, kind="fold", folder=folder)

    def show(c):
        return Node(None, (c[0], c[1]), is_terminal=True, kind="showdown")

    def facing_allin(c, to_act):
        opp = 1 - to_act
        n = Node(to_act, (c[0], c[1]), actions=["fold", "call"])
        n.children["fold"] = fold(c, to_act)
        called = list(c)
        called[to_act] = c[opp]
        n.children["call"] = show(called)
        return n

    def facing_bet(c, to_act):
        opp = 1 - to_act
        n = Node(to_act, (c[0], c[1]), actions=["fold", "call"])
        n.children["fold"] = fold(c, to_act)
        called = list(c)
        called[to_act] = c[opp]
        n.children["call"] = show(called)
        if c[opp] < stack - 1e-9:  # room to jam over the bet
            ac = list(c)
            ac[to_act] = stack
            n.actions.append("allin")
            n.children["allin"] = facing_allin(ac, opp)
        return n

    def after_check(c):  # IP acts with no bet outstanding
        n = Node(IP, (c[0], c[1]), actions=["check"])
        n.children["check"] = show(c)
        if bet < stack - 1e-9:
            bc = list(c)
            bc[IP] = bet
            n.actions.append("bet")
            n.children["bet"] = facing_bet(bc, OOP)
        ac = list(c)
        ac[IP] = stack
        n.actions.append("allin")
        n.children["allin"] = facing_allin(ac, OOP)
        return n

    root = Node(OOP, (0.0, 0.0), actions=["check"])
    root.children["check"] = after_check([0.0, 0.0])
    if bet < stack - 1e-9:
        bc = [0.0, 0.0]
        bc[OOP] = bet
        root.actions.append("bet")
        root.children["bet"] = facing_bet(bc, IP)
    ac = [0.0, 0.0]
    ac[OOP] = stack
    root.actions.append("allin")
    root.children["allin"] = facing_allin(ac, IP)
    _assign_paths(root, "")
    return root


class RiverSolver:
    def __init__(self, n, W, M, pot, stack, probs=None, labels=None, variant="cfr_plus"):
        self.n = n
        self.W = np.asarray(W, dtype=float)
        self.M = np.asarray(M, dtype=float)
        self.pot = float(pot)
        self.stack = float(stack)
        self.labels = labels
        self.variant = variant
        self._iter = 0
        p = np.ones(n) if probs is None else np.asarray(probs, dtype=float)
        self.p = p / p.sum()
        self.root = build_river_tree(pot, stack)
        self.regret: dict[str, np.ndarray] = {}
        self.strat_sum: dict[str, np.ndarray] = {}
        for node in self.root.decision_nodes():
            shape = (n, len(node.actions))
            self.regret[node.path] = np.zeros(shape)
            self.strat_sum[node.path] = np.zeros(shape)

    @classmethod
    def from_board(cls, board, pot, stack, probs=None, variant="cfr_plus"):
        hands = enumerate_hands(board)
        W, M = showdown_matrices(board, hands)
        labels = [card_str(a) + card_str(b) for a, b in hands]
        return cls(len(hands), W, M, pot, stack, probs=probs, labels=labels, variant=variant)

    def _sigma(self, node):
        regret = self.regret[node.path]
        pos = np.maximum(regret, 0.0)
        total = pos.sum(axis=1, keepdims=True)
        safe = np.where(total > 0, total, 1.0)
        uniform = np.full_like(regret, 1.0 / regret.shape[1])
        return np.where(total > 0, pos / safe, uniform)

    def _terminal_value(self, node, reach_opp, player):
        if node.kind == "fold":
            if node.folder == OOP:
                net_oop = -(self.pot / 2 + node.contrib[OOP])
            else:
                net_oop = self.pot / 2 + node.contrib[IP]
            const = net_oop if player == OOP else -net_oop
            return const * (self.M @ reach_opp)
        stake = self.pot / 2 + node.contrib[0]  # equal contributions at showdown
        return stake * (self.W @ reach_opp)

    def _walk(self, node, reach_p, reach_opp, player):
        if node.is_terminal:
            return self._terminal_value(node, reach_opp, player)
        if node.player == player:
            sigma = self._sigma(node)
            vals = [
                self._walk(node.children[a], reach_p * sigma[:, k], reach_opp, player)
                for k, a in enumerate(node.actions)
            ]
            value = np.zeros(self.n)
            for k in range(len(node.actions)):
                value += sigma[:, k] * vals[k]
            regret = self.regret[node.path]
            for k in range(len(node.actions)):
                regret[:, k] += vals[k] - value
            if self.variant == "cfr_plus":
                np.maximum(regret, 0.0, out=regret)
                weight = self._iter
            else:
                weight = 1.0
            self.strat_sum[node.path] += (reach_p[:, None] * sigma) * weight
            return value
        osigma = self._sigma(node)
        value = np.zeros(self.n)
        for k, a in enumerate(node.actions):
            value += self._walk(node.children[a], reach_p, reach_opp * osigma[:, k], player)
        return value

    def run(self, iterations):
        for _ in range(iterations):
            self._iter += 1
            for player in (OOP, IP):
                self._walk(self.root, self.p.copy(), self.p.copy(), player)

    def oop_ev(self):
        total = 0.0

        def walk(node, reach_oop, reach_ip):
            nonlocal total
            if node.is_terminal:
                if node.kind == "fold":
                    if node.folder == OOP:
                        net = -(self.pot / 2 + node.contrib[OOP])
                    else:
                        net = self.pot / 2 + node.contrib[IP]
                    total += net * (reach_oop @ self.M @ reach_ip)
                else:
                    stake = self.pot / 2 + node.contrib[0]
                    total += stake * (reach_oop @ self.W @ reach_ip)
                return
            sigma = self._sigma(node)
            for k, a in enumerate(node.actions):
                if node.player == OOP:
                    walk(node.children[a], reach_oop * sigma[:, k], reach_ip)
                else:
                    walk(node.children[a], reach_oop, reach_ip * sigma[:, k])

        walk(self.root, self.p.copy(), self.p.copy())
        return total

    def node_strategy(self, node):
        if self.variant == "cfr":
            ssum = self.strat_sum[node.path]
            total = ssum.sum(axis=1, keepdims=True)
            safe = np.where(total > 0, total, 1.0)
            uniform = np.full_like(ssum, 1.0 / ssum.shape[1])
            return np.where(total > 0, ssum / safe, uniform)
        return self._sigma(node)


def solve_river(board, pot=10.0, stack=20.0, iterations=400) -> dict:
    """Solve a HU river spot (uniform ranges). Returns per-node strategy summaries."""
    solver = RiverSolver.from_board(board, pot, stack)
    solver.run(iterations)
    nodes = {}
    for node in solver.root.decision_nodes():
        strat = solver.node_strategy(node)
        # combo-weighted action frequencies across the (uniform) range
        freq = {a: float(strat[:, k].mean()) for k, a in enumerate(node.actions)}
        nodes[node.path] = {"player": node.player, "actions": node.actions, "freq": freq}
    return {
        "board": [card_str(c) for c in board],
        "pot": pot,
        "stack": stack,
        "oop_ev": solver.oop_ev(),
        "nodes": nodes,
    }
