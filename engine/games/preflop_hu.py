"""Generic extensive-form HU preflop over ``n`` abstract hand classes.

Wraps the public betting tree so the validated generic ``CFRSolver`` can solve
*small* instances (n a few). Used to cross-validate the fast vectorized
``PreflopSolver``. Not used for the full 169-class solve (too slow — the chance
node deals n^2 hand pairs).
"""
from __future__ import annotations

import numpy as np

from engine.game import ExtensiveFormGame
from engine.preflop.realization import fold_value, seeflop_value, showdown_value
from engine.preflop.tree import build_tree


class PreflopHU(ExtensiveFormGame):
    num_players = 2

    def __init__(self, probs, equity, stack_bb, sizes=None, realization: float = 1.0):
        self.p = np.asarray(probs, dtype=float)
        self.p = self.p / self.p.sum()
        self.E = np.asarray(equity, dtype=float)
        self.n = len(self.p)
        self.root = build_tree(stack_bb, sizes)
        self.R = realization

    def initial_state(self):
        return (None, -1, -1)  # pre-deal

    def is_chance(self, state) -> bool:
        return state[0] is None

    def is_terminal(self, state) -> bool:
        return state[0] is not None and state[0].is_terminal

    def current_player(self, state) -> int:
        return state[0].player

    def legal_actions(self, state):
        return state[0].actions

    def chance_outcomes(self, state):
        return [
            ((i, j), float(self.p[i] * self.p[j]))
            for i in range(self.n)
            for j in range(self.n)
        ]

    def next_state(self, state, action):
        if state[0] is None:
            i, j = action
            return (self.root, i, j)
        node, i, j = state
        return (node.children[action], i, j)

    def infoset_key(self, state) -> str:
        node, i, j = state
        hand = i if node.player == 0 else j
        return f"{node.player}:{hand}:{node.path}"

    def terminal_utility(self, state, player) -> float:
        node, i, j = state
        if node.kind == "fold":
            net = fold_value(node.folder, node.contrib)
        elif node.kind == "showdown":
            net = showdown_value(float(self.E[i, j]), node.contrib[0])
        else:  # seeflop
            net = seeflop_value(float(self.E[i, j]), node.contrib, self.R)
        return net[0] if player == 0 else net[1]
