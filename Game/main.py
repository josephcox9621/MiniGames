"""Launch the MiniGames library with a browser-compatible Pygame loop."""

import asyncio
import platform
import sys

import pygame

from app.application import MiniGamesApp

GAME_WIDTH = 400
GAME_HEIGHT = 800
FRAMES_PER_SECOND = 60
MILLISECONDS_PER_SECOND = 1000


def configure_browser_input() -> None:
    """Keep touch gestures on the pygbag canvas from scrolling the browser page.

    Desktop Pygame has no browser canvas, so it requires no configuration.
    Only the canvas is affected; the rest of the page keeps its normal behavior.
    """
    if sys.platform != "emscripten":
        return

    browser_window = getattr(platform, "window", None)
    if browser_window is None:
        return

    canvas_style = browser_window.canvas.style
    canvas_style.touchAction = "none"
    canvas_style.userSelect = "none"


async def main() -> None:
    """Run input, animation, and rendering until the window is closed.

    Yield to asyncio every frame for browser compatibility and shut down Pygame
    after leaving the loop. Animation receives elapsed time in seconds.
    """
    pygame.init()
    try:
        screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT), pygame.SCALED)
        configure_browser_input()
        pygame.display.set_caption("MiniGames")
        clock = pygame.time.Clock()
        app = MiniGamesApp(screen)
        running = True

        while running:
            elapsed_ms = clock.tick(FRAMES_PER_SECOND)
            elapsed_seconds = elapsed_ms / MILLISECONDS_PER_SECOND

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    app.handle_event(event)

            app.update(elapsed_seconds)
            app.draw()
            pygame.display.flip()

            # pygbag needs control returned to the browser every frame.
            await asyncio.sleep(0)
    finally:
        pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())