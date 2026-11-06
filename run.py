"""Entry point: `python run.py` for development, or use gunicorn/waitress in production."""

import os

from app import create_app
from app.config import CONFIGS

config_name = os.environ.get("APP_CONFIG", "development")
app = create_app(CONFIGS[config_name])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
