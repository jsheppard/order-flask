"""Configuration classes. Select one with the APP_CONFIG environment variable."""

import os


class Config:
    DEBUG = False
    TESTING = False
    JSON_SORT_KEYS = False

    # order-models resources (/api/v2) are stored in MongoDB. MONGODB_URI is read first;
    # SPRING_MONGODB_URI is accepted as a fallback (the Spring order-data app's variable).
    DOMAIN_STORE = "mongo"  # or "memory"
    MONGODB_URI = os.environ.get("MONGODB_URI") or os.environ.get("SPRING_MONGODB_URI")
    # Optional: overrides the database named in the URI path.
    MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE")


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    DOMAIN_STORE = "memory"  # tests never touch MongoDB


CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": Config,
}
