from flask import Flask
from .config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Register routes from main.py
    from .main import app as main_app
    app.register_blueprint(main_app)

    return app
