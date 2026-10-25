"""Check Connect Four winning lines without depending on Pygame."""

WIN_LENGTH = 4
# (row step, column step): horizontal, vertical, and the two diagonal axes.
WIN_DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))


def find_winning_cells(
    board: list[list[int]],
    row: int,
    column: int,
    player: int,
) -> list[tuple[int, int]]:
    """Return a winning line through an occupied cell, or an empty list.

    The board must be a nonempty rectangular grid with the specified player's
    piece at (row, column). Coordinates are zero-based, with row zero at the top.
    All contiguous cells on the first winning axis are returned for highlighting.
    """
    rows = len(board)
    columns = len(board[0])
    # A new win can only pass through the last placed piece.
    for row_step, column_step in WIN_DIRECTIONS:
        cells = [(row, column)]
        # Scan both directions along horizontal, vertical, and diagonal axes.
        for direction in (-1, 1):
            next_row = row + row_step * direction
            next_column = column + column_step * direction
            while (
                0 <= next_row < rows
                and 0 <= next_column < columns
                and board[next_row][next_column] == player
            ):
                cells.append((next_row, next_column))
                next_row += row_step * direction
                next_column += column_step * direction
        if len(cells) >= WIN_LENGTH:
            return cells
    return []