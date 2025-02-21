import os
import pickle
import random

import numpy as np


class QLearningAgent:
    def __init__(self, alpha=0.5, gamma=0.9, epsilon=0.1):
        self.q_table = {}
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon

    def get_state_key(self, board, player):
        return (tuple(board), player)

    def get_q_value(self, state, action):
        return self.q_table.get((state, action), 0.0)

    def choose_action(self, state, available_actions, training=False):
        if random.random() < self.epsilon:
            return random.choice(available_actions), "exploration"
        q_values = [self.get_q_value(state, a) for a in available_actions]
        max_q = max(q_values)
        best_actions = [a for a, q in zip(available_actions, q_values) if q == max_q]
        return random.choice(best_actions), "exploitation"

    def update_q_value(self, state, action, reward, next_state):
        print(
            f"Updating Q-value for state {state}, action {action}, reward {reward}, next_state {next_state}"
        )
        old_q = self.get_q_value(state, action)

        # Handle terminal state where there's no next state
        if next_state is None:
            future_rewards = 0
        else:
            available = get_available_moves(list(next_state[0]))
            future_rewards = max(
                [self.get_q_value(next_state, a) for a in available] or [0]
            )

        new_q = old_q + self.alpha * (reward + self.gamma * future_rewards - old_q)
        self.q_table[(state, action)] = new_q

    def save(self, filename):
        with open(filename, "wb") as f:
            pickle.dump(
                {
                    "q_table": self.q_table,
                    "alpha": self.alpha,
                    "gamma": self.gamma,
                    "epsilon": self.epsilon,
                },
                f,
            )

    def load(self, filename):
        with open(filename, "rb") as f:
            data = pickle.load(f)
            self.q_table = data.get("q_table", {})
            self.alpha = data.get("alpha", self.alpha)
            self.gamma = data.get("gamma", self.gamma)
            self.epsilon = data.get("epsilon", self.epsilon)
