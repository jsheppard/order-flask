"""Consistent JSON error responses."""

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    """Raise from anywhere in a request to return a JSON error response."""

    def __init__(self, status: int, message: str, errors: list[str] | None = None):
        super().__init__(message)
        self.status = status
        self.message = message
        self.errors = errors or []


def _error_body(code: int, message: str, errors: list[str] | None = None) -> dict:
    body = {"error": {"code": code, "message": message}}
    if errors:
        body["error"]["details"] = errors
    return body


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def handle_api_error(err: ApiError):
        return jsonify(_error_body(err.status, err.message, err.errors)), err.status

    @app.errorhandler(HTTPException)
    def handle_http_exception(err: HTTPException):
        response = jsonify(_error_body(err.code or 500, err.name, [err.description]))
        response.status_code = err.code or 500
        # Keep protocol headers such as Allow on 405; Content-Type stays JSON.
        for name, value in err.get_headers():
            if name.lower() != "content-type":
                response.headers[name] = value
        return response

    @app.errorhandler(Exception)
    def handle_unexpected(err: Exception):
        app.logger.exception("Unhandled error")
        return jsonify(_error_body(500, "Internal server error")), 500
