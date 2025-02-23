## Q-Learning Agent

### Concept and Theory

Q-learning is a type of reinforcement learning algorithm where an agent learns to take actions in an environment by maximizing a cumulative reward. Key concepts include:

- **State:**  
  The current configuration of the Tic Tac Toe board.
- **Action:**  
  A move (placing an 'X' or 'O') in an available cell.
- **Reward:**  
  Feedback received after each move (e.g., winning gives a positive reward, losing gives a negative reward).
- **Q-Value:**  
  The expected future reward for taking a certain action from a given state. The agent updates these Q-values over time based on its experience.
- **Exploration vs. Exploitation:**  
  The agent uses an epsilon-greedy strategy to balance between exploring new moves and exploiting known moves with high Q-values.

### Agent Training and Decision Making

1. **Initialization:**  
   The agent loads a pre-saved model (if available) at the start of each request.
2. **Choosing an Action:**  
   The agent examines the board state, evaluates available moves, and selects a move by balancing between exploration (random moves) and exploitation (best-known move).
3. **Learning from Experience:**  
   After each game, the game logger stores the moves and results. The agent uses this log to update its Q-values through the learning process.
4. **Model Persistence:**  
   The updated model is saved to disk so that the agent can retain its learning across sessions.

## API Endpoints

- **GET /health:**  
  Checks the health of the application.
- **GET /game?session_id=YOUR_SESSION_ID:**  
  Returns the current game state, including the board, result, and scoreboard.
- **POST /move:**  
  Submits a move. Requires a JSON payload with `move` and `session_id`.
- **GET /reset?session_id=YOUR_SESSION_ID:**  
  Resets the game board (preserving the scoreboard).
- **GET /delete_session?session_id=YOUR_SESSION_ID:**  
  Deletes the session data when the user closes the tab.

> **Rate Limiting:**  
> All endpoints are rate-limited using Flask-Limiter to prevent abuse. For example, the `/move` endpoint is limited to 60 requests per minute.

## Running the Project

- **Backend Setup:**
 - Install dependencies: `pip install -r requirements.txt`
 - Set up configuration (e.g., `Config.RATE_LIMIT_STORAGE_URL`, `MODEL_SAVE_PATH`).
 - Run the Flask app: `flask run`
- **Frontend**: https://github.com/pixelcaliber/t3-ai/blob/master/README.md
