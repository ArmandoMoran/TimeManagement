from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask.testing import FlaskClient


def test_health_endpoint_returns_ok(client: FlaskClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
