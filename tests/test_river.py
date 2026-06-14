import numpy as np
import pytest

from engine.cfr import CFRSolver
from engine.exploitability import expected_value
from engine.games.river_game import RiverGame
from engine.postflop.river import (
    RiverSolver,
    enumerate_hands,
    parse_card,
    showdown_matrices,
    solve_river,
)


def test_enumerate_hands_count():
    board = [parse_card(c) for c in ["As", "Kd", "7h", "2c", "9s"]]
    assert len(enumerate_hands(board)) == 1081  # C(47, 2)


def test_showdown_matrices_properties():
    board = [parse_card(c) for c in ["As", "Kd", "7h", "2c", "9s"]]
    hands = enumerate_hands(board)
    W, M = showdown_matrices(board, hands)
    # W is antisymmetric; M is symmetric with a zero diagonal (a hand conflicts
    # with itself), and W is zero wherever hands conflict.
    assert np.allclose(W, -W.T)
    assert np.allclose(M, M.T)
    assert np.all(np.diag(M) == 0)
    assert np.all(W[M == 0] == 0)


def test_river_solver_matches_generic_game_value():
    # hand 0 beats all, hand 2 loses to all — a clean dominance ladder.
    W = np.array([[0, 1, 1], [-1, 0, 1], [-1, -1, 0]], dtype=float)
    M = np.ones((3, 3))
    pot, stack = 10.0, 20.0

    gen = CFRSolver(RiverGame(W, pot, stack), variant="cfr_plus")
    gen.run(5000)
    gen_ev = expected_value(RiverGame(W, pot, stack), gen.solution_strategy(), 0)

    vec = RiverSolver(3, W, M, pot, stack, variant="cfr_plus")
    vec.run(5000)

    assert abs(gen_ev - vec.oop_ev()) < 0.05


@pytest.mark.slow
def test_full_river_solve_runs_and_is_bounded():
    board = [parse_card(c) for c in ["As", "Kd", "7h", "2c", "9s"]]
    result = solve_river(board, pot=10.0, stack=20.0, iterations=200)
    assert len(result["nodes"]) > 0
    # OOP EV is bounded by the contested pot/stack — a sanity bound, not a fudge.
    assert -result["pot"] - result["stack"] < result["oop_ev"] < result["pot"] + result["stack"]
    # action frequencies at the root sum to ~1 per the (uniform) range average
    root = result["nodes"][""]
    assert abs(sum(root["freq"].values()) - 1.0) < 1e-6
