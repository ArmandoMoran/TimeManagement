from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from tests.integration._factories import (
    auth_headers,
    bootstrap_admin,
    create_client_record,
    create_project,
    login,
    register_user,
)

if TYPE_CHECKING:
    from flask.testing import FlaskClient


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _seed_submitted_entry(client: FlaskClient, *, owner_token: str, project_id: str) -> str:
    now = datetime.now(UTC)
    entry = client.post(
        "/api/v1/entries",
        headers=auth_headers(owner_token),
        json={
            "project_id": project_id,
            "started_at": _iso(now - timedelta(hours=1)),
            "ended_at": _iso(now),
            "description": "discovery",
        },
    ).get_json()
    submit = client.post(
        f"/api/v1/entries/{entry['id']}/submit",
        headers=auth_headers(owner_token),
    )
    assert submit.status_code == 200
    return str(entry["id"])


def test_employee_cannot_list_approvals(client: FlaskClient) -> None:
    admin = bootstrap_admin(client)
    register_user(client, admin_token=admin["access_token"], email="emp@example.com")
    emp_token = login(client, email="emp@example.com", password="long-enough-pw")

    response = client.get("/api/v1/approvals", headers=auth_headers(emp_token))

    assert response.status_code == 403


def test_admin_approves_submitted_entry(client: FlaskClient) -> None:
    admin = bootstrap_admin(client)
    customer = create_client_record(client, admin_token=admin["access_token"])
    project = create_project(
        client, admin_token=admin["access_token"], client_id=str(customer["id"])
    )
    entry_id = _seed_submitted_entry(
        client, owner_token=admin["access_token"], project_id=str(project["id"])
    )

    pending = client.get("/api/v1/approvals", headers=auth_headers(admin["access_token"]))
    assert pending.status_code == 200
    assert len(pending.get_json()["entries"]) == 1

    approve = client.post(
        "/api/v1/approvals/approve",
        headers=auth_headers(admin["access_token"]),
        json={"entry_ids": [entry_id]},
    )
    assert approve.status_code == 200
    [approved] = approve.get_json()["entries"]
    assert approved["status"] == "approved"
    assert approved["approved_by"] == admin["user_id"]


def test_admin_rejects_submitted_entry_with_reason(client: FlaskClient) -> None:
    admin = bootstrap_admin(client)
    customer = create_client_record(client, admin_token=admin["access_token"])
    project = create_project(
        client, admin_token=admin["access_token"], client_id=str(customer["id"])
    )
    entry_id = _seed_submitted_entry(
        client, owner_token=admin["access_token"], project_id=str(project["id"])
    )

    response = client.post(
        "/api/v1/approvals/reject",
        headers=auth_headers(admin["access_token"]),
        json={"entry_ids": [entry_id], "reason": "needs more detail"},
    )

    assert response.status_code == 200
    [rejected] = response.get_json()["entries"]
    assert rejected["status"] == "draft"
    assert "needs more detail" in rejected["notes"]


def test_cannot_approve_draft_entry(client: FlaskClient) -> None:
    admin = bootstrap_admin(client)
    customer = create_client_record(client, admin_token=admin["access_token"])
    project = create_project(
        client, admin_token=admin["access_token"], client_id=str(customer["id"])
    )
    # Create a draft (not submitted) entry.
    now = datetime.now(UTC)
    entry = client.post(
        "/api/v1/entries",
        headers=auth_headers(admin["access_token"]),
        json={
            "project_id": str(project["id"]),
            "started_at": _iso(now - timedelta(hours=1)),
            "ended_at": _iso(now),
        },
    ).get_json()

    response = client.post(
        "/api/v1/approvals/approve",
        headers=auth_headers(admin["access_token"]),
        json={"entry_ids": [entry["id"]]},
    )

    assert response.status_code == 409
