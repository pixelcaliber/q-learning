import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key-change-this")
    MODEL_SAVE_PATH = os.getenv(
        "MODEL_SAVE_PATH", "instance/models/tictactoe_model.pkl"
    )
    RATE_LIMIT_STORAGE_URL = os.getenv("RATE_LIMIT_STORAGE_URL", "memory://")
