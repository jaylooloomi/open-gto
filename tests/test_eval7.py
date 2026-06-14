from engine.eval7 import (
    FLUSH,
    FOUR_KIND,
    FULL_HOUSE,
    HIGH_CARD,
    ONE_PAIR,
    STRAIGHT,
    STRAIGHT_FLUSH,
    THREE_KIND,
    TWO_PAIR,
    evaluate7,
)

_RANKS = "23456789TJQKA"


def c(label: str, suit: int) -> int:
    """Card int from a rank label and suit 0..3, e.g. c('A', 0)."""
    return suit * 13 + _RANKS.index(label)


def test_category_ordering():
    royal = evaluate7([c("T", 0), c("J", 0), c("Q", 0), c("K", 0), c("A", 0), c("2", 1), c("3", 2)])
    quads = evaluate7([c("9", 0), c("9", 1), c("9", 2), c("9", 3), c("A", 0), c("2", 1), c("3", 2)])
    boat = evaluate7([c("9", 0), c("9", 1), c("9", 2), c("A", 0), c("A", 1), c("2", 1), c("3", 2)])
    flush = evaluate7([c("2", 0), c("5", 0), c("7", 0), c("9", 0), c("J", 0), c("A", 1), c("K", 2)])
    straight = evaluate7([c("5", 0), c("6", 1), c("7", 2), c("8", 3), c("9", 0), c("2", 1), c("A", 2)])
    trips = evaluate7([c("9", 0), c("9", 1), c("9", 2), c("A", 0), c("K", 1), c("2", 1), c("3", 2)])
    two_pair = evaluate7([c("9", 0), c("9", 1), c("A", 0), c("A", 1), c("K", 1), c("2", 1), c("3", 2)])
    pair = evaluate7([c("9", 0), c("9", 1), c("A", 0), c("K", 1), c("Q", 1), c("2", 1), c("3", 2)])
    high = evaluate7([c("9", 0), c("7", 1), c("A", 0), c("K", 1), c("Q", 1), c("2", 1), c("3", 2)])

    assert royal[0] == STRAIGHT_FLUSH
    assert quads[0] == FOUR_KIND
    assert boat[0] == FULL_HOUSE
    assert flush[0] == FLUSH
    assert straight[0] == STRAIGHT
    assert trips[0] == THREE_KIND
    assert two_pair[0] == TWO_PAIR
    assert pair[0] == ONE_PAIR
    assert high[0] == HIGH_CARD
    assert royal > quads > boat > flush > straight > trips > two_pair > pair > high


def test_wheel_straight_is_five_high():
    wheel = evaluate7([c("A", 0), c("2", 1), c("3", 2), c("4", 3), c("5", 0), c("K", 1), c("Q", 2)])
    six_high = evaluate7([c("2", 0), c("3", 1), c("4", 2), c("5", 3), c("6", 0), c("K", 1), c("Q", 2)])
    assert wheel[0] == STRAIGHT
    assert six_high[0] == STRAIGHT
    assert six_high > wheel  # 6-high beats the wheel


def test_flush_beats_higher_straight():
    flush = evaluate7([c("2", 0), c("4", 0), c("6", 0), c("8", 0), c("9", 0), c("A", 1), c("K", 2)])
    straight = evaluate7([c("T", 0), c("J", 1), c("Q", 2), c("K", 3), c("A", 0), c("2", 1), c("3", 2)])
    assert flush[0] == FLUSH
    assert straight[0] == STRAIGHT
    assert flush > straight


def test_two_pair_kicker_breaks_tie():
    aces_kings_q = evaluate7([c("A", 0), c("A", 1), c("K", 0), c("K", 1), c("Q", 2), c("2", 3), c("3", 0)])
    aces_kings_j = evaluate7([c("A", 2), c("A", 3), c("K", 2), c("K", 3), c("J", 0), c("2", 1), c("3", 1)])
    assert aces_kings_q > aces_kings_j


def test_straight_flush_beats_quads():
    sf = evaluate7([c("5", 0), c("6", 0), c("7", 0), c("8", 0), c("9", 0), c("9", 1), c("9", 2)])
    assert sf[0] == STRAIGHT_FLUSH  # not fooled by the trip 9s into a lower category
