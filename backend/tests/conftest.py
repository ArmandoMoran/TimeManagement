from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from app import create_app
from app.config import TestConfig
from app.extensions import db

if TYPE_CHECKING:
    from collections.abc import Iterator

    from flask import Flask
    from flask.testing import FlaskClient
    from flask_sqlalchemy.session import Session as _FlaskSASession
    from sqlalchemy.orm import scoped_session


@pytest.fixture(scope="session")
def _app() -> Flask:
    return create_app(TestConfig)


@pytest.fixture(scope="session", autouse=True)
def _db_schema(_app: Flask) -> Iterator[None]:
    """Create all tables once per session against the test DB."""
    with _app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()


@pytest.fixture
def app(_app: Flask) -> Iterator[Flask]:
    with _app.app_context():
        yield _app


@pytest.fixture(autouse=True)
def _isolate_db(app: Flask) -> Iterator[None]:
    """Truncate every table after each test so tests can't leak rows.

    Using ``DELETE`` (not ``TRUNCATE``) inside a single transaction commit keeps
    sequences if any, and works without ``RESTART IDENTITY`` privileges.
    """
    yield
    for table in reversed(db.metadata.sorted_tables):
        db.session.execute(table.delete())
    db.session.commit()


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


@pytest.fixture
def session(app: Flask) -> scoped_session[_FlaskSASession]:
    _ = app  # establishes app context for the session
    return db.session
