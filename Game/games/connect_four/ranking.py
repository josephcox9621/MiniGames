"""Track a local CPU-mode rating with bounded win and loss streak changes."""

from typing import Literal

from shared.profile_store import ProfileStore


MatchResult = Literal["win", "loss", "draw"]


class CpuRanking:
    """Award 20-40 points per decisive result, with a minimum rating of zero.

    Each consecutive win or loss adds 5 to that result's magnitude, up to 40.
    Changing result direction starts a new streak. Draws break the streak and
    leave the rating unchanged. Only completed CPU matches should be recorded.
    """

    STARTING_RATING = 1000
    BASE_CHANGE = 20
    STREAK_BONUS = 5
    MAX_CHANGE = 40
    TIERS = ((1800, "Diamond"), (1500, "Platinum"), (1200, "Gold"), (1000, "Silver"), (0, "Bronze"))

    def __init__(self, store: ProfileStore | None = None) -> None:
        """Load persisted progress, or start a new profile when none is usable."""
        self.store = store if store is not None else ProfileStore("connect_four_rank")
        self.rating = self.STARTING_RATING
        self.streak = 0
        self.wins = 0
        self.losses = 0
        self.draws = 0
        self._load()

    def _load(self) -> None:
        """Validate the complete save before applying any values from it."""
        data = self.store.load()
        if data is None:
            return
        fields = ("rating", "streak", "wins", "losses", "draws")
        if data.get("version") != 1 or any(type(data.get(field)) is not int for field in fields):
            self.store.error = "Saved rank unavailable"
            return
        if any(data[field] < 0 for field in ("rating", "wins", "losses", "draws")):
            self.store.error = "Saved rank unavailable"
            return
        if not -data["losses"] <= data["streak"] <= data["wins"]:
            self.store.error = "Saved rank unavailable"
            return
        self.rating = data["rating"]
        self.streak = data["streak"]
        self.wins = data["wins"]
        self.losses = data["losses"]
        self.draws = data["draws"]

    @property
    def tier(self) -> str:
        """Return the tier name corresponding to the current rating."""
        for minimum, name in self.TIERS:
            if self.rating >= minimum:
                return name
        return "Bronze"

    @property
    def streak_label(self) -> str:
        """Describe the current streak, using a sign only in the stored value."""
        if self.streak > 0:
            return f"{self.streak} win streak"
        if self.streak < 0:
            return f"{abs(self.streak)} loss streak"
        return "No streak"

    def record(self, result: MatchResult) -> int:
        """Apply and save one result; return the actual signed rating change."""
        if result not in ("win", "loss", "draw"):
            raise ValueError("Result must be win, loss, or draw.")

        previous_rating = self.rating
        if result == "draw":
            self.draws += 1
            self.streak = 0
        else:
            direction = 1 if result == "win" else -1
            if self.streak * direction > 0:
                self.streak += direction
            else:
                self.streak = direction
            change = self.BASE_CHANGE + (abs(self.streak) - 1) * self.STREAK_BONUS
            change = min(change, self.MAX_CHANGE)
            self.rating = max(0, self.rating + direction * change)
            if result == "win":
                self.wins += 1
            else:
                self.losses += 1

        self.store.save({
            "version": 1,
            "rating": self.rating,
            "streak": self.streak,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
        })
        return self.rating - previous_rating