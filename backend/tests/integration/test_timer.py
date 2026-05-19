from __future__ import annotations

import time
from typing import TYPE_CHECKING

from tests.integration._factories import (
    auth_headers,
    bootstrap_admin,
    create_client_record,
    create_project,
)

if TYPE_CHECKING:
    from flask.testing import FlaskClient


def _setup_project(client: FlaskClient) -> dict[str, str]:
    admin = bootstrap_admin(client)
    customer = create_client_record(client, admin_token=admin["access_token"])
    project = create_project(
        client,
        admin_token=admin["access_token"],
        client_id=str(customer["id"]),
    )
    return {
        "token": admin["access_token"],
        "project_id": str(project["id"]),
    }


def test_start_creates_running_entry(client: FlaskClient) -> None:
    ctx = _setup_project(client)

    response = client.post(
        "/api/v1/timer/start",
        headers=auth_headers(ctx["token"]),
        json={"project_id": ctx["project_id"], "description": "kickoff"},
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body["status"] == "draft"
    assert body["ended_at"] is None
    assert body["description"] == "kickoff"


def test_current_returns_running_state_and_elapsed(client: FlaskClient) -> None:
    ctx = _setup_project(client)
    client.post(
        "/api/v1/timer/start",
        headers=auth_headers(ctx["token"]),
        json={"project_id": ctx["project_id"]},
    )
    time.sleep(0.05)

    response = client.get("/api/v1/timer/current", headers=auth_headers(ctx["token"]))

    assert response.status_code == 200
    body = response.get_json()
    assert body["state"] == "running"
    assert body["elapsed_seconds"] >= 0


def test_start_when_already_running_returns_409(client: FlaskClient) -> None:
    ctx = _setup_project(client)
    client.post(
        "/api/v1/timer/start",
        headers=auth_headers(ctx["token"]),
        json={"project_id": ctx["project_id"]},
    )

    again = client.post(
        "/api/v1/timer/start",
        headers=auth_headers(ctx["token"]),
        json={"project_id": ctx["project_id"]},
    )

    assert again.status_code == 409


def test_pause_resume_stop_lifecycle(client: FlaskClient) -> None:
    ctx = _setup_project(client)
    headers = auth_headers(ctx["token"])
    client.post(
        "/api/v1/timer/start",
        headers=headers,
        json={"project_id": ctx["project_id"]},
    )
    time.sleep(1.1)

    paused = client.post("/api/v1/timer/pause", headers=headers)
    assert paused.status_code == 200

    current = client.get("/api/v1/timer/current", headers=headers).get_json()
    assert current["state"] == "paused"

    resumed = client.post("/api/v1/timer/resume", headers=headers)
    assert resumed.status_code == 200
    time.sleep(0.2)

    stopped = client.post("/api/v1/timer/stop", headers=headers)
    assert stopped.status_code == 200
    body = stopped.get_json()
    assert body["ended_at"] is not None
    # Sub-minute elapsed rounds up to one full 6-min unit (default).
    assert body["rounded_seconds"] == 360
    assert 1 <= body["duration_seconds"] < 360


def test_pause_without_running_returns_404(client: FlaskClient) -> None:
    ctx = _setup_project(client)

    response = client.post("/api/v1/timer/pause", headers=auth_headers(ctx["token"]))

    assert response.status_code == 404


def test_current_returns_null_when_no_timer(client: FlaskClient) -> None:
    ctx = _setup_project(client)

    response = client.get("/api/v1/timer/current", headers=auth_headers(ctx["token"]))

    assert response.status_code == 200
    assert response.get_json() is None
