from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING

from tests.integration._factories import (
    auth_headers,
    bootstrap_admin,
    create_client_record,
    create_project,
)

if TYPE_CHECKING:
    from flask.testing import FlaskClient


def _approved_entry(
    client: FlaskClient, *, admin_token: str, project_id: str, hours: int = 2
) -> str:
    now = datetime.now(UTC).replace(microsecond=0)
    entry = client.post(
        "/api/v1/entries",
        headers=auth_headers(admin_token),
        json={
            "project_id": project_id,
            "started_at": (now - timedelta(hours=hours + 1)).isoformat(),
            "ended_at": (now - timedelta(hours=1)).isoformat(),
        },
    ).get_json()
    client.post(f"/api/v1/entries/{entry['id']}/submit", headers=auth_headers(admin_token))
    client.post(
        "/api/v1/approvals/approve",
        headers=auth_headers(admin_token),
        json={"entry_ids": [entry["id"]]},
    )
    return str(entry["id"])


def test_outstanding_returns_counts(client: FlaskClient) -> None:
    admin = bootstrap_admin(client)
    customer = create_client_record(client, admin_token=admin["access_token"])
    project = create_project(
        client, admin_token=admin["access_token"], client_id=str(customer["id"])
    )
    _approved_entry(client, admin_token=admin["access_token"], project_id=str(project["id"]))

    response = client.get(
        "/api/v1/reports/outstanding", headers=auth_headers(admin["access_token"])
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["approved_uninvoiced_count"] == 1
    assert body["approved_uninvoiced_seconds"] > 0


def test_utilization_groups_by_user(client: FlaskClient) -> None:
    admin = bootstrap_admin(client)
    customer = create_client_record(client, admin_token=admin["access_token"])
    project = create_project(
        client, admin_token=admin["access_token"], client_id=str(customer["id"])
    )
    _approved_entry(client, admin_token=admin["access_token"], project_id=str(project["id"]))

    today = date.today()  # noqa: DTZ011
    response = client.get(
        "/api/v1/reports/utilization",
        query_string={
            "start": (today - timedelta(days=2)).isoformat(),
            "end": today.isoformat(),
        },
        headers=auth_headers(admin["access_token"]),
    )

    assert response.status_code == 200
    rows = response.get_json()["rows"]
    assert len(rows) == 1
    assert rows[0]["total_seconds"] > 0
    assert rows[0]["utilization"] == 1.0  # all billable
