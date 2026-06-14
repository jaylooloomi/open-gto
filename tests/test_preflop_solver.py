import numpy as np
import pytest

from engine.cfr import CFRSolver
from engine.equity import COMBO_WEIGHTS
from engine.exploitability import expected_value
from engine.games.preflop_hu import PreflopHU
from engine.preflop.solver import PreflopSolver, solve_preflop_hu


def _tiny():
    probs = np.array([1 / 3, 1 / 3, 1 / 3])
    equity = np.array([[0.5, 0.6, 0.7], [0.4, 0.5, 0.6], [0.3, 0.4, 0.5]])
    return probs, equity


def test_preflop_hu_chance_outcomes():
    probs, equity = _tiny()
    g = PreflopHU(probs, equity, stack_bb=10)
    s = g.initial_state()
    assert g.is_chance(s)
    assert len(g.chance_outcomes(s)) == 9  # 3x3 deals
    assert abs(sum(p for _, p in g.chance_outcomes(s)) - 1.0) < 1e-9


def test_vectorized_matches_generic_game_value():
    # The equilibrium VALUE is unique in a 2p zero-sum game, so it is the robust
    # cross-check (action frequencies can differ between equally-valid equilibria,
    # e.g. 3bet vs jam with the nuts).
    probs, equity = _tiny()
    stack = 10
    game = PreflopHU(probs, equity, stack)
    gen = CFRSolver(game, variant="cfr_plus")
    gen.run(5000)
    gen_ev = expected_value(game, gen.solution_strategy(), 0)

    vec = PreflopSolver(stack, probs=probs, equity=equity, variant="cfr_plus")
    vec.run(5000)

    assert abs(gen_ev - vec.sb_ev()) < 0.02


def test_root_sb_strategy_agrees():
    # SB's first-in decision is well-reached and should match the generic engine.
    probs, equity = _tiny()
    stack = 10
    gen = CFRSolver(PreflopHU(probs, equity, stack), variant="cfr_plus")
    gen.run(5000)
    gstrat = gen.solution_strategy()
    vec = PreflopSolver(stack, probs=probs, equity=equity, variant="cfr_plus")
    vec.run(5000)
    vstrat = vec.node_strategy(vec.root)
    for hand in range(3):
        gen_row = gstrat[f"0:{hand}:"]
        for k, action in enumerate(vec.root.actions):
            assert abs(gen_row[action] - vstrat[hand, k]) < 0.08


@pytest.mark.slow
def test_full_169_preflop_ranges_are_sane():
    result = solve_preflop_hu(50.0, iterations=800)
    root = result["nodes"][""]["chart"]  # SB first-in
    assert root["AA"]["raise"] > 0.9
    assert root["72o"]["fold"] > 0.9

    # SB (button) opens a wide range heads-up.
    weights = COMBO_WEIGHTS / COMBO_WEIGHTS.sum()
    labels = list(root.keys())
    enters = sum(weights[i] * (1 - root[labels[i]]["fold"]) for i in range(169))
    assert enters > 0.6

    bb = result["nodes"]["raise"]["chart"]  # BB facing the open
    assert bb["AA"]["3bet"] + bb["AA"].get("allin", 0.0) > 0.9
    assert bb["72o"]["fold"] > 0.9
