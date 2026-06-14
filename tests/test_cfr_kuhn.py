from engine.cfr import CFRSolver
from engine.games.kuhn import KuhnPoker


def test_kuhn_game_value_converges():
    g = KuhnPoker()
    solver = CFRSolver(g, variant="cfr")
    solver.run(20000)
    # Known result: the game value for the first player is -1/18.
    assert abs(solver.game_value() - (-1 / 18)) < 5e-3


def test_kuhn_strategy_alpha_relationship():
    g = KuhnPoker()
    solver = CFRSolver(g, variant="cfr")
    solver.run(20000)
    avg = solver.average_strategy()
    # First player bets the Jack ("0:") with probability alpha in [0, 1/3],
    # and every equilibrium satisfies P(bet King) = 3 * P(bet Jack).
    alpha = avg["0:"]["b"]
    assert 0.0 <= alpha <= 0.34
    assert abs(avg["2:"]["b"] - 3 * alpha) < 0.06


def test_cfr_plus_also_converges():
    g = KuhnPoker()
    solver = CFRSolver(g, variant="cfr_plus")
    solver.run(2000)
    assert abs(solver.game_value() - (-1 / 18)) < 5e-3
