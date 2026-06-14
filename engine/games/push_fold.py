"""Heads-up NLHE preflop push/fold (jam-or-fold).

The small blind (button) posts 0.5, the big blind posts 1, and effective stacks
are ``stack_bb``. The SB either jams all-in or folds; facing a jam the BB calls
or folds. Net payoffs (in big blinds), from the SB's perspective:

  SB folds            -> -0.5
  SB jams, BB folds   -> +1.0
  SB jams, BB calls   -> (2 * equity - 1) * stack_bb   (showdown)

Two solvers live here:

* :class:`PushFoldGame` expresses the spot as a generic
  :class:`~engine.game.ExtensiveFormGame`, so the validated CFR engine can solve
  small instances. It enumerates n^2 deals, so it is only practical for tiny n.
* :class:`PushFoldSolver` is a vectorized CFR+ over the full 169x169 equity
  matrix -- the production path. It is cross-checked against the generic engine.

Both treat the two players' hands as independent (combo-weighted), i.e. they
ignore card removal between the hole cards. This is a deliberate MVP
simplification documented in the design spec.
"""
from __future__ import annotations

import numpy as np

from engine.equity import COMBO_WEIGHTS, HANDS_169, get_equity_matrix
from engine.game import ExtensiveFormGame


class PushFoldGame(ExtensiveFormGame):
    """Generic extensive-form push/fold over ``n`` abstract hand classes."""

    num_players = 2

    def __init__(self, probs, equity, stack_bb: float):
        self.p = np.asarray(probs, dtype=float)
        self.p = self.p / self.p.sum()
        self.E = np.asarray(equity, dtype=float)
        self.S = float(stack_bb)
        self.n = len(self.p)

    def initial_state(self):
        return ("deal",)

    def is_terminal(self, state) -> bool:
        return state[0] in ("tf", "tbf", "tc")

    def is_chance(self, state) -> bool:
        return state[0] == "deal"

    def current_player(self, state) -> int:
        return 0 if state[0] == "sb" else 1

    def legal_actions(self, state):
        return ("jam", "fold") if state[0] == "sb" else ("call", "fold")

    def chance_outcomes(self, state):
        return [
            ((i, j), float(self.p[i] * self.p[j]))
            for i in range(self.n)
            for j in range(self.n)
        ]

    def next_state(self, state, action):
        if state[0] == "deal":
            i, j = action
            return ("sb", i, j)
        _, i, j = state
        if state[0] == "sb":
            return ("bb", i, j) if action == "jam" else ("tf", i, j)
        return ("tc", i, j) if action == "call" else ("tbf", i, j)

    def infoset_key(self, state) -> str:
        _, i, j = state
        return f"sb:{i}" if state[0] == "sb" else f"bb:{j}"

    def terminal_utility(self, state, player) -> float:
        kind, i, j = state
        if kind == "tf":
            net0 = -0.5
        elif kind == "tbf":
            net0 = 1.0
        else:  # showdown
            net0 = (2.0 * self.E[i, j] - 1.0) * self.S
        return net0 if player == 0 else -net0


