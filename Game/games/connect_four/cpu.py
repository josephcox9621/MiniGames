"""Choose legal CPU moves using the game's existing winning-line rules."""

from .rules import find_winning_cells


def choose_column(board: list[list[int]], cpu_player: int, human_player: int) -> int | None:
    """Win immediately, block an immediate loss, or prefer the centre column.

    Return None when the board is full. Trial moves use a copy so the live game
    board never changes while the CPU is deciding.
    """
    column_count = len(board[0])
    centre = column_count // 2
    legal_columns = [column for column in range(column_count) if board[0][column] == 0]
    legal_columns.sort(key=lambda column: abs(column - centre))
    trial_board = [row.copy() for row in board]

    for player in (cpu_player, human_player):
        for column in legal_columns:
            row = next(row for row in reversed(range(len(board))) if board[row][column] == 0)
            trial_board[row][column] = player
            winning_cells = find_winning_cells(trial_board, row, column, player)
            trial_board[row][column] = 0
            if winning_cells:
                return column

    return legal_columns[0] if legal_columns else None