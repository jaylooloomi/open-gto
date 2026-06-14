"""A compact, correct 7-card poker hand evaluator.

Cards are ints 0..51 with ``rank = card % 13`` (0=2, 1=3, ..., 8=T, 9=J, 10=Q,
11=K, 12=A) and ``suit = card // 13``. :func:`evaluate7` returns a tuple whose
natural ordering ranks hands correctly: higher tuple == stronger hand.
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable

# Hand categories (higher is better).
STRAIGHT_FLUSH = 8
FOUR_KIND = 7
FULL_HOUSE = 6
FLUSH = 5
STRAIGHT = 4
THREE_KIND = 3
TWO_PAIR = 2
ONE_PAIR = 1
HIGH_CARD = 0


def _straight_high(desc_ranks) -> int | None:
    """Highest straight top-rank from a set of rank indices, else None.

    Handles the wheel (A-2-3-4-5) by treating the Ace (12) as also -1.
    """
    rs = set(desc_ranks)
    if 12 in rs:
        rs = rs | {-1}
    for high in range(12, 2, -1):  # down to 3 -> wheel (5-high straight)
        if all((high - i) in rs for i in range(5)):
            return high
    return None


def evaluate7(cards: Iterable[int]) -> tuple:
    cards = list(cards)
    ranks_desc = sorted((c % 13 for c in cards), reverse=True)
    rank_count = Counter(c % 13 for c in cards)
    suit_count = Counter(c // 13 for c in cards)

    flush_suit = next((s for s, n in suit_count.items() if n >= 5), None)
    flush_top5: tuple = ()
    if flush_suit is not None:
        flush_ranks = sorted(
            (c % 13 for c in cards if c // 13 == flush_suit), reverse=True
        )
        sf_high = _straight_high(flush_ranks)
        if sf_high is not None:
            return (STRAIGHT_FLUSH, sf_high)
        flush_top5 = tuple(flush_ranks[:5])

    by_count = sorted(rank_count.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
    if by_count[0][1] == 4:
        quad = by_count[0][0]
        kicker = max(r for r in rank_count if r != quad)
        return (FOUR_KIND, quad, kicker)

    trips = sorted((r for r, n in rank_count.items() if n == 3), reverse=True)
    pairs = sorted((r for r, n in rank_count.items() if n == 2), reverse=True)
    if trips and (len(trips) >= 2 or pairs):
        top_trip = trips[0]
        pair_candidates = trips[1:] + pairs
        return (FULL_HOUSE, top_trip, max(pair_candidates))

    if flush_suit is not None:
        return (FLUSH, *flush_top5)

    straight_high = _straight_high(set(c % 13 for c in cards))
    if straight_high is not None:
        return (STRAIGHT, straight_high)

    if trips:
        top_trip = trips[0]
        kickers = sorted((r for r in rank_count if r != top_trip), reverse=True)[:2]
        return (THREE_KIND, top_trip, *kickers)

    if len(pairs) >= 2:
        hi, lo = pairs[0], pairs[1]
        kicker = max(r for r in rank_count if r not in (hi, lo))
        return (TWO_PAIR, hi, lo, kicker)

    if len(pairs) == 1:
        p = pairs[0]
        kickers = sorted((r for r in rank_count if r != p), reverse=True)[:3]
        return (ONE_PAIR, p, *kickers)

    return (HIGH_CARD, *ranks_desc[:5])
