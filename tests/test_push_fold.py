import numpy as np
import pytest

from engine.cfr import CFRSolver
from engine.games.push_fold import PushFoldGame, PushFoldSolver, solve_push_fold


def _tiny_setup():
    # 3 abstract hands strong/medium/weak with an antisymmetric equity matrix.
    probs = np.array([1 / 3, 1 / 3, 1 / 3])
    equity = np.array(
        [
            [0.5, 0.7, 0.9],
            [0.3, 0.5, 0.7],
            [0.1, 0.3, 0.5],
        ]
    )
    return probs, equity


def test_vectorized_matches_generic_engine():
    # The vectorized push/fold CFR must agree with the validated generic CFR
    # engine on the same small game (cross-validation of the fast path's math).
    probs, equity = _tiny_setup()
    stack = 8.0

    generic = CFRSolver(PushFoldGame(probs, equity, stack), variant="cfr_plus")
    generic.run(8000)
    gstrat = generic.solution_strategy()
    g_jam = [gstrat[f"sb:{i}"]["jam"] for i in range(3)]
    g_call = [gstrat[f"bb:{j}"]["call"] for j in range(3)]

    vec = PushFoldSolver(stack, probs=probs, equity=equity, variant="cfr_plus")
    vec.run(8000)
    v_jam = vec.sb_jam_freqs()
    v_call = vec.bb_call_freqs()

    for i in range(3):
        assert abs(g_jam[i] - v_jam[i]) < 0.05
        assert abs(g_call[i] - v_call[i]) < 0.05


def test_strong_hand_always_jams_and_calls():
    probs, equity = _tiny_setup()
    vec = PushFoldSolver(6.0, probs=probs, equity=equity, variant="cfr_plus")
    vec.run(3000)
    # The strongest hand (index 0) should jam and call essentially always.
    assert vec.sb_jam_freqs()[0] > 0.95
    assert vec.bb_call_freqs()[0] > 0.95


@pytest.mark.slow
def test_full_169_short_stack_jams_wide():
    # At 2bb effective, the SB profitably jams almost everything.
    result = solve_push_fold(2.0, iterations=800)
    jam = np.array(list(result["sb_jam"].values()))
    assert jam.mean() > 0.9
    assert result["sb_jam"]["AA"] > 0.99


@pytest.mark.slow
def test_full_169_ten_bb_premium_jams_trash_folds():
    result = solve_push_fold(10.0, iterations=1500)
    assert result["sb_jam"]["AA"] > 0.99
    assert result["sb_jam"]["KK"] > 0.99
    assert result["sb_jam"]["72o"] < 0.5      # bottom of the range folds
    assert result["bb_call"]["AA"] > 0.99     # AA always calls a jam
