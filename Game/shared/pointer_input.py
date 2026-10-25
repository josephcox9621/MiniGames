"""Normalize mouse and touch activation across screen transitions."""

import pygame


class PointerInput:
    """Track gestures for the whole application, not an individual screen."""

    def __init__(self, screen: pygame.Surface) -> None:
        """Use the logical display size when converting normalized finger positions."""
        self.screen = screen
        self.active_fingers: set[int] = set()
        self.received_touch = False

    def normalize(self, event: pygame.event.Event) -> pygame.event.Event | None:
        """Return a mouse/keyboard event, or None for an ignored touch duplicate.

        Only the first finger activates a control. Keep this instance alive when
        switching screens so synthetic clicks cannot activate the new screen.
        """
        if event.type == pygame.WINDOWFOCUSLOST:
            self.active_fingers.clear()
        elif event.type == pygame.FINGERDOWN:
            self.received_touch = True
            is_first_finger = not self.active_fingers
            self.active_fingers.add(event.finger_id)
            if not is_first_finger:
                return None
            width, height = self.screen.get_size()
            position = (int(event.x * width), int(event.y * height))
            return pygame.event.Event(
                pygame.MOUSEBUTTONDOWN, button=1, pos=position, touch=False,
            )
        elif event.type == pygame.FINGERUP:
            self.active_fingers.discard(event.finger_id)
            return None
        elif event.type == pygame.FINGERMOTION:
            return None
        elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            if self.received_touch and getattr(event, "touch", False):
                return None
        return event