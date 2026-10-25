"""List playable games in one place so the menu need not know their internals."""

from dataclasses import dataclass
from typing import Callable, Protocol

import pygame

from games.connect_four.connect_four import ConnectFour


class PlayableGame(Protocol):
    """Frame-loop interface implemented by games in the collection."""

    def handle_event(self, event: pygame.event.Event) -> None:
        """Process one input event."""
        ...

    def update(self, delta_time: float) -> None:
        """Advance gameplay using elapsed seconds."""
        ...

    def draw(self) -> None:
        """Draw the current frame without presenting the display."""
        ...


@dataclass(frozen=True)
class GameEntry:
    """Menu label and constructor for a playable game."""

    title: str
    players: str
    create: Callable[[pygame.Surface], PlayableGame]


AVAILABLE_GAMES = (
    GameEntry("Connect Four", "2 players", ConnectFour),
)