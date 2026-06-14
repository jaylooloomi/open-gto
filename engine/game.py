"""Abstract extensive-form game interface used by the CFR solver."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Hashable, Sequence

State = Hashable
Action = Hashable


class ExtensiveFormGame(ABC):
    """Two-player zero-sum extensive-form game with chance and imperfect info.

    Implementations describe a game tree. The solver only needs to walk it:
    distinguish chance/decision/terminal nodes, enumerate actions, and read
    terminal payoffs. Information sets are identified by an opaque string key so
    that distinct histories indistinguishable to the acting player share regret.
    """

    num_players: int = 2

    @abstractmethod
    def initial_state(self) -> State:
        """Return the root state of the game."""

    @abstractmethod
    def is_terminal(self, state: State) -> bool:
        """True if no more actions can be taken from ``state``."""

    @abstractmethod
    def is_chance(self, state: State) -> bool:
        """True if ``state`` is a chance (nature) node."""

    @abstractmethod
    def current_player(self, state: State) -> int:
        """Acting player (0 or 1). Only valid for non-terminal decision nodes."""

    @abstractmethod
    def legal_actions(self, state: State) -> Sequence[Action]:
        """Actions available at a decision node."""

    @abstractmethod
    def chance_outcomes(self, state: State) -> Sequence[tuple[Action, float]]:
        """(action, probability) pairs summing to 1, for a chance node."""

    @abstractmethod
    def next_state(self, state: State, action: Action) -> State:
        """State reached by applying ``action`` to ``state``."""

    @abstractmethod
    def infoset_key(self, state: State) -> str:
        """Stable key identifying the acting player's information set."""

    @abstractmethod
    def terminal_utility(self, state: State, player: int) -> float:
        """Utility for ``player`` at a terminal ``state`` (zero-sum)."""
