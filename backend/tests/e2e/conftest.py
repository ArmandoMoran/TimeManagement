from __future__ import annotations

import threading
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import requests
from app import create_app
from app.config import TestConfig
from werkzeug.serving import make_server

if TYPE_CHECKING:
    from collections.abc import Iterator

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"


class E2EConfig(TestConfig):
    """Wires the built frontend into the Flask app for full-stack e2e tests."""

    FRONTEND_DIST_PATH = str(FRONTEND_DIST)


@pytest.fixture(scope="session")
def flask_server() -> Iterator[str]:
    if not FRONTEND_DIST.exists():
        pytest.skip(f"frontend not built — run `npm run build` in {PROJECT_ROOT / 'frontend'}")

    app = create_app(E2EConfig)
    with app.app_context():
        # Ensure schema exists on the test DB before the server starts handling requests.
        from app.extensions import db

        db.create_all()

    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)


@pytest.fixture(autouse=True)
def _reset_between_tests(flask_server: str) -> Iterator[None]:
    yield
    requests.post(f"{flask_server}/api/v1/test/reset", timeout=10).raise_for_status()


@pytest.fixture
def admin_account(flask_server: str) -> dict[str, str]:
    """Seed and return a bootstrap admin via the API."""
    creds = {
        "email": "admin@example.com",
        "password": "long-enough-pw",
        "name": "Admin",
    }
    response = requests.post(
        f"{flask_server}/api/v1/auth/register",
        json=creds,
        timeout=10,
    )
    response.raise_for_status()
    body = response.json()
    return {
        **creds,
        "access_token": body["access_token"],
        "refresh_token": body["refresh_token"],
        "user_id": body["user"]["id"],
    }
