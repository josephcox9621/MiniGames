"""Draw Connect Four without changing its rules or turn state."""

from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from .connect_four import ConnectFour


TEXT_COLOR = (237, 241, 229)
BOARD_BACKGROUND_COLOR = (16, 25, 31)
WIN_OUTLINE_COLOR = (255, 255, 229)
BUTTON_COLOR = (61, 80, 86)


class ConnectFourRenderer:
    """Paint a game's state in layers, with pieces behind the board's holes."""

    def __init__(self, game: "ConnectFour") -> None:
        """Keep a reference to the game so resets are visible on the next frame."""
        self.game = game
        self.screen = game.screen

    def draw(self) -> None:
        """Repaint the full frame; the host is responsible for display.flip()."""
        self.screen.blit(self.game.background, (0, 0))
        self._draw_heading()
        self._draw_preview()
        pygame.draw.rect(self.screen, BOARD_BACKGROUND_COLOR, self.game.board_rect)
        self._draw_settled_pieces()
        self._draw_falling_piece()
        self._draw_board_overlay()
        self._draw_restart_button()

    def cell_position(self, row: int, column: int) -> tuple[int, int]:
        """Convert a board cell to its top-left window position in pixels."""
        game = self.game
        left = game.board_rect.left + column * game.cell_size
        top = game.board_rect.top + row * game.cell_size
        return left, top

    def draw_text(
        self, text: str, font: pygame.font.Font, center: tuple[int, int],
    ) -> None:
        """Draw a label centered at the given window position."""
        label = font.render(text, True, TEXT_COLOR)
        self.screen.blit(label, label.get_rect(center=center))

    def _draw_heading(self) -> None:
        """Draw the title and current turn or result message."""
        game = self.game
        center_x = self.screen.get_width() // 2
        self.draw_text("CONNECT FOUR", game.title_font, (center_x, 48))
        self.draw_text(game.message, game.font, (center_x, 90))

    def _draw_preview(self) -> None:
        """Show the selected piece above its column when a move is available."""
        game = self.game
        if game.game_over or game.animation is not None:
            return

        # Fade a copy so the shared sprite stays opaque during normal play.
        preview = game.pieces[game.current_player].copy()
        preview.set_alpha(150)
        left, _ = self.cell_position(0, game.selected_column)
        top = game.board_rect.top - game.cell_size - 6
        self.screen.blit(preview, (left, top))

    def _draw_settled_pieces(self) -> None:
        """Paint occupied cells, excluding the piece that is still falling."""
        game = self.game
        for row in range(game.ROWS):
            for column in range(game.COLUMNS):
                player = game.board[row][column]
                if player == game.EMPTY:
                    continue
                # The falling piece reserves a board cell before it visually lands.
                if game.animation == (row, column, player):
                    continue
                self.screen.blit(game.pieces[player], self.cell_position(row, column))

    def _draw_falling_piece(self) -> None:
        """Paint the active piece at its animated height."""
        game = self.game
        if game.animation is None:
            return

        row, column, player = game.animation
        left, _ = self.cell_position(row, column)
        self.screen.blit(game.pieces[player], (left, int(game.animation_y)))

    def _draw_board_overlay(self) -> None:
        """Mask piece edges with board tiles and outline the winning cells."""
        game = self.game
        for row in range(game.ROWS):
            for column in range(game.COLUMNS):
                position = self.cell_position(row, column)
                self.screen.blit(game.board_tile, position)
                if (row, column) in game.winning_cells:
                    outline = pygame.Rect(position, (game.cell_size, game.cell_size))
                    pygame.draw.rect(self.screen, WIN_OUTLINE_COLOR, outline, width=3)

    def _draw_restart_button(self) -> None:
        """Paint the new-game button below the board."""
        game = self.game
        pygame.draw.rect(self.screen, BUTTON_COLOR, game.restart_rect, border_radius=4)
        self.draw_text("New game", game.font, game.restart_rect.center)