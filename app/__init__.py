from flask import Flask, jsonify

from .config import Config
from .db import close_db, init_db
from .errors import register_error_handlers


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    init_db(app.config["DATABASE"])
    app.teardown_appcontext(close_db)
    register_error_handlers(app)

    from .controllers import register_blueprints
    register_blueprints(app)

    @app.get("/health")
    def health():
        return jsonify({"status": "UP"})

    return app
