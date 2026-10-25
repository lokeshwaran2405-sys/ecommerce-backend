from flask import jsonify


class AppError(Exception):
    status_code = 500

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class ValidationError(AppError):
    status_code = 400


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"error": err.message}), err.status_code

    @app.errorhandler(404)
    def handle_404(_):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(405)
    def handle_405(_):
        return jsonify({"error": "Method not allowed"}), 405
