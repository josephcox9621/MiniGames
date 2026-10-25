"""Extract reusable, transparency-preserving pixel-art sprites from PNG sheets."""

from pathlib import Path

import pygame


class SpriteSheet:
    """Load an image once and extract independent sprites in pixel coordinates."""

    def __init__(self, path: str | Path) -> None:
        """Load a sheet from path, propagating missing-file or image-load errors."""
        self.image = pygame.image.load(str(path))

    def get_sprite(
        self,
        rect: tuple[int, int, int, int] | pygame.Rect,
        size: tuple[int, int] | None = None,
    ) -> pygame.Surface:
        """Return an independent crop, optionally scaled with nearest neighbor.

        Args:
            rect: Source (x, y, width, height) in pixels, or a pygame.Rect.
            size: Output (width, height), or None to keep the source dimensions.

        Returns:
            A new surface retaining the source image's transparency.

        Raises:
            ValueError: The crop is outside the sheet or dimensions are not positive.
        """
        region = pygame.Rect(rect)
        if region.width <= 0 or region.height <= 0:
            raise ValueError("Sprite dimensions must be positive.")
        if not self.image.get_rect().contains(region):
            raise ValueError(f"Sprite rectangle {region} is outside the spritesheet.")
        # Subsurfaces share pixels with their parent; copy to make edits independent.
        sprite = self.image.subsurface(region).copy()
        if size is None:
            return sprite

        width, height = size
        if width <= 0 or height <= 0:
            raise ValueError("Scaled sprite dimensions must be positive.")

        # Nearest-neighbor scaling preserves hard pixel-art edges without blur.
        return pygame.transform.scale(sprite, size)