"""Provide a local two-player Connect Four game with replaceable pixel artwork."""

from pathlib import Path
import random

import pygame

from .assets import DEFAULT_SPRITE_RECTS, PLAYER_COLORS, ConnectFourAssets
from .cpu import choose_column
from .ranking import CpuRanking
from .renderer import ConnectFourRenderer
from .rules import find_winning_cells


class ConnectFour:
	"""Two-player game with event, update, and draw hooks for a Pygame loop.

	Optional transparent PNGs in asset_dir: board_tile.png, red_piece.png,
	yellow_piece.png, and background.png. Missing images use pixel placeholders.
	Mapped spritesheet crops take priority over individual PNGs. The host calls
	handle_event for input, update with elapsed seconds, and draw each frame.
	"""

	# Board entries use 0 for empty, 1 for red, and 2 for yellow.
	ROWS = 6
	COLUMNS = 7
	EMPTY = 0
	RED_PLAYER = 1
	YELLOW_PLAYER = 2
	PLAYER_NAMES = {RED_PLAYER: "Red", YELLOW_PLAYER: "Yellow"}
	FALL_SPEED = 950
	CPU_DELAY_SECONDS = 0.4
	PLAYER_COLORS = PLAYER_COLORS
	# Source rectangles are (x, y, width, height), measured in sheet pixels.
	DEFAULT_SPRITE_RECTS = DEFAULT_SPRITE_RECTS

	def __init__(
		self,
		screen: pygame.Surface,
		asset_dir: str | Path | None = None,
		*,
		spritesheet_path: str | Path | None = None,
		sprite_rects: dict[str, tuple[int, int, int, int]] | None = None,
		vs_cpu: bool = False,
		ranking: CpuRanking | None = None,
	) -> None:
		"""Prepare the layout, cache artwork, and start a new game.

		Args:
		    screen: Fixed-size surface on which the game renders.
		    asset_dir: Asset folder; defaults to Game/assets/connect_four.
		    spritesheet_path: Explicit path; otherwise use connect_four_spritesheet.png.
		    sprite_rects: Asset filenames mapped to (x, y, width, height) crops.
		        None uses DEFAULT_SPRITE_RECTS; a mapping replaces those defaults.
		    vs_cpu: Randomly assign human and CPU colours for each new match.
		    ranking: Shared CPU-mode progress; loads saved progress when omitted.

		Raises:
		    ValueError: The surface is too small or a sheet crop is invalid.

		Explicit sheet paths are relative to the working directory unless absolute.
		Image-loading errors propagate rather than silently hiding invalid artwork.
		"""
		if not pygame.font.get_init():
			pygame.font.init()
		self.screen = screen
		self.vs_cpu = vs_cpu
		self.ranking = None
		if vs_cpu:
			self.ranking = ranking if ranking is not None else CpuRanking()
		self._create_layout()
		self._load_artwork(asset_dir, spritesheet_path, sprite_rects)
		self.renderer = ConnectFourRenderer(self)
		# Keep gesture tracking across game resets, including a held restart tap.
		self._active_fingers: set[int] = set()
		self._received_finger_events = False
		self.reset()

	def _create_layout(self) -> None:
		"""Fit the board and controls to the window and prepare label fonts."""
		screen = self.screen
		self.cell_size = min((screen.get_width() - 24) // self.COLUMNS, 64)
		board_height = self.cell_size * self.ROWS
		if self.cell_size < 16 or screen.get_height() < board_height + 220:
			raise ValueError("The window is too small for the board and controls.")

		board_width = self.cell_size * self.COLUMNS
		board_left = (screen.get_width() - board_width) // 2
		board_top = (screen.get_height() - board_height) // 2 + 20
		self.board_rect = pygame.Rect(
			board_left, board_top, board_width, board_height,
		)
		self.restart_rect = pygame.Rect(
			screen.get_width() // 2 - 65, self.board_rect.bottom + 28, 130, 48
		)
		self.title_font = pygame.font.Font(None, 38)
		self.font = pygame.font.Font(None, 26)
		self.small_font = pygame.font.Font(None, 21)

	def _load_artwork(
		self,
		asset_dir: str | Path | None,
		spritesheet_path: str | Path | None,
		sprite_rects: dict[str, tuple[int, int, int, int]] | None,
	) -> None:
		"""Load and scale the game's artwork once, before the frame loop starts."""
		if sprite_rects is None:
			sprite_rects = self.DEFAULT_SPRITE_RECTS
		self.assets = ConnectFourAssets(
			asset_dir,
			spritesheet_path=spritesheet_path,
			sprite_rects=sprite_rects,
		)
		# Keep existing asset attributes available to callers of ConnectFour.
		self.asset_dir = self.assets.asset_dir
		self.sprite_rects = self.assets.sprite_rects
		self.spritesheet = self.assets.spritesheet
		tile_size = (self.cell_size, self.cell_size)
		self.board_tile = self._load_asset("board_tile.png", tile_size)
		self.pieces = {
			self.RED_PLAYER: self._load_asset("red_piece.png", tile_size),
			self.YELLOW_PLAYER: self._load_asset("yellow_piece.png", tile_size),
		}
		self.background = self._load_asset("background.png", self.screen.get_size())

	def _load_asset(self, filename: str, size: tuple[int, int]) -> pygame.Surface:
		"""Return artwork at size using a sheet, standalone PNG, or placeholder.

		filename identifies a known game asset; size is the output width and height.
		Configured crops and existing images must be valid or loading raises an error.
		"""
		return self.assets.load(filename, size)

	def reset(self) -> None:
		"""Start a fresh match, reassigning CPU-mode colours; red always moves first.

		Artwork and ranking are retained. Unfinished matches do not affect rank.
		"""
		self.human_player = self.RED_PLAYER
		if self.vs_cpu:
			self.human_player = random.choice((self.RED_PLAYER, self.YELLOW_PLAYER))
		self.cpu_player = self.YELLOW_PLAYER if self.human_player == self.RED_PLAYER else self.RED_PLAYER
		self.player_names = dict(self.PLAYER_NAMES)
		if self.vs_cpu:
			self.player_names[self.human_player] = f"You ({self.PLAYER_NAMES[self.human_player]})"
			self.player_names[self.cpu_player] = f"CPU ({self.PLAYER_NAMES[self.cpu_player]})"
		self.rating_change: int | None = None
		self._result_recorded = False
		# Create independent rows so changing one cell never changes another row.
		self.board = [[self.EMPTY] * self.COLUMNS for _ in range(self.ROWS)]
		self.current_player = self.RED_PLAYER
		self.winner: int | None = None
		self.is_draw = False
		self.winning_cells: list[tuple[int, int]] = []
		self.selected_column = self.COLUMNS // 2
		self.message = f"{self.player_names[self.current_player]}'s turn"
		# Animation stores the destination row, column, and player; y is in pixels.
		self.animation: tuple[int, int, int] | None = None
		self.animation_y = 0.0
		self._cpu_wait_seconds = 0.0

	@property
	def is_cpu_turn(self) -> bool:
		"""Return whether the assigned CPU colour has the next move."""
		return self.vs_cpu and self.current_player == self.cpu_player and not self.game_over

	@property
	def game_over(self) -> bool:
		"""Return whether the completed game has a winner or a draw."""
		return self.winner is not None or self.is_draw

	def drop_piece(self, column: int) -> bool:
		"""Attempt to drop the current player's piece into a zero-based column.

		Return True when a cell is reserved and its falling animation starts.
		Return False for an invalid or full column, an active animation, or game over.
		Turn changes and result detection occur in update after the piece lands.
		"""
		if self.is_cpu_turn:
			return False
		return self._start_drop(column)

	def _start_drop(self, column: int) -> bool:
		"""Reserve a legal move and animate it for either a human or the CPU."""
		# Lock input while a piece falls so turns cannot overlap.
		if self.game_over or self.animation is not None:
			return False
		if not 0 <= column < self.COLUMNS:
			return False
		row = self._find_open_row(column)
		if row is None:
			self.message = "Column full"
			return False

		# Reserve the destination now, but wait until landing to resolve the turn.
		self.board[row][column] = self.current_player
		self.animation = (row, column, self.current_player)
		self.animation_y = float(self.board_rect.top - self.cell_size)
		return True

	def _find_open_row(self, column: int) -> int | None:
		"""Find the lowest empty cell in a valid column, or None if it is full."""
		for row in reversed(range(self.ROWS)):
			if self.board[row][column] == self.EMPTY:
				return row
		return None

	def _finish_move(self, row: int, column: int, player: int) -> None:
		"""Resolve a landed move by recording a win, a draw, or the next turn.

		row and column are the occupied destination cell; player is its owner (1 or 2).
		Winning cells are retained so draw can highlight the completed line.
		"""
		if self.game_over:
			return
		cells = find_winning_cells(self.board, row, column, player)
		if cells:
			self.winner = player
			self.winning_cells = cells
			self.message = f"{self.player_names[player]} wins!"
			self._record_ranked_result()
			return
		# With gravity, a full top row means the entire board is full.
		# Check this after wins so a winning final move is not reported as a draw.
		if all(self.board[0]):
			self.is_draw = True
			self.message = "Draw!"
			self._record_ranked_result()
			return
		if player == self.RED_PLAYER:
			self.current_player = self.YELLOW_PLAYER
		else:
			self.current_player = self.RED_PLAYER
		self._cpu_wait_seconds = 0.0
		self.message = f"{self.player_names[self.current_player]}'s turn"

	def _record_ranked_result(self) -> None:
		"""Save a completed CPU result once, relative to the human's assigned colour."""
		if self.ranking is None or self._result_recorded or not self.game_over:
			return
		self._result_recorded = True
		if self.is_draw:
			self.rating_change = self.ranking.record("draw")
		elif self.winner == self.human_player:
			self.rating_change = self.ranking.record("win")
		else:
			self.rating_change = self.ranking.record("loss")

	def handle_event(self, event: pygame.event.Event) -> None:
		"""Process keyboard, mouse, or touchscreen input.

		Arrows select columns; Space, Enter, or Down drop a piece. R resets the game.
		Click or tap a column to drop, or the new-game button to restart.
		Only the first finger in a gesture activates controls.
		Window-close events remain the host loop's responsibility.
		"""
		if event.type == pygame.FINGERDOWN:
			self._handle_touch(event)
		elif event.type == pygame.FINGERUP:
			self._active_fingers.discard(event.finger_id)
		elif event.type == pygame.KEYDOWN:
			self._handle_key(event.key)
		elif event.type == pygame.MOUSEMOTION:
			if self._is_duplicate_touch_mouse(event):
				return
			if self.board_rect.left <= event.pos[0] < self.board_rect.right:
				self.selected_column = self._column_at(event.pos[0])
		elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
			if self._is_duplicate_touch_mouse(event):
				return
			self._handle_click(event.pos)
		elif event.type == pygame.WINDOWFOCUSLOST:
			# Switching apps can interrupt a gesture before its finger-up arrives.
			self._active_fingers.clear()

	def _handle_touch(self, event: pygame.event.Event) -> None:
		"""Activate a control once using normalized finger coordinates (0 to 1)."""
		self._received_finger_events = True
		is_first_finger = not self._active_fingers
		self._active_fingers.add(event.finger_id)
		if not is_first_finger:
			return

		# Use logical game dimensions, not iPhone hardware pixels or pixel density.
		width, height = self.screen.get_size()
		position = (int(event.x * width), int(event.y * height))
		self._handle_click(position)

	def _is_duplicate_touch_mouse(self, event: pygame.event.Event) -> bool:
		"""Ignore synthetic mouse input only when native finger events are available.

		Mouse-only browser backends can still deliver taps as ordinary clicks.
		Physical mouse events remain usable after touching the screen.
		"""
		return self._received_finger_events and getattr(event, "touch", False)

	def _handle_key(self, key: int) -> None:
		"""Apply a keyboard command, wrapping column selection at either edge."""
		if key == pygame.K_r:
			self.reset()
		elif key == pygame.K_LEFT:
			self.selected_column = (self.selected_column - 1) % self.COLUMNS
		elif key == pygame.K_RIGHT:
			self.selected_column = (self.selected_column + 1) % self.COLUMNS
		elif key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_DOWN):
			self.drop_piece(self.selected_column)

	def _handle_click(self, position: tuple[int, int]) -> None:
		"""Restart or drop a piece when a click or tap hits a game control."""
		if self.restart_rect.collidepoint(position):
			self.reset()
		elif self.board_rect.collidepoint(position):
			self.selected_column = self._column_at(position[0])
			self.drop_piece(self.selected_column)

	def _column_at(self, mouse_x: int) -> int:
		"""Convert a horizontal position within the board to a column index."""
		return (mouse_x - self.board_rect.left) // self.cell_size

	def update(self, delta_time: float) -> None:
		"""Advance a falling piece by delta_time seconds and resolve it on landing.

		Negative elapsed times are treated as zero. Between animations the CPU
		waits briefly before making its move, without blocking the frame loop.
		"""
		if self.animation is None:
			self._update_cpu(delta_time)
			return
		row, column, player = self.animation
		target_y = self.board_rect.top + row * self.cell_size
		elapsed_seconds = max(0.0, delta_time)
		distance = self.FALL_SPEED * elapsed_seconds
		# Clamp the position so a slow frame cannot move the piece past its cell.
		self.animation_y = min(target_y, self.animation_y + distance)
		if self.animation_y >= target_y:
			self.animation = None
			self._finish_move(row, column, player)

	def _update_cpu(self, delta_time: float) -> None:
		"""Start one CPU move after a short delay; leave human turns unchanged."""
		if not self.is_cpu_turn:
			return
		self._cpu_wait_seconds += max(0.0, delta_time)
		if self._cpu_wait_seconds < self.CPU_DELAY_SECONDS:
			return

		column = choose_column(self.board, self.cpu_player, self.human_player)
		if column is not None:
			self.selected_column = column
			self._start_drop(column)

	def _draw_text(self, text: str, font: pygame.font.Font, center: tuple[int, int]) -> None:
		"""Render text with font at the given pixel center on the game surface."""
		self.renderer.draw_text(text, font, center)

	def draw(self) -> None:
		"""Paint the current state without advancing gameplay or flipping the display.

		Render the background, status, preview, pieces, board overlay, win outlines,
		and restart control. The host presents the completed frame afterward.
		"""
		self.renderer.draw()
