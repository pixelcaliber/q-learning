def check_win(board, player):
    win_conditions = [
        [0, 1, 2],
        [3, 4, 5],
        [6, 7, 8],  # rows
        [0, 3, 6],
        [1, 4, 7],
        [2, 5, 8],  # columns
        [0, 4, 8],
        [2, 4, 6],  # diagonals
    ]
    return any(all(board[i] == player for i in cond) for cond in win_conditions)


def get_available_moves(board):
    return [i for i, cell in enumerate(board) if cell == " "]


def is_board_full(board):
    return " " not in board
    