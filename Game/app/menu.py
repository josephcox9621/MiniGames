"""Render and navigate the game selection screen."""

import pygame

from games.connect_four.assets import ConnectFourAssets

from .game_registry import GameEntry


class GameMenu:
    """Offer registered games through touch, mouse, and keyboard selection."""

    def __init__(self, screen: pygame.Surface, games: tuple[GameEntry, ...]) -> None:
        """Build fixed menu rows and cache artwork for the Connect Four entry."""
        self.screen = screen
        self.games = games
        self.selected_index = 0
        self.title_font = pygame.font.Font(None, 48)
        self.game_font = pygame.font.Font(None, 30)
        self.detail_font = pygame.font.Font(None, 23)
        self.rows = [
            pygame.Rect(24, 166 + index * 112, screen.get_width() - 48, 96)
            for index in range(len(games))
        ]
        assets = ConnectFourAssets()
        self.board_tile = assets.load("board_tile.png", (16, 16))
        self.red_piece = assets.load("red_piece.png", (16, 16))
        self.yellow_piece = assets.load("yellow_piece.png", (16, 16))

    def handle_event(self, event: pygame.event.Event) -> GameEntry | None:
        """Return the activated game, or None when only the selection changes."""
        if not self.games:
            return None
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_LEFT):
                self.selected_index = (self.selected_index - 1) % len(self.games)
            elif event.key in (pygame.K_DOWN, pygame.K_RIGHT):
                self.selected_index = (self.selected_index + 1) % len(self.games)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.games[self.selected_index]
        elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            for index, row in enumerate(self.rows):
                if row.collidepoint(event.pos):
                    self.selected_index = index
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        return self.games[index]
        return None

    def draw(self) -> None:
        """Paint a compact game library with a visible keyboard selection."""
        self.screen.fill((24, 34, 40))
        for line_y in range(0, self.screen.get_height(), 16):
            pygame.draw.line(
                self.screen, (29, 40, 46), (0, line_y),
                (self.screen.get_width(), line_y),
            )
        self._draw_label("MINIGAMES", self.title_font, (24, 54), (237, 241, 229))
        self._draw_label("Games", self.detail_font, (24, 120), (158, 185, 185))

        for index, (entry, row) in enumerate(zip(self.games, self.rows)):
            selected = index == self.selected_index
            pygame.draw.rect(self.screen, (36, 52, 59), row, border_radius=4)
            if selected:
                pygame.draw.rect(self.screen, (78, 191, 183), row, width=2, border_radius=4)
            if entry.title == "Connect Four":
                self._draw_connect_four_icon(row.left + 12, row.top + 16)
            self._draw_label(entry.title, self.game_font, (row.left + 96, row.top + 22), (237, 241, 229))
            self._draw_label(entry.players, self.detail_font, (row.left + 96, row.top + 55), (158, 185, 185))

    def _draw_label(
        self, text: str, font: pygame.font.Font,
        position: tuple[int, int], color: tuple[int, int, int],
    ) -> None:
        """Draw a left-aligned label at its top-left position."""
        self.screen.blit(font.render(text, True, color), position)

    def _draw_connect_four_icon(self, left: int, top: int) -> None:
        """Build a small board preview using the game's actual sprite artwork."""
        for row in range(4):
            for column in range(4):
                position = (left + column * 16, top + row * 16)
                if row >= 2:
                    piece = self.red_piece if (row + column) % 2 else self.yellow_piece
                    self.screen.blit(piece, position)
                self.screen.blit(self.board_tile, position)