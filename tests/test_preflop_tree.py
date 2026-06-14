from engine.preflop.tree import BB, SB, build_tree


def test_root_actions():
    root = build_tree(stack_bb=20)
    assert root.player == SB
    assert set(root.actions) == {"fold", "limp", "raise", "allin"}


def test_fold_terminal():
    root = build_tree(stack_bb=20)
    fold = root.child("fold")
    assert fold.is_terminal and fold.kind == "fold" and fold.folder == SB


def test_allin_called_is_showdown():
    root = build_tree(stack_bb=20)
    show = root.child("allin").child("call")
    assert show.is_terminal and show.kind == "showdown"
    assert show.contrib == (20.0, 20.0)


def test_raise_called_is_seeflop():
    root = build_tree(stack_bb=20)
    flop = root.child("raise").child("call")
    assert flop.is_terminal and flop.kind == "seeflop"
    assert flop.contrib == (2.5, 2.5)


def test_limp_then_check_sees_flop():
    root = build_tree(stack_bb=20)
    bb = root.child("limp")
    assert bb.player == BB
    assert "check" in bb.actions
    flop = bb.child("check")
    assert flop.is_terminal and flop.kind == "seeflop"
    assert flop.contrib == (1.0, 1.0)


def test_three_bet_branch_exists_and_sizes():
    root = build_tree(stack_bb=100)
    bb = root.child("raise")  # BB faces SB open to 2.5
    assert {"fold", "call", "3bet", "allin"} <= set(bb.actions)
    threebet = bb.child("3bet")
    # 3bet to = open(2.5) x 3.0 = 7.5
    assert abs(threebet.contrib[BB] - 7.5) < 1e-9


def test_raise_cap_collapses_to_allin_when_short():
    # At a short stack the open already nears all-in, so re-raises become all-in.
    root = build_tree(stack_bb=6)
    bb = root.child("raise")
    # 3bet to would be 7.5 > 6 stack, so only fold/call/allin remain.
    assert "3bet" not in bb.actions
    assert {"fold", "call", "allin"} <= set(bb.actions)
