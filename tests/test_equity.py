from engine.equity import COMBO_WEIGHTS, HANDS_169, hand_vs_hand_equity


def test_169_hand_classes():
    assert len(HANDS_169) == 169
    assert len(set(HANDS_169)) == 169


def test_combo_weights_sum_to_1326():
    assert int(COMBO_WEIGHTS.sum()) == 1326  # C(52, 2)


def test_aa_dominates_trash():
    eq = hand_vs_hand_equity("AA", "72o", samples=3000, seed=3)
    assert eq > 0.85  # AA vs 72o ~ 0.88


def test_equity_is_complementary():
    a = hand_vs_hand_equity("AKs", "QQ", samples=3000, seed=4)
    b = hand_vs_hand_equity("QQ", "AKs", samples=3000, seed=4)
    assert abs(a + b - 1.0) < 0.05


def test_overcards_vs_underpair_is_a_coinflip():
    eq = hand_vs_hand_equity("AKs", "22", samples=4000, seed=5)
    assert 0.45 < eq < 0.55  # classic ~50/50 race
