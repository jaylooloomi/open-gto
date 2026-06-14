from engine.preflop.realization import fold_value, seeflop_value, showdown_value


def test_fold_value_bb_folds():
    # SB committed 3, BB committed 1, BB folds -> SB wins BB's 1.
    assert fold_value(1, (3.0, 1.0)) == (1.0, -1.0)


def test_fold_value_sb_folds():
    assert fold_value(0, (0.5, 1.0)) == (-0.5, 0.5)


def test_showdown_coinflip_is_zero_ev():
    net_sb, net_bb = showdown_value(0.5, 10.0)
    assert abs(net_sb) < 1e-9 and abs(net_bb) < 1e-9


def test_showdown_edge_scales_with_stake():
    assert abs(showdown_value(0.6, 10.0)[0] - 2.0) < 1e-9  # (1.2-1)*10


def test_seeflop_coinflip_is_zero():
    assert abs(seeflop_value(0.5, (2.5, 2.5))[0]) < 1e-9


def test_seeflop_realization_shrinks_edge():
    full = seeflop_value(0.7, (5.0, 5.0), realization=1.0)[0]
    half = seeflop_value(0.7, (5.0, 5.0), realization=0.5)[0]
    assert abs(half - full / 2) < 1e-9
