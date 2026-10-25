"""Coordinate the game library, active game, and shared navigation."""

import pygame

from shared.pointer_input import PointerInput

from .game_registry import AVAILABLE_GAMES, PlayableGame
from .menu import GameMenu


class MiniGamesApp:
    """Own screen transitions while games remain unaware of the menu."""

    def __init__(self, screen: pygame.Surface) -> None:
        """Start at the game library and prepare a touch-sized return control."""
        self.screen = screen
        self.menu = GameMenu(screen, AVAILABLE_GAMES)
        self.pointer = PointerInput(screen)
        self.active_game: PlayableGame | None = None
        self.back_rect = pygame.Rect(24, screen.get_height() - 72, 120, 48)
        self.button_font = pygame.font.Font(None, 26)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Normalize pointers, handle navigation, then route the event once."""
        event = self.pointer.normalize(event)
        if event is None:
            return

        if self.active_game is None:
            entry = self.menu.handle_event(event)
            if entry is not None:
                self.active_game = entry.create(self.screen)
            return

        pressed_escape = event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
        clicked_back = (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.back_rect.collidepoint(event.pos)
        )
        if pressed_escape or clicked_back:
            self.active_game = None
            return
        self.active_game.handle_event(event)

    def update(self, delta_time: float) -> None:
        """Advance only the currently active game."""
        if self.active_game is not None:
            self.active_game.update(delta_time)

    def draw(self) -> None:
        """Draw the library or active game with application-level navigation."""
        if self.active_game is None:
            self.menu.draw()
            return

        self.active_game.draw()
        pygame.draw.rect(self.screen, (61, 80, 86), self.back_rect, border_radius=4)
        label = self.button_font.render("< Games", True, (237, 241, 229))
        self.screen.blit(label, label.get_rect(center=self.back_rect.center))