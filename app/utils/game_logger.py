import json
import os
from datetime import datetime


class GameLogger:
    def __init__(self, log_dir="instance/game_logs"):
        self.log_dir = log_dir
        self.current_game_log = []
        os.makedirs(log_dir, exist_ok=True)

    def log_move(self, player, move, board_before):
        """Log a single move in the current game."""
        self.current_game_log.append(
            {
                "player": player,
                "move": move,
                "board_before": board_before.copy(),
            }
        )

    def log_game_result(self, result):
        """Log the game result and save the complete game log."""
        self.current_game_log.append(
            {"result": result, "timestamp": datetime.utcnow().isoformat()}
        )
        self._save_game_log()

    def _save_game_log(self):
        """Save the current game log to a file."""
        if not self.current_game_log:
            return

        # timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"human_games_log.jsonl"
        filepath = os.path.join(self.log_dir, filename)

        with open(filepath, "w") as f:
            #     json.dump(self.current_game_log, f)
            # with open("human_games_log.jsonl", "a") as f:
            f.write(json.dumps(self.current_game_log) + "\n")
        self.current_game_log = []


def process_game_log_for_training(agent, game_log):
    """Process a complete game log to train the agent."""
    print("Processing game log for learning")
    result = next(
        (entry["result"] for entry in reversed(game_log) if "result" in entry), None
    )

    for idx, entry in enumerate(game_log):
        if entry.get("player") == "ai":
            board_before = entry["board_before"]
            action = int(entry["move"])
            state = agent.get_state_key(board_before, "O")

            # Create board after AI move
            board_after_ai = board_before.copy()
            board_after_ai[action] = "O"

            # Calculate reward
            reward = 0
            next_state = None

            # Determine reward based on game outcome
            if check_win(board_after_ai, "O"):
                reward = 1
                next_state = None
            elif " " not in board_after_ai:  # Draw
                reward = 0.5
                next_state = None
            else:
                # Look ahead to human's response
                if idx + 1 < len(game_log):
                    next_entry = game_log[idx + 1]
                    if next_entry.get("player") == "human":
                        human_move = next_entry["move"]
                        board_after_human = board_after_ai.copy()
                        board_after_human[human_move] = "X"

                        if check_win(board_after_human, "X"):
                            reward = -1
                            next_state = None
                        elif " " not in board_after_human:
                            reward = 0.5
                            next_state = None
                        else:
                            next_state = agent.get_state_key(board_after_human, "O")
                            reward = 0  # Neutral reward for continuing game

            # Update Q-values
            agent.update_q_value(state, action, reward, next_state)


def load_human_games(log_filename):
    """Load human games from a JSON-lines file.
    Returns a list of game episodes (each episode is a list of move dictionaries).
    """
    episodes = []
    if not os.path.exists(log_filename):
        return episodes
    with open(log_filename, "r") as f:
        for line in f:
            try:
                episode = json.loads(line.strip())
                episodes.append(episode)
            except Exception as e:
                print("Error reading a log line:", e)
    return episodes


def replay_human_game(agent, game_episode):
    """Replay one human game log and update the agent for each agent move.
    Each move record that has "player"=="ai" is updated with the final reward.
    """
    # Determine final reward based on game result:
    final_reward = 0
    for record in game_episode:
        if "result" in record:
            if record["result"] == "ai win":
                final_reward = 1
            elif record["result"] == "human win":
                final_reward = -1
            elif record["result"] == "draw":
                final_reward = 0
            break
    # Replay each move for agent ("O")
    for record in game_episode:
        if record.get("player") == "ai":
            board_before = record.get("board_before")
            if board_before is None:
                continue
            action = record.get("move")
            # Reconstruct next state by applying the move:
            new_board = board_before.copy()
            new_board[action] = "O"
            state = agent.get_state_key(board_before, "O")
            next_state = agent.get_state_key(new_board, "O")
            agent.update_q_value(state, action, final_reward, next_state)


def batch_train_from_logs(agent, log_dir):
    """Train the agent from all available game logs."""
    human_episodes = load_human_games("human_games_log.jsonl")
    if human_episodes:
        print(
            f"Replaying {len(human_episodes)} human game(s) for additional training..."
        )
        for ep_log in human_episodes:
            replay_human_game(agent, ep_log)

    agent.save("trained_model.pickle")
