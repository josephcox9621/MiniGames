"""Select a Connect Four opponent before starting a match."""

import pygame

from .assets import ConnectFourAssets
from .connect_four import ConnectFour
from .ranking import CpuRanking


class ConnectFourSession:
    """Present PvP/CPU choices, then forward the frame loop to the chosen match.

    Pointer events arrive normalized by the application's shared input handler.
    Returning to the library and reopening Connect Four shows these choices again.
    """

    MODES = (
        ("Player vs Player", "Red vs Yellow", False),
        ("Player vs CPU", "Ranked / Random colour", True),
    )

    def __init__(self, screen: pygame.Surface, ranking: CpuRanking | None = None) -> None:
        """Prepare mode controls and artwork without starting a match."""
        self.screen = screen
        self.ranking = ranking if ranking is not None else CpuRanking()
        self.game: ConnectFour | None = None
        self.selected_index = 0
        self.title_font = pygame.font.Font(None, 38)
        self.mode_font = pygame.font.Font(None, 30)
        self.detail_font = pygame.font.Font(None, 23)
        self.mode_rects = [
            pygame.Rect(24, 280 + index * 112, screen.get_width() - 48, 96)
            for index in range(len(self.MODES))
        ]
        assets = ConnectFourAssets()
        self.background = assets.load("background.png", screen.get_size())
        self.tile = assets.load("board_tile.png", (32, 32))
        self.red_piece = assets.load("red_piece.png", (32, 32))
        self.yellow_piece = assets.load("yellow_piece.png", (32, 32))

    def handle_event(self, event: pygame.event.Event) -> None:
        """Select an opponent by keyboard or pointer, or forward match input."""
        if self.game is not None:
            self.game.handle_event(event)
            return

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_LEFT):
                self.selected_index = (self.selected_index - 1) % len(self.MODES)
            elif event.key in (pygame.K_DOWN, pygame.K_RIGHT):
                self.selected_index = (self.selected_index + 1) % len(self.MODES)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._start_match()
        elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            for index, rect in enumerate(self.mode_rects):
                if rect.collidepoint(event.pos):
                    self.selected_index = index
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self._start_match()
                    return

    def _start_match(self) -> None:
        """Create a fresh match using the selected opponent mode."""
        title, description, vs_cpu = self.MODES[self.selected_index]
        self.game = ConnectFour(self.screen, vs_cpu=vs_cpu, ranking=self.ranking)

    def update(self, delta_time: float) -> None:
        """Advance the chosen match; the mode selector has no timed state."""
        if self.game is not None:
            self.game.update(delta_time)

    def draw(self) -> None:
        """Draw opponent choices with a sprite preview, or draw the active match."""
        if self.game is not None:
            self.game.draw()
            return

        self.screen.blit(self.background, (0, 0))
        center_x = self.screen.get_width() // 2
        heading = self.title_font.render("CONNECT FOUR", True, (237, 241, 229))
        self.screen.blit(heading, heading.get_rect(center=(center_x, 70)))

        for row in range(3):
            for column in range(7):
                position = (center_x - 112 + column * 32, 130 + row * 32)
                if row == 2:
                    piece = self.red_piece if column % 2 else self.yellow_piece
                    self.screen.blit(piece, position)
                self.screen.blit(self.tile, position)

        for index, (title, description, vs_cpu) in enumerate(self.MODES):
            rect = self.mode_rects[index]
            pygame.draw.rect(self.screen, (36, 52, 59), rect, border_radius=4)
            if index == self.selected_index:
                pygame.draw.rect(self.screen, (78, 191, 183), rect, width=2, border_radius=4)
            label = self.mode_font.render(title, True, (237, 241, 229))
            detail = self.detail_font.render(description, True, (158, 185, 185))
            self.screen.blit(label, (rect.left + 20, rect.top + 20))
            self.screen.blit(detail, (rect.left + 20, rect.top + 56))

        self._draw_ranking()

    def _draw_ranking(self) -> None:
        """Show saved CPU progress even before the player starts a match."""
        rank = self.ranking
        lines = [
            f"CPU rank: {rank.tier} / {rank.rating:,}",
            rank.streak_label,
            f"{rank.wins} wins / {rank.losses} losses / {rank.draws} draws",
        ]
        if rank.store.error:
            lines.append(rank.store.error)
        for index, text in enumerate(lines):
            label = self.detail_font.render(text, True, (158, 185, 185))
            self.screen.blit(label, (24, 530 + index * 28))