"""Application factory for the Order API."""

from flask import Flask

from .api import api_bp
from .config import Config
from .domain_api import MODELS, domain_bp
from .domain_store import create_domain_store
from .errors import register_error_handlers


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Each app instance gets its own store, which keeps tests isolated.
    app.extensions["domain_store"] = create_domain_store(app.config, MODELS)

    register_error_handlers(app)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(domain_bp, url_prefix="/api/v2")

    return app
