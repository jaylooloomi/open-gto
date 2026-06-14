import pytest

from engine.cfr import CFRSolver
from engine.exploitability import exploitability
from engine.games.leduc import LeducPoker, _legal, _replay


def test_private_deal_is_chance_30_outcomes():
    g = LeducPoker()
    s = g.initial_state()
    assert g.is_chance(s)
    outcomes = g.chance_outcomes(s)
    assert len(outcomes) == 30  # 6*5 ordered distinct deals
    assert abs(sum(p for _, p in outcomes) - 1.0) < 1e-9


def test_round1_opening_actions_are_check_or_bet():
    g = LeducPoker()
    s = g.next_state(g.initial_state(), (4, 2))  # P0=K, P1=Q
    assert list(g.legal_actions(s)) == ["k", "b"]
    assert g.current_player(s) == 0


def test_facing_a_bet_can_fold_call_or_raise_then_cap():
    assert _legal("b", 2) == ["f", "c", "r"]      # P1 faces P0's bet
    assert _legal("br", 2) == ["f", "c"]          # raise cap reached, no re-raise


def test_check_check_proceeds_to_board():
    g = LeducPoker()
    s = g.next_state(g.initial_state(), (4, 2))
    s = g.next_state(s, "k")
    s = g.next_state(s, "k")
    # round 1 closed by check-check -> deal board (chance)
    assert g.is_chance(s)
    assert len(g.chance_outcomes(s)) == 4  # 4 cards remain


def test_fold_terminal_payoff():
    g = LeducPoker()
    # P0=K, P1=Q; P0 bets 2, P1 folds. P0 net = +P1 contribution (just the ante 1).
    s = g.next_state(g.initial_state(), (4, 2))
    s = g.next_state(s, "b")
    s = g.next_state(s, "f")
    assert g.is_terminal(s)
    assert g.terminal_utility(s, 0) == 1.0
    assert g.terminal_utility(s, 1) == -1.0


def test_showdown_pair_beats_high_card():
    g = LeducPoker()
    # P0=Q(card2), P1=K(card4), board=Q(card3) -> P0 pairs the board and wins.
    # check-check round1, deal board, check-check round2 -> showdown, stake = ante 1.
    s = g.next_state(g.initial_state(), (2, 4))
    s = g.next_state(g.next_state(s, "k"), "k")
    s = g.next_state(s, 3)  # board = other Queen
    s = g.next_state(g.next_state(s, "k"), "k")
    assert g.is_terminal(s)
    assert g.terminal_utility(s, 0) == 1.0  # P0 wins ante from P1


def test_showdown_high_card_no_pair():
    g = LeducPoker()
    # P0=K(4), P1=Q(2), board=J(0) -> no pairs, K beats Q, P0 wins.
    s = g.next_state(g.initial_state(), (4, 2))
    s = g.next_state(g.next_state(s, "k"), "k")
    s = g.next_state(s, 0)
    s = g.next_state(g.next_state(s, "k"), "k")
    assert g.terminal_utility(s, 0) == 1.0


def test_leduc_has_288_infosets():
    # The known information-set count for Leduc poker; a structural sanity check.
    g = LeducPoker()
    solver = CFRSolver(g, variant="cfr_plus")
    solver.run(1)
    assert len(solver.nodes) == 288


@pytest.mark.slow
def test_leduc_cfr_plus_converges():
    # The engine generalizes beyond Kuhn: CFR+ drives Leduc exploitability down.
    g = LeducPoker()
    solver = CFRSolver(g, variant="cfr_plus")
    solver.run(20)
    baseline = exploitability(g, solver.solution_strategy())
    solver.run(280)  # 300 total
    converged = exploitability(g, solver.solution_strategy())
    assert converged < baseline
    assert converged < 0.1
