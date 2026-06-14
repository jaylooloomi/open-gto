"""Preflop all-in equity for the 169 starting-hand classes.

Equities are estimated by Monte Carlo over board runouts using :mod:`engine.eval7`.
Because suits are symmetric preflop, one representative (card-disjoint) combo per
class pair is sampled. The full 169x169 matrix is cached to ``data/equity_169.npy``.

Index layout of :data:`HANDS_169`: 13 pocket pairs, then 78 suited, then 78
offsuit hands. :data:`COMBO_WEIGHTS` gives the number of card combinations per
class (pair=6, suited=4, offsuit=12), summing to 1326 = C(52, 2).
"""
from __future__ import annotations

import random
from pathlib import Path

import numpy as np

from engine.eval7 import evaluate7

_RANKS = "AKQJT98765432"            # display order, A high
_CARD_RANK = {ch: i for i, ch in enumerate("23456789TJQKA")}  # eval rank index
_DATA = Path(__file__).parent / "data"
_CACHE = _DATA / "equity_169.npy"


def _build_labels() -> list[str]:
    pairs = [r * 2 for r in _RANKS]
    suited, offsuit = [], []
    for i in range(13):
        for j in range(i + 1, 13):
            suited.append(_RANKS[i] + _RANKS[j] + "s")
            offsuit.append(_RANKS[i] + _RANKS[j] + "o")
    return pairs + suited + offsuit


HANDS_169 = _build_labels()
HAND_INDEX = {h: i for i, h in enumerate(HANDS_169)}


def _combo_weight(label: str) -> int:
    if len(label) == 2:
        return 6
    return 4 if label.endswith("s") else 12


COMBO_WEIGHTS = np.array([_combo_weight(h) for h in HANDS_169], dtype=float)


def _materialize(label: str, used: set[int]) -> list[int]:
    """Pick concrete cards (0..51) for a class label, avoiding ``used``."""
    if len(label) == 2:  # pocket pair
        r = _CARD_RANK[label[0]]
        chosen = [s * 13 + r for s in range(4) if s * 13 + r not in used]
        if len(chosen) >= 2:
            return chosen[:2]
        raise ValueError(f"cannot materialize {label}")
    hi, lo, kind = _CARD_RANK[label[0]], _CARD_RANK[label[1]], label[2]
    if kind == "s":
        for s in range(4):
            cards = [s * 13 + hi, s * 13 + lo]
            if cards[0] not in used and cards[1] not in used:
                return cards
    else:  # offsuit: different suits
        for s1 in range(4):
            for s2 in range(4):
                if s1 == s2:
                    continue
                cards = [s1 * 13 + hi, s2 * 13 + lo]
                if cards[0] not in used and cards[1] not in used:
                    return cards
    raise ValueError(f"cannot materialize {label} avoiding {used}")


def hand_vs_hand_equity(a: str, b: str, samples: int = 2000, seed: int = 0) -> float:
    """Monte Carlo equity of class ``a`` vs class ``b`` (wins + 0.5*ties)."""
    rng = random.Random(seed)
    ca = _materialize(a, set())
    cb = _materialize(b, set(ca))
    deck = [x for x in range(52) if x not in set(ca + cb)]
    wins = ties = 0
    for _ in range(samples):
        board = rng.sample(deck, 5)
        va = evaluate7(ca + board)
        vb = evaluate7(cb + board)
        if va > vb:
            wins += 1
        elif va == vb:
            ties += 1
    return (wins + 0.5 * ties) / samples


def build_equity_matrix(samples: int = 500, seed: int = 0) -> np.ndarray:
    """Compute the full 169x169 equity matrix (diagonal = 0.5 by symmetry)."""
    n = len(HANDS_169)
    matrix = np.full((n, n), 0.5)
    for i in range(n):
        for j in range(i + 1, n):
            eq = hand_vs_hand_equity(HANDS_169[i], HANDS_169[j], samples, seed + i * 169 + j)
            matrix[i, j] = eq
            matrix[j, i] = 1.0 - eq
    return matrix


def get_equity_matrix(samples: int = 500, seed: int = 0) -> np.ndarray:
    """Load the cached equity matrix, building and caching it on first use."""
    if _CACHE.exists():
        return np.load(_CACHE)
    matrix = build_equity_matrix(samples, seed)
    _DATA.mkdir(exist_ok=True)
    np.save(_CACHE, matrix)
    return matrix
