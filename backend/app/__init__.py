from __future__ import annotations

from typing import TYPE_CHECKING

from flask import Flask, jsonify
from flask_cors import CORS

from app.api import health, spa
from app.config import Config
from app.errors import TimeTrackError
from app.extensions import db, jwt, limiter, migrate

if TYPE_CHECKING:
    from flask.wrappers import Response


def create_app(config: type[Config] | Config | None = None) -> Flask:
    """Application factory.

    Pass a ``Config`` subclass (or instance) to override defaults — useful for
    tests. With no argument, the environment-selected config is used.
    """
    app = Flask(__name__)
    app.config.from_object(config or Config.from_environment())

    _init_extensions(app)
    _register_error_handlers(app)
    _register_blueprints(app)

    # Import models so SQLAlchemy/Alembic sees them at migration time.
    from app import models  # noqa: F401

    return app


def _init_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    from app.auth.jwt_callbacks import register_jwt_callbacks

    register_jwt_callbacks(jwt)


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(TimeTrackError)
    def handle_app_error(err: TimeTrackError) -> tuple[Response, int]:
        return jsonify(err.to_envelope()), err.status


def _register_blueprints(app: Flask) -> None:
    from app.api import (
        approvals,
        auth,
        clients,
        entries,
        invoices,
        projects,
        reports,
        timer,
    )

    app.register_blueprint(health.bp, url_prefix="/api/v1")
    app.register_blueprint(auth.bp, url_prefix="/api/v1/auth")
    app.register_blueprint(clients.bp, url_prefix="/api/v1/clients")
    app.register_blueprint(projects.bp, url_prefix="/api/v1/projects")
    app.register_blueprint(entries.bp, url_prefix="/api/v1/entries")
    app.register_blueprint(timer.bp, url_prefix="/api/v1/timer")
    app.register_blueprint(approvals.bp, url_prefix="/api/v1/approvals")
    app.register_blueprint(invoices.bp, url_prefix="/api/v1/invoices")
    app.register_blueprint(reports.bp, url_prefix="/api/v1/reports")

    if app.config.get("TESTING", False):
        from app.api import test_helpers

        app.register_blueprint(test_helpers.bp, url_prefix="/api/v1/test")

    app.register_blueprint(spa.bp)
