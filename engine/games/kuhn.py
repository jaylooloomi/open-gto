"""Kuhn poker: the canonical tiny imperfect-information game.

Deck of 3 cards {0=J, 1=Q, 2=K}. Each player antes 1 and is dealt one card.
Betting alphabet: "p" = pass (check or fold), "b" = bet (or call).

Terminal histories and player-0 net payoff (zero-sum):
  "pp"   both check -> showdown, pot = 2 antes -> +/-1
  "bp"   P0 bets, P1 folds        -> P0 wins 1
  "pbp"  P0 checks, P1 bets, P0 folds -> P0 loses 1
  "bb"   P0 bets, P1 calls -> showdown, pot includes bet -> +/-2
  "pbb"  P0 checks, P1 bets, P0 calls -> showdown -> +/-2

Kuhn poker has a known game value of -1/18 for the first player, and every Nash
equilibrium satisfies P(bet King) = 3 * P(bet Jack) for the first player.
"""
from __future__ import annotations

from itertools import permutations
from typing import Sequence

from engine.game import Action, ExtensiveFormGame, State

_TERMINAL = frozenset({"pp", "bp", "bb", "pbp", "pbb"})


class KuhnPoker(ExtensiveFormGame):
    num_players = 2

    def initial_state(self) -> State:
        return ("chance",)

    def is_terminal(self, state: State) -> bool:
        if state[0] == "chance":
            return False
        _, history = state
        return history in _TERMINAL

    def is_chance(self, state: State) -> bool:
        return state[0] == "chance"

    def current_player(self, state: State) -> int:
        _, history = state
        return len(history) % 2

    def legal_actions(self, state: State) -> Sequence[Action]:
        return ("p", "b")

    def chance_outcomes(self, state: State):
        deals = list(permutations((0, 1, 2), 2))  # 6 ordered distinct deals
        prob = 1.0 / len(deals)
        return [(deal, prob) for deal in deals]

    def next_state(self, state: State, action: Action) -> State:
        if state[0] == "chance":
            return (action, "")  # action is the (card0, card1) tuple
        cards, history = state
        return (cards, history + action)

    def infoset_key(self, state: State) -> str:
        cards, history = state
        return f"{cards[self.current_player(state)]}:{history}"

    def terminal_utility(self, state: State, player: int) -> float:
        cards, history = state
        c0, c1 = cards
        if history == "pp":
            payoff0 = 1.0 if c0 > c1 else -1.0
        elif history == "bp":
            payoff0 = 1.0
        elif history == "pbp":
            payoff0 = -1.0
        elif history in ("bb", "pbb"):
            payoff0 = 2.0 if c0 > c1 else -2.0
        else:
            raise ValueError(f"not a terminal history: {history!r}")
        return payoff0 if player == 0 else -payoff0
