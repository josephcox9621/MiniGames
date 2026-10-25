"""Regression checks for CPU colours, streak ratings, and profile storage."""

import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame

from games.connect_four.connect_four import ConnectFour
from games.connect_four.ranking import CpuRanking
from games.connect_four.session import ConnectFourSession
from shared.profile_store import ProfileStore


class CpuRankingTests(unittest.TestCase):
    """Exercise ranking and gameplay without touching the user's real profile."""

    @classmethod
    def setUpClass(cls) -> None:
        """Create a headless display for sprite loading and rendering."""
        pygame.init()
        cls.screen = pygame.display.set_mode((400, 800))

    @classmethod
    def tearDownClass(cls) -> None:
        """Release Pygame resources after the tests."""
        pygame.quit()

    def setUp(self) -> None:
        """Give each test its own temporary rating file."""
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "rank.json"
        self.rank = CpuRanking(ProfileStore("test", self.path))

    def make_game(self, human_player: int) -> ConnectFour:
        """Choose a deterministic human colour while retaining real game logic."""
        with patch("games.connect_four.connect_four.random.choice", return_value=human_player):
            return ConnectFour(self.screen, vs_cpu=True, ranking=self.rank)

    def test_streak_changes_are_capped(self) -> None:
        """Repeated wins and losses grow to, but never exceed, 40 points."""
        expected = [20, 25, 30, 35, 40, 40, 40]
        self.assertEqual([self.rank.record("win") for _ in expected], expected)
        self.assertEqual([self.rank.record("loss") for _ in expected], [-value for value in expected])

    def test_draw_breaks_streak(self) -> None:
        """A draw changes no rating and restarts the next result at 20 points."""
        self.rank.record("win")
        before = self.rank.rating
        self.assertEqual(self.rank.record("draw"), 0)
        self.assertEqual(self.rank.rating, before)
        self.assertEqual(self.rank.streak, 0)
        self.assertEqual(self.rank.record("win"), 20)

    def test_rating_floor_and_tiers(self) -> None:
        """Losses stop at zero and tier names follow the documented thresholds."""
        self.rank.rating = 5
        self.assertEqual(self.rank.record("loss"), -5)
        self.assertEqual(self.rank.record("loss"), 0)
        for rating, tier in [(0, "Bronze"), (1000, "Silver"), (1200, "Gold"), (1500, "Platinum"), (1800, "Diamond")]:
            self.rank.rating = rating
            self.assertEqual(self.rank.tier, tier)

    def test_desktop_progress_reloads(self) -> None:
        """Rating, statistics, and streak survive loading a new profile object."""
        for result in ("win", "win", "loss", "draw", "loss", "loss"):
            self.rank.record(result)
        loaded = CpuRanking(ProfileStore("test", self.path))
        self.assertEqual(loaded.rating, self.rank.rating)
        self.assertEqual((loaded.wins, loaded.losses, loaded.draws, loaded.streak), (2, 3, 1, -2))

    def test_invalid_saves_use_default_profile(self) -> None:
        """Corrupt JSON and invalid field types cannot crash or corrupt the rank."""
        invalid_profiles = ["{bad", "[]", json.dumps({"version": 1, "rating": True})]
        for raw in invalid_profiles:
            self.path.write_text(raw, encoding="utf-8")
            loaded = CpuRanking(ProfileStore("test", self.path))
            self.assertEqual(loaded.rating, 1000)
            self.assertIsNotNone(loaded.store.error)

    def test_browser_progress_and_blocked_storage(self) -> None:
        """Browser localStorage persists results and degrades safely when denied."""
        saved_values = {}
        storage = SimpleNamespace(getItem=saved_values.get, setItem=saved_values.__setitem__)
        window = SimpleNamespace(localStorage=storage)
        with patch("shared.profile_store.sys.platform", "emscripten"), patch(
            "shared.profile_store.platform.window", window, create=True,
        ):
            rank = CpuRanking(ProfileStore("browser_test"))
            rank.record("win")
            loaded = CpuRanking(ProfileStore("browser_test"))
            self.assertEqual((loaded.rating, loaded.streak, loaded.wins), (1020, 1, 1))
            storage.setItem = Mock(side_effect=RuntimeError("Storage blocked"))
            self.assertEqual(loaded.record("win"), 25)
            self.assertEqual(loaded.store.error, "Rank not saved")
            storage.getItem = Mock(side_effect=RuntimeError("Storage blocked"))
            unavailable = CpuRanking(ProfileStore("browser_test"))
            self.assertEqual(unavailable.rating, 1000)
            self.assertIsNotNone(unavailable.store.error)

    def test_desktop_write_failure_preserves_session_progress(self) -> None:
        """A failed file save retains the in-memory result and exposes a warning."""
        blocked = Path(self.folder.name) / "not_a_folder"
        blocked.write_text("file", encoding="utf-8")
        rank = CpuRanking(ProfileStore("test", blocked / "rank.json"))
        self.assertEqual(rank.record("win"), 20)
        self.assertEqual(rank.store.error, "Rank not saved")

    def test_cpu_can_open_as_red(self) -> None:
        """When the human is yellow, red CPU opens and then yields to the human."""
        game = self.make_game(2)
        self.assertTrue(game.is_cpu_turn)
        self.assertFalse(game.drop_piece(0))
        game.update(.4)
        game.update(1)
        self.assertEqual(game.current_player, game.human_player)
        self.assertEqual(game.board[5][3], 1)
        self.assertTrue(game.drop_piece(0))

    def test_both_colours_score_wins_and_losses_once(self) -> None:
        """Results follow the human colour, not a fixed red-player assumption."""
        for human in (1, 2):
            for human_won in (True, False):
                with self.subTest(human=human, human_won=human_won):
                    game = self.make_game(human)
                    winner = human if human_won else game.cpu_player
                    game.board[5][:4] = [winner] * 4
                    completed_before = self.rank.wins + self.rank.losses
                    game._finish_move(5, 3, winner)
                    self.assertEqual(game.rating_change > 0, human_won)
                    game._finish_move(5, 3, winner)
                    game.update(10)
                    self.assertEqual(self.rank.wins + self.rank.losses, completed_before + 1)
                    game.draw()

    def test_draw_scores_once(self) -> None:
        """A final nonwinning move records one draw and clears an existing streak."""
        self.rank.record("win")
        game = self.make_game(2)
        game.board = [
            [1, 1, 2, 2, 1, 1, 0],
            [2, 2, 1, 1, 2, 2, 1],
            [1, 1, 2, 2, 1, 1, 2],
            [2, 2, 1, 1, 2, 2, 1],
            [1, 1, 2, 2, 1, 1, 2],
            [2, 2, 1, 1, 2, 2, 1],
        ]
        game.current_player = 2
        self.assertTrue(game.drop_piece(6))
        game.update(1)
        game.update(10)
        self.assertTrue(game.is_draw)
        self.assertEqual((game.rating_change, self.rank.draws, self.rank.streak), (0, 1, 0))

    def test_restart_reassigns_colour_without_scoring(self) -> None:
        """Restarting an unfinished CPU match rerolls ownership without a result."""
        game = self.make_game(1)
        self.assertTrue(game.drop_piece(0))
        with patch("games.connect_four.connect_four.random.choice", return_value=2):
            game.reset()
        self.assertEqual(game.human_player, 2)
        self.assertTrue(game.is_cpu_turn)
        self.assertEqual((self.rank.rating, self.rank.wins, self.rank.losses), (1000, 0, 0))
        self.assertFalse(self.path.exists())

    def test_pvp_does_not_score(self) -> None:
        """PvP matches cannot affect the supplied CPU profile."""
        game = ConnectFour(self.screen, ranking=self.rank)
        game.board[5][:4] = [1] * 4
        game._finish_move(5, 3, 1)
        self.assertIsNone(game.ranking)
        self.assertEqual(self.rank.rating, 1000)
        self.assertFalse(self.path.exists())

    def test_session_uses_shared_profile(self) -> None:
        """Mode selection passes the existing rank into a newly started CPU match."""
        session = ConnectFourSession(self.screen, ranking=self.rank)
        session.draw()
        session.selected_index = 1
        session.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        self.assertIsNotNone(session.game)
        self.assertIs(session.game.ranking, self.rank)
        session.draw()


if __name__ == "__main__":
    unittest.main()