from __future__ import annotations

import os
from typing import Literal

Environment = Literal["development", "test", "production"]


class Config:
    """Base configuration.

    Subclasses override per environment. Selection is driven by ``FLASK_ENV``.
    """

    ENV: Environment = "development"
    DEBUG: bool = False
    TESTING: bool = False

    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://timetrack:timetrack@localhost:15432/timetrack",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    SECRET_KEY: str = os.environ.get(
        "SECRET_KEY",
        "dev-secret-change-me-also-this-is-long-enough-for-hs256",
    )
    JWT_SECRET_KEY: str = os.environ.get(
        "JWT_SECRET_KEY",
        "dev-jwt-secret-change-me-also-this-is-long-enough-for-hs256",
    )
    JWT_ACCESS_TOKEN_EXPIRES: int = 15 * 60  # 15 minutes
    JWT_REFRESH_TOKEN_EXPIRES: int = 7 * 24 * 60 * 60  # 7 days

    DEFAULT_CURRENCY: str = "USD"
    BOOTSTRAP_ADMIN_EMAIL: str | None = os.environ.get("BOOTSTRAP_ADMIN_EMAIL")
    BOOTSTRAP_ADMIN_PASSWORD: str | None = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD")

    RATELIMIT_STORAGE_URI: str = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_HEADERS_ENABLED: bool = True

    @staticmethod
    def from_environment() -> type[Config]:
        env = os.environ.get("FLASK_ENV", "development").lower()
        match env:
            case "test" | "testing":
                return TestConfig
            case "production" | "prod":
                return ProductionConfig
            case _:
                return DevelopmentConfig


class DevelopmentConfig(Config):
    ENV = "development"
    DEBUG = True


class TestConfig(Config):
    ENV = "test"
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql+psycopg://timetrack:timetrack@localhost:15432/timetrack_test",
    )
    # Disable per-IP rate limits inside tests — the loopback address accumulates
    # quickly across many tests and pollutes assertions about real responses.
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    ENV = "production"
    DEBUG = False
