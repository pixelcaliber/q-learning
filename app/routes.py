from flask import Blueprint, current_app, jsonify, request

from .models.q_learning_agent import QLearningAgent
from .utils.game_logger import GameLogger, process_game_log_for_training
from .utils.game_logic import check_win, get_available_moves, is_board_full

bp = Blueprint("main", __name__)
game_state = {"board": [" "] * 9, "result": None, "turn": "X"}
scoreboard = {"human": 0, "ai": 0, "draw": 0}

agent = QLearningAgent()


def initialize_agent():
    agent.load(current_app.config["MODEL_SAVE_PATH"])


@bp.before_app_request
def setup():
    initialize_agent()


# Initialize game logger
game_logger = GameLogger()


@bp.route("/health")
def health_check():
    return jsonify({"status": "healthy"})


@bp.route("/game")
# @limiter.limit("60 per minute")
def get_game():
    return jsonify(
        {
            "board": game_state["board"],
            "result": game_state["result"],
            "scoreboard": scoreboard,
        }
    )


@bp.route("/reset")
# @limiter.limit("30 per minute")
def reset_game():
    global game_state
    game_state = {"board": [" "] * 9, "result": None, "turn": "X"}
    game_logger.current_game_log = []  # Reset game log
    return jsonify({"board": game_state["board"], "message": "Game reset"})


@bp.route("/move", methods=["POST"])
# @limiter.limit("60 per minute")
def make_move():
    global game_state, scoreboard

    try:
        data = request.get_json()
        if not data or "move" not in data:
            return jsonify({"error": "Invalid request"}), 400

        move = int(data["move"])
        if move < 0 or move > 8:
            return jsonify({"error": "Invalid move"}), 400

        board = game_state["board"]
        if board[move] != " ":
            return jsonify({"error": "Cell already occupied"}), 400

        # Log human move
        game_logger.log_move("human", move, board)

        # Human move
        board[move] = "X"

        # Check human win
        if check_win(board, "X"):
            game_state["result"] = "human win"
            scoreboard["human"] += 1
            game_logger.log_game_result("human win")
            process_game_log_for_training(agent, game_logger.current_game_log)
            agent.save(current_app.config["MODEL_SAVE_PATH"])
            return jsonify(
                {
                    "board": board,
                    "result": "human win",
                    "message": "You win!",
                    "scoreboard": scoreboard,
                }
            )

        # Check draw
        if is_board_full(board):
            game_state["result"] = "draw"
            scoreboard["draw"] += 1
            game_logger.log_game_result("draw")
            process_game_log_for_training(agent, game_logger.current_game_log)
            agent.save(current_app.config["MODEL_SAVE_PATH"])
            return jsonify(
                {
                    "board": board,
                    "result": "draw",
                    "message": "Draw!",
                    "scoreboard": scoreboard,
                }
            )

        # AI move
        available = get_available_moves(board)
        state = agent.get_state_key(board, "O")

        original_epsilon = agent.epsilon
        agent.epsilon = 0
        ai_move, _ = agent.choose_action(state, available)
        agent.epsilon = original_epsilon

        game_logger.log_move("ai", ai_move, board)
        board[int(ai_move)] = "O"

        # Check AI win
        if check_win(board, "O"):
            game_state["result"] = "ai win"
            scoreboard["ai"] += 1
            game_logger.log_game_result("ai win")
            process_game_log_for_training(agent, game_logger.current_game_log)
            agent.save(current_app.config["MODEL_SAVE_PATH"])
            return jsonify(
                {
                    "board": board,
                    "result": "ai win",
                    "message": "AI wins!",
                    "scoreboard": scoreboard,
                }
            )

        # Check draw after AI move
        if is_board_full(board):
            game_state["result"] = "draw"
            scoreboard["draw"] += 1
            game_logger.log_game_result("draw")
            process_game_log_for_training(agent, game_logger.current_game_log)
            agent.save(current_app.config["MODEL_SAVE_PATH"])
            return jsonify(
                {
                    "board": board,
                    "result": "draw",
                    "message": "Draw!",
                    "scoreboard": scoreboard,
                }
            )

        return jsonify(
            {
                "board": board,
                "message": f"Move accepted. AI played cell {ai_move}.",
                "scoreboard": scoreboard,
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
