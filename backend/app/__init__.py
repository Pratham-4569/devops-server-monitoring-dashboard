from flask import Flask
from flask_cors import CORS

from app.config import Config
from app.exceptions import AppError
from app.routes.api import api_bp
from app.utils.response import error_response


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Nginx proxies /api to Flask on one origin; CORS is optional for local `python run.py`.
    if app.config.get("CORS_ENABLED", True):
        CORS(app)

    app.register_blueprint(api_bp)

    @app.errorhandler(AppError)
    def handle_app_error(exc):
        return error_response(exc.message, status_code=exc.status_code, code=exc.code)

    @app.errorhandler(404)
    def handle_not_found(_error):
        return error_response("Endpoint not found", status_code=404, code="NOT_FOUND")

    @app.errorhandler(500)
    def handle_server_error(_error):
        return error_response(
            "An unexpected error occurred",
            status_code=500,
            code="INTERNAL_ERROR",
        )

    return app
