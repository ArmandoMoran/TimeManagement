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


def _setup(client: FlaskClient) -> dict[str, str]:
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
        "user_id": admin["user_id"],
    }


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def test_create_manual_entry(client: FlaskClient) -> None:
    ctx = _setup(client)
    start = datetime.now(UTC) - timedelta(hours=2)
    end = start + timedelta(minutes=45)

    response = client.post(
        "/api/v1/entries",
        headers=auth_headers(ctx["token"]),
        json={
            "project_id": ctx["project_id"],
            "started_at": _iso(start),
            "ended_at": _iso(end),
            "description": "wireframes",
        },
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body["duration_seconds"] == 45 * 60
    assert body["status"] == "draft"


def test_manual_entry_with_end_before_start_returns_422(client: FlaskClient) -> None:
    ctx = _setup(client)
    start = datetime.now(UTC)
    end = start - timedelta(minutes=5)

    response = client.post(
        "/api/v1/entries",
        headers=auth_headers(ctx["token"]),
        json={
            "project_id": ctx["project_id"],
            "started_at": _iso(start),
            "ended_at": _iso(end),
        },
    )

    assert response.status_code == 422


def test_employee_sees_only_own_entries(client: FlaskClient) -> None:
    ctx = _setup(client)
    other = register_user(client, admin_token=ctx["token"], email="other@example.com")
    other_token = login(client, email="other@example.com", password="long-enough-pw")
    now = datetime.now(UTC)

    # Admin's own entry.
    client.post(
        "/api/v1/entries",
        headers=auth_headers(ctx["token"]),
        json={
            "project_id": ctx["project_id"],
            "started_at": _iso(now - timedelta(hours=1)),
            "ended_at": _iso(now),
        },
    )
    # Other user's entry.
    client.post(
        "/api/v1/entries",
        headers=auth_headers(other_token),
        json={
            "project_id": ctx["project_id"],
            "started_at": _iso(now - timedelta(hours=1)),
            "ended_at": _iso(now),
        },
    )

    list_for_other = client.get("/api/v1/entries", headers=auth_headers(other_token)).get_json()
    assert len(list_for_other["entries"]) == 1
    assert list_for_other["entries"][0]["user_id"] == other["id"]


def test_submit_changes_status_and_blocks_resubmit(client: FlaskClient) -> None:
    ctx = _setup(client)
    now = datetime.now(UTC)
    entry = client.post(
        "/api/v1/entries",
        headers=auth_headers(ctx["token"]),
        json={
            "project_id": ctx["project_id"],
            "started_at": _iso(now - timedelta(hours=1)),
            "ended_at": _iso(now),
        },
    ).get_json()

    submit = client.post(
        f"/api/v1/entries/{entry['id']}/submit",
        headers=auth_headers(ctx["token"]),
    )
    assert submit.status_code == 200
    assert submit.get_json()["status"] == "submitted"

    again = client.post(
        f"/api/v1/entries/{entry['id']}/submit",
        headers=auth_headers(ctx["token"]),
    )
    assert again.status_code == 409


def test_bulk_submit(client: FlaskClient) -> None:
    ctx = _setup(client)
    now = datetime.now(UTC)
    ids = []
    for hours in (3, 2, 1):
        entry = client.post(
            "/api/v1/entries",
            headers=auth_headers(ctx["token"]),
            json={
                "project_id": ctx["project_id"],
                "started_at": _iso(now - timedelta(hours=hours)),
                "ended_at": _iso(now - timedelta(hours=hours - 1)),
            },
        ).get_json()
        ids.append(entry["id"])

    response = client.post(
        "/api/v1/entries/bulk-submit",
        headers=auth_headers(ctx["token"]),
        json={"entry_ids": ids},
    )

    assert response.status_code == 200
    entries = response.get_json()["entries"]
    assert all(e["status"] == "submitted" for e in entries)


def test_employee_cannot_edit_others_entry(client: FlaskClient) -> None:
    ctx = _setup(client)
    other = register_user(client, admin_token=ctx["token"], email="o@example.com")
    other_token = login(client, email="o@example.com", password="long-enough-pw")
    now = datetime.now(UTC)
    entry = client.post(
        "/api/v1/entries",
        headers=auth_headers(other_token),
        json={
            "project_id": ctx["project_id"],
            "started_at": _iso(now - timedelta(hours=1)),
            "ended_at": _iso(now),
        },
    ).get_json()

    _ = other  # unused
    # Create a third user, try to edit other's entry.
    register_user(client, admin_token=ctx["token"], email="thief@example.com")
    thief_token = login(client, email="thief@example.com", password="long-enough-pw")
    response = client.patch(
        f"/api/v1/entries/{entry['id']}",
        headers=auth_headers(thief_token),
        json={"description": "stolen"},
    )

    assert response.status_code == 403


def test_delete_own_entry(client: FlaskClient) -> None:
    ctx = _setup(client)
    now = datetime.now(UTC)
    entry = client.post(
        "/api/v1/entries",
        headers=auth_headers(ctx["token"]),
        json={
            "project_id": ctx["project_id"],
            "started_at": _iso(now - timedelta(hours=1)),
            "ended_at": _iso(now),
        },
    ).get_json()

    response = client.delete(f"/api/v1/entries/{entry['id']}", headers=auth_headers(ctx["token"]))

    assert response.status_code == 200
