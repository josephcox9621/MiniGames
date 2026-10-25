"""Load Connect Four artwork and generate pixel-art fallbacks."""

from pathlib import Path

import pygame

from spritesheet import SpriteSheet


PLAYER_COLORS = {1: (231, 77, 86), 2: (246, 202, 70)}
NATIVE_TILE_SIZE = (32, 32)
# Each crop is (left, top, width, height) in spritesheet pixels.
DEFAULT_SPRITE_RECTS = {
    "board_tile.png": (0, 0, 32, 32),
    "red_piece.png": (32, 0, 32, 32),
    "yellow_piece.png": (64, 0, 32, 32),
}


class ConnectFourAssets:
    """Resolve artwork from a shared sheet, standalone PNGs, or placeholders."""

    def __init__(
        self,
        asset_dir: str | Path | None = None,
        *,
        spritesheet_path: str | Path | None = None,
        sprite_rects: dict[str, tuple[int, int, int, int]] | None = None,
    ) -> None:
        """Configure asset sources without loading individual game sprites.

        Default assets are relative to this module. Explicit sheet paths are
        relative to the working directory unless absolute. A supplied rectangle
        mapping replaces the defaults. Explicit missing sheets raise load errors.
        """
        if asset_dir is None:
            asset_dir = Path(__file__).resolve().parents[2] / "assets" / "connect_four"
        self.asset_dir = Path(asset_dir)

        # Copy caller configuration so later edits cannot change the crop mapping.
        if sprite_rects is None:
            sprite_rects = DEFAULT_SPRITE_RECTS
        self.sprite_rects = dict(sprite_rects)

        self.spritesheet: SpriteSheet | None = None
        if spritesheet_path is not None:
            self.spritesheet = SpriteSheet(spritesheet_path)
        else:
            default_sheet = self.asset_dir / "connect_four_spritesheet.png"
            if default_sheet.is_file():
                self.spritesheet = SpriteSheet(default_sheet)

    def load(self, filename: str, size: tuple[int, int]) -> pygame.Surface:
        """Return a known game asset scaled to the requested width and height.

        Mapped sheet crops take priority over PNGs and generated placeholders.
        Invalid configured artwork raises errors instead of silently falling back.
        """
        if self.spritesheet is not None and filename in self.sprite_rects:
            return self.spritesheet.get_sprite(self.sprite_rects[filename], size)
        path = self.asset_dir / filename
        if path.is_file():
            image = pygame.image.load(str(path))
            return pygame.transform.scale(image, size)

        if filename == "background.png":
            return self._create_background(size)
        if filename == "board_tile.png":
            placeholder = self._create_board_tile()
        else:
            player = 1 if filename == "red_piece.png" else 2
            placeholder = self._create_piece(PLAYER_COLORS[player])

        return pygame.transform.scale(placeholder, size)

    @staticmethod
    def _create_background(size: tuple[int, int]) -> pygame.Surface:
        """Create the striped fallback background at the window's dimensions."""
        width, height = size
        background = pygame.Surface(size)
        background.fill((24, 34, 40))
        for line_y in range(0, height, 16):
            pygame.draw.line(background, (29, 40, 46), (0, line_y), (width, line_y))
        return background

    @staticmethod
    def _create_board_tile() -> pygame.Surface:
        """Create a native-size board tile with a transparent hole for pieces."""
        tile = pygame.Surface(NATIVE_TILE_SIZE, pygame.SRCALPHA)
        tile.fill((42, 137, 155))
        pygame.draw.rect(tile, (72, 173, 182), (0, 0, 32, 2))
        pygame.draw.rect(tile, (22, 93, 116), (30, 0, 2, 32))
        # Pieces are painted first and remain visible through this hole.
        pygame.draw.circle(tile, (0, 0, 0, 0), (16, 16), 12)
        return tile

    @staticmethod
    def _create_piece(color: tuple[int, int, int]) -> pygame.Surface:
        """Create a shaded pixel-art disc on a transparent native-size canvas."""
        piece = pygame.Surface(NATIVE_TILE_SIZE, pygame.SRCALPHA)
        shadow_color = tuple(channel // 2 for channel in color)
        pygame.draw.circle(piece, shadow_color, (16, 17), 11)
        pygame.draw.circle(piece, color, (16, 15), 10)
        pygame.draw.rect(piece, (255, 240, 208), (11, 9, 5, 2))
        return piece