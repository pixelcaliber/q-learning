import threading

from flask import Blueprint, current_app, jsonify, request

from . import limiter
from .models.q_learning_agent import QLearningAgent
from .utils.game_logger import GameLogger, process_game_log_for_training
from .utils.game_logic import check_win, get_available_moves, is_board_full

bp = Blueprint("main", __name__)
game_state = {"board": [" "] * 9, "result": None, "turn": "X"}
scoreboard = {"human": 0, "ai": 0, "draw": 0}

agent = QLearningAgent()

session_lock = threading.Lock()
sessions = {}


def initialize_agent():
    agent.load(current_app.config["MODEL_SAVE_PATH"])


@bp.before_app_request
def setup():
    initialize_agent()


def initialize_session():
    """Return a new session state including game state, scoreboard, and logger."""
    return {
        "game_state": {"board": [" "] * 9, "result": None, "turn": "X"},
        "scoreboard": {"human": 0, "ai": 0, "draw": 0},
        "game_logger": GameLogger(),
    }


def get_session(session_id):
    """Return the session data for the given session_id, creating one if needed."""
    with session_lock:
        if session_id not in sessions:
            sessions[session_id] = initialize_session()
        return sessions[session_id]


game_logger = GameLogger()


@limiter.limit("100 per minute")
@bp.route("/health")
def health_check():
    return jsonify({"status": "healthy"})


@bp.route("/game")
@limiter.limit("60 per minute")
def get_game():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"error": "Session id required"}), 400
    session_data = get_session(session_id)
    return jsonify(
        {
            "board": session_data["game_state"]["board"],
            "result": session_data["game_state"]["result"],
            "scoreboard": session_data["scoreboard"],
        }
    )


@bp.route("/reset")
@limiter.limit("60 per minute")
def reset_game():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"error": "Session id required"}), 400
    session_data = get_session(session_id)
    session_data["game_state"] = {"board": [" "] * 9, "result": None, "turn": "X"}
    session_data["game_logger"] = GameLogger()
    return jsonify(
        {"board": session_data["game_state"]["board"], "message": "Game reset"}
    )


@bp.route("/delete_session", methods=["POST"])
@limiter.limit("20 per minute")
def delete_session():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"error": "Session id required"}), 400
    with session_lock:
        if session_id in sessions:
            del sessions[session_id]
    return jsonify({"message": "Session deleted"})


class MoveResult:
    def __init__(self):
        self.result = None


def process_move_logic(session_data, move, config, move_result):
    try:
        board = session_data["game_state"]["board"]
        scoreboard = session_data["scoreboard"]
        game_logger = session_data["game_logger"]

        # Validate move
        if move < 0 or move > 8:
            move_result.result = ({"error": "Invalid move"}, 400)
            return

        if board[move] != " ":
            move_result.result = ({"error": "Cell already occupied"}, 400)
            return

        # Log and process human move
        game_logger.log_move("human", move, board)
        board[move] = "X"

        # Check if human wins
        if check_win(board, "X"):
            session_data["game_state"]["result"] = "human win"
            scoreboard["human"] += 1
            game_logger.log_game_result("human win")
            process_game_log_for_training(agent, game_logger.current_game_log)
            agent.save(config["MODEL_SAVE_PATH"])
            move_result.result = (
                {
                    "board": board,
                    "result": "human win",
                    "message": "You win!",
                    "scoreboard": scoreboard,
                },
                200,
            )
            return

        # Check for draw after human move
        if is_board_full(board):
            session_data["game_state"]["result"] = "draw"
            scoreboard["draw"] += 1
            game_logger.log_game_result("draw")
            process_game_log_for_training(agent, game_logger.current_game_log)
            agent.save(config["MODEL_SAVE_PATH"])
            move_result.result = (
                {
                    "board": board,
                    "result": "draw",
                    "message": "Draw!",
                    "scoreboard": scoreboard,
                },
                200,
            )
            return

        # AI move
        available = get_available_moves(board)
        state = agent.get_state_key(board, "O")
        original_epsilon = agent.epsilon
        agent.epsilon = 0  # force exploitation
        ai_move, _ = agent.choose_action(state, available)
        agent.epsilon = original_epsilon

        game_logger.log_move("ai", ai_move, board)
        board[int(ai_move)] = "O"

        # Check if AI wins
        if check_win(board, "O"):
            session_data["game_state"]["result"] = "ai win"
            scoreboard["ai"] += 1
            game_logger.log_game_result("ai win")
            process_game_log_for_training(agent, game_logger.current_game_log)
            agent.save(config["MODEL_SAVE_PATH"])
            move_result.result = (
                {
                    "board": board,
                    "result": "ai win",
                    "message": "AI wins!",
                    "scoreboard": scoreboard,
                },
                200,
            )
            return

        # Check for draw after AI move
        if is_board_full(board):
            session_data["game_state"]["result"] = "draw"
            scoreboard["draw"] += 1
            game_logger.log_game_result("draw")
            process_game_log_for_training(agent, game_logger.current_game_log)
            agent.save(config["MODEL_SAVE_PATH"])
            move_result.result = (
                {
                    "board": board,
                    "result": "draw",
                    "message": "Draw!",
                    "scoreboard": scoreboard,
                },
                200,
            )
            return

        # If game continues, set turn back to human and respond with current state.
        session_data["game_state"]["turn"] = "X"
        move_result.result = (
            {
                "board": board,
                "message": f"Move accepted. AI played cell {ai_move}.",
                "scoreboard": scoreboard,
            },
            200,
        )
    except Exception as e:
        move_result.result = ({"error": str(e)}, 500)


@bp.route("/move", methods=["POST"])
@limiter.limit("60 per minute")
def make_move():
    data = request.get_json()
    if not data or "move" not in data or "session_id" not in data:
        return (
            jsonify({"error": "Invalid request. 'move' and 'session_id' required"}),
            400,
        )
    try:
        move = int(data["move"])
    except ValueError:
        return jsonify({"error": "Move must be an integer"}), 400

    session_id = data["session_id"]
    session_data = get_session(session_id)
    move_result = MoveResult()
    # Start a new thread to process the move concurrently.
    thread = threading.Thread(
        target=process_move_logic,
        args=(session_data, move, current_app.config, move_result),
    )
    thread.start()
    thread.join()  # Wait for the thread to complete.

    response, status = move_result.result
    return jsonify(response), status
