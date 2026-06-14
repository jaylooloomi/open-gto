"""Leduc poker: the standard small benchmark for equilibrium solvers.

Deck: 6 physical cards, ranks {0=J, 1=Q, 2=K}, two suits each
(card // 2 == rank). Each player antes 1 and is dealt one private card.
Round 1 betting (bet size 2), then one community card is revealed, then
round 2 betting (bet size 4). At most two bets/raises per round.

Showdown: a player whose private card pairs the board wins; otherwise the
higher private rank wins; equal ranks split (net 0).

Betting alphabet within a round (player 0 acts first):
  k = check, b = bet, c = call, r = raise, f = fold
A round proceeds to the next stage on "kk" or any call; a fold ends the hand.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import permutations
from typing import Sequence

from engine.game import Action, ExtensiveFormGame, State

_RAISE_CAP = 2  # at most a bet + one raise per round
_R1_BET = 2
_R2_BET = 4
_DECK = (0, 1, 2, 3, 4, 5)  # physical cards; rank = card // 2


def _rank(card: int) -> int:
    return card // 2


@lru_cache(maxsize=None)
def _replay(actions: str, bet_size: int):
    """Replay a round's action string.

    Returns (contrib, to_act, num_bets, folded, status) where
    contrib = (p0_in, p1_in) (this round only), status in {"open","proceed","fold"}.
    Cached: only ~9 distinct round strings exist, so this collapses to lookups.
    """
    contrib = [0, 0]
    to_act = 0
    num_bets = 0
    folded = None
    for a in actions:
        opp = 1 - to_act
        if a == "k":
            pass
        elif a == "b":
            contrib[to_act] += bet_size
            num_bets += 1
        elif a == "c":
            contrib[to_act] = contrib[opp]
        elif a == "r":
            contrib[to_act] = contrib[opp] + bet_size
            num_bets += 1
        elif a == "f":
            folded = to_act
            to_act = opp
            break
        else:
            raise ValueError(f"bad action {a!r}")
        to_act = opp

    if folded is not None:
        status = "fold"
    elif actions.endswith("c") or actions == "kk":
        status = "proceed"
    else:
        status = "open"
    return tuple(contrib), to_act, num_bets, folded, status


def _legal(actions: str, bet_size: int) -> list[str]:
    contrib, to_act, num_bets, _, _ = _replay(actions, bet_size)
    opp = 1 - to_act
    if contrib[opp] > contrib[to_act]:  # facing a bet/raise
        acts = ["f", "c"]
        if num_bets < _RAISE_CAP:
            acts.append("r")
        return acts
    return ["k", "b"]  # no outstanding bet


class LeducPoker(ExtensiveFormGame):
    num_players = 2

    def initial_state(self) -> State:
        return (-1, -1, -1, "", "")  # c0, c1, board, r1, r2

    def _phase(self, state: State) -> str:
        c0, c1, board, r1, r2 = state
        if c0 == -1:
            return "deal"
        s1 = _replay(r1, _R1_BET)[4]
        if s1 == "fold":
            return "terminal"
        if s1 == "open":
            return "r1"
        # round 1 proceeded
        if board == -1:
            return "deal_board"
        s2 = _replay(r2, _R2_BET)[4]
        if s2 == "open":
            return "r2"
        return "terminal"

    def is_terminal(self, state: State) -> bool:
        return self._phase(state) == "terminal"

    def is_chance(self, state: State) -> bool:
        return self._phase(state) in ("deal", "deal_board")

    def current_player(self, state: State) -> int:
        _, _, _, r1, r2 = state
        if self._phase(state) == "r1":
            return _replay(r1, _R1_BET)[1]
        return _replay(r2, _R2_BET)[1]

    def legal_actions(self, state: State) -> Sequence[Action]:
        _, _, _, r1, r2 = state
        if self._phase(state) == "r1":
            return _legal(r1, _R1_BET)
        return _legal(r2, _R2_BET)

    def chance_outcomes(self, state: State):
        c0, c1, board, _, _ = state
        if c0 == -1:
            deals = list(permutations(_DECK, 2))  # 30 ordered private deals
            prob = 1.0 / len(deals)
            return [(deal, prob) for deal in deals]
        remaining = [c for c in _DECK if c not in (c0, c1)]
        prob = 1.0 / len(remaining)
        return [(card, prob) for card in remaining]

    def next_state(self, state: State, action: Action) -> State:
        c0, c1, board, r1, r2 = state
        phase = self._phase(state)
        if phase == "deal":
            return (action[0], action[1], -1, "", "")
        if phase == "deal_board":
            return (c0, c1, action, r1, "")
        if phase == "r1":
            return (c0, c1, board, r1 + action, "")
        return (c0, c1, board, r1, r2 + action)

    def infoset_key(self, state: State) -> str:
        c0, c1, board, r1, r2 = state
        me = self.current_player(state)
        my_rank = _rank(c0 if me == 0 else c1)
        board_str = str(_rank(board)) if board != -1 else "?"
        return f"{my_rank}|{board_str}|{r1}/{r2}"

    def _winner(self, c0: int, c1: int, board: int):
        r0, r1, rb = _rank(c0), _rank(c1), _rank(board)
        if r0 == rb:
            return 0
        if r1 == rb:
            return 1
        if r0 > r1:
            return 0
        if r1 > r0:
            return 1
        return None  # split

    def terminal_utility(self, state: State, player: int) -> float:
        c0, c1, board, r1, r2 = state
        c1r, _, _, folded1, _ = _replay(r1, _R1_BET)
        c2r, _, _, folded2, _ = _replay(r2, _R2_BET)
        total = [1 + c1r[0] + c2r[0], 1 + c1r[1] + c2r[1]]  # ante + both rounds

        folded = folded1 if folded1 is not None else folded2
        if folded is not None:
            net0 = total[1] if folded == 1 else -total[0]
        else:
            w = self._winner(c0, c1, board)
            stake = total[0]  # equal at showdown
            net0 = 0.0 if w is None else (stake if w == 0 else -stake)
        return float(net0) if player == 0 else float(-net0)
