"""Persist small JSON profiles on desktop and in pygbag browser storage."""

import json
import platform
import sys
from pathlib import Path


class ProfileStore:
    """Store one profile outside the bundled game assets.

    Desktop saves live in the user's .minigames folder. Browser saves use
    localStorage for the current site, so they survive ordinary page reloads.
    An explicit path uses file storage on any platform, including in tests.
    """

    def __init__(self, name: str, path: Path | None = None) -> None:
        """Choose file storage or the current browser's localStorage."""
        self.key = f"minigames.{name}.v1"
        self.use_browser = path is None and sys.platform == "emscripten"
        self.path = path if path is not None else Path.home() / ".minigames" / f"{name}.json"
        self.error: str | None = None

    def load(self) -> dict | None:
        """Read a JSON object, returning None for missing or unreadable data."""
        try:
            if self.use_browser:
                raw = platform.window.localStorage.getItem(self.key)
                if not raw:
                    return None
            else:
                if not self.path.exists():
                    return None
                raw = self.path.read_text(encoding="utf-8")
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("Expected a profile object.")
            self.error = None
            return data
        except Exception:
            # Browser privacy settings can throw JS errors, not just OSError.
            self.error = "Saved rank unavailable"
            return None

    def save(self, data: dict) -> bool:
        """Save a profile, returning False if storage is blocked or unavailable."""
        try:
            raw = json.dumps(data)
            if self.use_browser:
                platform.window.localStorage.setItem(self.key, raw)
            else:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                temporary_path = self.path.with_suffix(".tmp")
                temporary_path.write_text(raw, encoding="utf-8")
                temporary_path.replace(self.path)
            self.error = None
            return True
        except Exception:
            self.error = "Rank not saved"
            return False