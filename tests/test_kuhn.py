from engine.games.kuhn import KuhnPoker


def test_initial_is_chance_and_deals_six_outcomes():
    g = KuhnPoker()
    s = g.initial_state()
    assert g.is_chance(s)
    outcomes = g.chance_outcomes(s)
    assert len(outcomes) == 6  # 3*2 ordered distinct deals
    assert abs(sum(p for _, p in outcomes) - 1.0) < 1e-9


def test_terminal_utility_bet_call_high_card_wins():
    g = KuhnPoker()
    # deal P0=K(2), P1=Q(1); P0 bets, P1 calls -> P0 wins the larger pot
    # ("b" is the bet/call action; "bb" = bet then call -> showdown)
    s = g.next_state(g.initial_state(), (2, 1))
    s = g.next_state(s, "b")
    s = g.next_state(s, "b")
    assert g.is_terminal(s)
    assert g.terminal_utility(s, 0) == 2.0
    assert g.terminal_utility(s, 1) == -2.0


def test_fold_to_bet_loses_one():
    g = KuhnPoker()
    # P0 bets, P1 folds ("p") -> P0 wins 1 regardless of cards
    s = g.next_state(g.initial_state(), (0, 2))  # P0 has worst card
    s = g.next_state(s, "b")
    s = g.next_state(s, "p")
    assert g.is_terminal(s)
    assert g.terminal_utility(s, 0) == 1.0


def test_current_player_alternates():
    g = KuhnPoker()
    s = g.next_state(g.initial_state(), (1, 0))
    assert g.current_player(s) == 0
    assert g.current_player(g.next_state(s, "p")) == 1