class PushFoldSolver:
    """Vectorized CFR+ solver for push/fold over hand classes."""

    def __init__(self, stack_bb: float, probs=None, equity=None, variant: str = "cfr_plus"):
        self.E = get_equity_matrix() if equity is None else np.asarray(equity, dtype=float)
        weights = COMBO_WEIGHTS if probs is None else np.asarray(probs, dtype=float)
        self.p = weights / weights.sum()
        self.S = float(stack_bb)
        self.A = 2.0 * self.E - 1.0  # SB net per stack at showdown; antisymmetric
        self.variant = variant
        self.n = len(self.p)
        self._iter = 0
        self.regret_sb = np.zeros((self.n, 2))  # [jam, fold]
        self.regret_bb = np.zeros((self.n, 2))  # [call, fold]
        self.sum_sb = np.zeros((self.n, 2))
        self.sum_bb = np.zeros((self.n, 2))

    @staticmethod
    def _match(regret: np.ndarray) -> np.ndarray:
        pos = np.maximum(regret, 0.0)
        total = pos.sum(axis=1, keepdims=True)
        safe = np.where(total > 0, total, 1.0)  # avoid 0/0; rows fixed up below
        return np.where(total > 0, pos / safe, 0.5)

    def run(self, iterations: int) -> None:
        for _ in range(iterations):
            self._iter += 1
            s_sb = self._match(self.regret_sb)
            s_bb = self._match(self.regret_bb)
            jam, call = s_sb[:, 0], s_bb[:, 0]

            # SB action values (proper expectation over BB's hand).
            bb_call_vec = self.p * call
            bb_fold_mass = 1.0 - bb_call_vec.sum()
            v_jam = bb_fold_mass * 1.0 + self.S * (self.A @ bb_call_vec)
            v_fold = np.full(self.n, -0.5)
            v_sb = jam * v_jam + (1.0 - jam) * v_fold
            self.regret_sb[:, 0] += self.p * (v_jam - v_sb)
            self.regret_sb[:, 1] += self.p * (v_fold - v_sb)

            # BB action values (counterfactual: weighted by SB's jam reach).
            sb_jam_vec = self.p * jam
            sb_jam_mass = sb_jam_vec.sum()
            v_call = self.S * (self.A @ sb_jam_vec)
            v_bfold = np.full(self.n, -1.0 * sb_jam_mass)
            v_bb = call * v_call + (1.0 - call) * v_bfold
            self.regret_bb[:, 0] += self.p * (v_call - v_bb)
            self.regret_bb[:, 1] += self.p * (v_bfold - v_bb)

            if self.variant == "cfr_plus":
                np.maximum(self.regret_sb, 0.0, out=self.regret_sb)
                np.maximum(self.regret_bb, 0.0, out=self.regret_bb)
                weight = self._iter
            else:
                weight = 1.0
            self.sum_sb += weight * s_sb
            self.sum_bb += weight * s_bb

    def _solution(self, regret: np.ndarray, ssum: np.ndarray) -> np.ndarray:
        if self.variant == "cfr":
            total = ssum.sum(axis=1, keepdims=True)
            return np.where(total > 0, ssum / total, 0.5)
        return self._match(regret)

    def sb_jam_freqs(self) -> np.ndarray:
        return self._solution(self.regret_sb, self.sum_sb)[:, 0]

    def bb_call_freqs(self) -> np.ndarray:
        return self._solution(self.regret_bb, self.sum_bb)[:, 0]

    def exploitability(self) -> float:
        """Nash gap: total gain both players get by best-responding. 0 == Nash."""
        jam = self._match(self.regret_sb)[:, 0]
        call = self._match(self.regret_bb)[:, 0]

        bb_call_vec = self.p * call
        bb_fold_mass = 1.0 - bb_call_vec.sum()
        v_jam = bb_fold_mass + self.S * (self.A @ bb_call_vec)
        v_fold = np.full(self.n, -0.5)
        v_sb = jam * v_jam + (1.0 - jam) * v_fold
        delta_sb = (self.p * (np.maximum(v_jam, v_fold) - v_sb)).sum()

        sb_jam_vec = self.p * jam
        sb_jam_mass = sb_jam_vec.sum()
        v_call = self.S * (self.A @ sb_jam_vec)
        v_bfold = np.full(self.n, -1.0 * sb_jam_mass)
        v_bb = call * v_call + (1.0 - call) * v_bfold
        delta_bb = (self.p * (np.maximum(v_call, v_bfold) - v_bb)).sum()

        return float(delta_sb + delta_bb)

    def sb_jam_chart(self) -> dict[str, float]:
        return {h: float(f) for h, f in zip(HANDS_169, self.sb_jam_freqs())}

    def bb_call_chart(self) -> dict[str, float]:
        return {h: float(f) for h, f in zip(HANDS_169, self.bb_call_freqs())}


def solve_push_fold(stack_bb: float, iterations: int = 1500, variant: str = "cfr_plus") -> dict:
    """Solve the full 169-class push/fold spot; returns SB jam and BB call charts."""
    solver = PushFoldSolver(stack_bb, variant=variant)
    solver.run(iterations)
    return {
        "stack_bb": stack_bb,
        "sb_jam": solver.sb_jam_chart(),
        "bb_call": solver.bb_call_chart(),
        "exploitability": solver.exploitability(),
    }
