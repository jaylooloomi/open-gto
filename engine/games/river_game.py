"""Generic extensive-form river game over ``n`` abstract hands (cross-validation).

Used to check the vectorized :class:`RiverSolver` against the trusted generic
``CFRSolver``. No card removal (M = all ones) in this synthetic form.
"""
from __future__ import annotations

import numpy as np

from engine.game import ExtensiveFormGame
from engine.postflop.river import IP, OOP, build_river_tree


class RiverGame(ExtensiveFormGame):
    num_players = 2

    def __init__(self, win_matrix, pot, stack, probs=None):
        self.W = np.asarray(win_matrix, dtype=float)
        self.n = self.W.shape[0]
        self.pot = float(pot)
        self.stack = float(stack)
        p = np.ones(self.n) if probs is None else np.asarray(probs, dtype=float)
        self.p = p / p.sum()
        self.root = build_river_tree(pot, stack)

    def initial_state(self):
        return (None, -1, -1)

    def is_chance(self, state):
        return state[0] is None

    def is_terminal(self, state):
        return state[0] is not None and state[0].is_terminal

    def current_player(self, state):
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

    def infoset_key(self, state):
        node, i, j = state
        hand = i if node.player == OOP else j
        return f"{node.player}:{hand}:{node.path}"

    def terminal_utility(self, state, player):
        node, i, j = state
        if node.kind == "fold":
            if node.folder == OOP:
                net_oop = -(self.pot / 2 + node.contrib[OOP])
            else:
                net_oop = self.pot / 2 + node.contrib[IP]
        else:
            net_oop = (self.pot / 2 + node.contrib[0]) * self.W[i, j]
        return net_oop if player == OOP else -net_oop
