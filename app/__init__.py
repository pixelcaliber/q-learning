from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from .config import Config

limiter = Limiter(
    key_func=get_remote_address, storage_uri=Config.RATE_LIMIT_STORAGE_URL
)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)
    limiter.init_app(app)

    from .routes import bp

    app.register_blueprint(bp)

    return app
