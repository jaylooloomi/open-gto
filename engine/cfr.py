"""Counterfactual Regret Minimization solver (CFR / CFR+ / DCFR).

All three variants share one tree traversal; they differ only in how cumulative
regret is updated and how the average strategy is weighted:

  - "cfr":      vanilla CFR. Regret matching; uniform-weighted average strategy.
                The AVERAGE strategy converges to a Nash equilibrium (O(1/sqrt(T))).
  - "cfr_plus": regret-matching+ (cumulative regret clamped at 0 each update) with
                linear averaging. ~1 order of magnitude faster than vanilla CFR.
  - "dcfr":     Discounted CFR. Cumulative positive/negative regret and the
                average-strategy accumulator are discounted each iteration by
                t^a/(t^a+1), t^b/(t^b+1), (t/(t+1))^g. Defaults a=3/2, b=0, g=2.

Refs: Zinkevich et al. 2007; Tammelin 2014 (CFR+); Brown & Sandholm 2019 (DCFR).
"""
from __future__ import annotations

import numpy as np

from engine.game import ExtensiveFormGame


class _Node:
    """Regret minimizer for a single information set."""

    __slots__ = ("actions", "regret_sum", "strategy_sum")

    def __init__(self, actions):
        self.actions = list(actions)
        n = len(self.actions)
        self.regret_sum = np.zeros(n)
        self.strategy_sum = np.zeros(n)

    def strategy(self) -> np.ndarray:
        positive = np.maximum(self.regret_sum, 0.0)
        total = positive.sum()
        if total > 0:
            return positive / total
        return np.full(len(self.actions), 1.0 / len(self.actions))


class CFRSolver:
    """Solve a two-player zero-sum :class:`ExtensiveFormGame` by self-play."""

    def __init__(self, game: ExtensiveFormGame, variant: str = "cfr_plus"):
        if variant not in ("cfr", "cfr_plus", "dcfr"):
            raise ValueError(f"unknown variant: {variant!r}")
        self.game = game
        self.variant = variant
        self.nodes: dict[str, _Node] = {}
        self._iter = 0
        self._dcfr = (1.5, 0.0, 2.0)  # alpha, beta, gamma

    def _node(self, key, actions) -> _Node:
        node = self.nodes.get(key)
        if node is None:
            node = _Node(actions)
            self.nodes[key] = node
        return node

    def run(self, iterations: int) -> None:
        # Alternating updates: each iteration updates one player against the
        # other's current strategy. This is the canonical form for CFR+ and
        # converges markedly faster than simultaneous updates.
        for _ in range(iterations):
            self._iter += 1
            if self.variant == "dcfr":
                self._apply_discount()
            player = self._iter % self.game.num_players
            self._walk(self.game.initial_state(), player, 1.0, 1.0)

    def _apply_discount(self) -> None:
        alpha, beta, gamma = self._dcfr
        t = self._iter
        pos_d = (t**alpha) / (t**alpha + 1)
        neg_d = (t**beta) / (t**beta + 1)
        strat_d = (t / (t + 1)) ** gamma
        for node in self.nodes.values():
            r = node.regret_sum
            node.regret_sum = np.where(r > 0, r * pos_d, r * neg_d)
            node.strategy_sum *= strat_d

    def _walk(self, state, player, reach_self, reach_opp) -> float:
        game = self.game
        if game.is_terminal(state):
            return game.terminal_utility(state, player)
        if game.is_chance(state):
            value = 0.0
            for action, prob in game.chance_outcomes(state):
                value += prob * self._walk(
                    game.next_state(state, action), player, reach_self, reach_opp * prob
                )
            return value

        cur = game.current_player(state)
        key = game.infoset_key(state)
        actions = game.legal_actions(state)
        node = self._node(key, actions)
        strategy = node.strategy()

        action_util = np.zeros(len(node.actions))
        node_util = 0.0
        for i, action in enumerate(node.actions):
            nxt = game.next_state(state, action)
            if cur == player:
                action_util[i] = self._walk(nxt, player, reach_self * strategy[i], reach_opp)
            else:
                action_util[i] = self._walk(nxt, player, reach_self, reach_opp * strategy[i])
            node_util += strategy[i] * action_util[i]

        if cur == player:
            regret = action_util - node_util
            node.regret_sum += reach_opp * regret
            if self.variant == "cfr_plus":
                np.maximum(node.regret_sum, 0.0, out=node.regret_sum)
                weight = reach_self * self._iter  # linear averaging
            else:
                weight = reach_self
            node.strategy_sum += weight * strategy
        return node_util

    def average_strategy(self) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for key, node in self.nodes.items():
            total = node.strategy_sum.sum()
            if total > 0:
                probs = node.strategy_sum / total
            else:
                probs = np.full(len(node.actions), 1.0 / len(node.actions))
            out[key] = {a: float(p) for a, p in zip(node.actions, probs)}
        return out

    def current_strategy(self) -> dict[str, dict]:
        return {
            key: {a: float(p) for a, p in zip(node.actions, node.strategy())}
            for key, node in self.nodes.items()
        }

    def solution_strategy(self) -> dict[str, dict]:
        """The strategy that converges to Nash for this variant.

        Vanilla CFR's *average* strategy converges; CFR+ and DCFR converge on
        the *current* strategy directly (empirically much faster). Downstream
        consumers (charts, API) should read the solution through this method.
        """
        if self.variant == "cfr":
            return self.average_strategy()
        return self.current_strategy()

    def game_value(self) -> float:
        """Expected value for player 0 under the average strategy."""
        from engine.exploitability import expected_value

        return expected_value(self.game, self.average_strategy(), 0)
