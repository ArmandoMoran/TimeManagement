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


def _setup_approved_entry(
    client: FlaskClient,
    *,
    admin_token: str,
    project_id: str,
    duration_hours: float = 2.0,
) -> str:
    now = datetime.now(UTC).replace(microsecond=0)
    entry = client.post(
        "/api/v1/entries",
        headers=auth_headers(admin_token),
        json={
            "project_id": project_id,
            "started_at": (now - timedelta(hours=duration_hours + 1)).isoformat(),
            "ended_at": (now - timedelta(hours=1)).isoformat(),
            "description": "dev work",
        },
    ).get_json()
    client.post(f"/api/v1/entries/{entry['id']}/submit", headers=auth_headers(admin_token))
    client.post(
        "/api/v1/approvals/approve",
        headers=auth_headers(admin_token),
        json={"entry_ids": [entry["id"]]},
    )
    return str(entry["id"])


def test_invoice_preview_groups_by_project_and_user(client: FlaskClient) -> None:
    admin = bootstrap_admin(client)
    customer = create_client_record(client, admin_token=admin["access_token"])
    project = create_project(
        client,
        admin_token=admin["access_token"],
        client_id=str(customer["id"]),
        default_rate_cents=15000,
    )
    _setup_approved_entry(
        client,
        admin_token=admin["access_token"],
        project_id=str(project["id"]),
        duration_hours=2.0,
    )

    today = date.today()  # noqa: DTZ011
    response = client.post(
        "/api/v1/invoices/preview",
        headers=auth_headers(admin["access_token"]),
        json={
            "client_id": str(customer["id"]),
            "start": (today - timedelta(days=7)).isoformat(),
            "end": today.isoformat(),
        },
    )

    assert response.status_code == 200
    body = response.get_json()
    assert len(body["lines"]) == 1
    assert body["subtotal_cents"] > 0


def test_create_invoice_marks_entries_as_invoiced(client: FlaskClient) -> None:
    admin = bootstrap_admin(client)
    customer = create_client_record(client, admin_token=admin["access_token"])
    project = create_project(
        client,
        admin_token=admin["access_token"],
        client_id=str(customer["id"]),
        default_rate_cents=20000,
    )
    entry_id = _setup_approved_entry(
        client, admin_token=admin["access_token"], project_id=str(project["id"])
    )

    today = date.today()  # noqa: DTZ011
    response = client.post(
        "/api/v1/invoices",
        headers=auth_headers(admin["access_token"]),
        json={
            "client_id": str(customer["id"]),
            "start": (today - timedelta(days=7)).isoformat(),
            "end": today.isoformat(),
        },
    )

    assert response.status_code == 201
    invoice = response.get_json()
    assert invoice["invoice_number"].startswith("INV-")
    assert invoice["status"] == "draft"
    assert invoice["total_cents"] > 0

    # Entry is now invoiced.
    entries = client.get(
        "/api/v1/entries?status=invoiced",
        headers=auth_headers(admin["access_token"]),
    ).get_json()["entries"]
    assert any(e["id"] == entry_id for e in entries)


def test_create_invoice_with_no_eligible_entries_returns_422(
    client: FlaskClient,
) -> None:
    admin = bootstrap_admin(client)
    customer = create_client_record(client, admin_token=admin["access_token"])

    today = date.today()  # noqa: DTZ011
    response = client.post(
        "/api/v1/invoices",
        headers=auth_headers(admin["access_token"]),
        json={
            "client_id": str(customer["id"]),
            "start": (today - timedelta(days=7)).isoformat(),
            "end": today.isoformat(),
        },
    )

    assert response.status_code == 422


def test_invoice_number_sequence_increments(client: FlaskClient) -> None:
    admin = bootstrap_admin(client)
    customer = create_client_record(client, admin_token=admin["access_token"])
    project = create_project(
        client,
        admin_token=admin["access_token"],
        client_id=str(customer["id"]),
        default_rate_cents=10000,
    )

    today = date.today()  # noqa: DTZ011
    numbers = []
    for _ in range(2):
        _setup_approved_entry(
            client, admin_token=admin["access_token"], project_id=str(project["id"])
        )
        response = client.post(
            "/api/v1/invoices",
            headers=auth_headers(admin["access_token"]),
            json={
                "client_id": str(customer["id"]),
                "start": (today - timedelta(days=7)).isoformat(),
                "end": today.isoformat(),
            },
        )
        assert response.status_code == 201
        numbers.append(response.get_json()["invoice_number"])

    assert numbers[0] != numbers[1]
    n1 = int(numbers[0].rsplit("-", 1)[1])
    n2 = int(numbers[1].rsplit("-", 1)[1])
    assert n2 == n1 + 1


def test_mark_sent_then_paid(client: FlaskClient) -> None:
    admin = bootstrap_admin(client)
    customer = create_client_record(client, admin_token=admin["access_token"])
    project = create_project(
        client,
        admin_token=admin["access_token"],
        client_id=str(customer["id"]),
        default_rate_cents=10000,
    )
    _setup_approved_entry(client, admin_token=admin["access_token"], project_id=str(project["id"]))
    today = date.today()  # noqa: DTZ011
    invoice = client.post(
        "/api/v1/invoices",
        headers=auth_headers(admin["access_token"]),
        json={
            "client_id": str(customer["id"]),
            "start": (today - timedelta(days=7)).isoformat(),
            "end": today.isoformat(),
        },
    ).get_json()

    sent = client.post(
        f"/api/v1/invoices/{invoice['id']}/send",
        headers=auth_headers(admin["access_token"]),
    )
    assert sent.status_code == 200
    assert sent.get_json()["status"] == "sent"

    paid = client.post(
        f"/api/v1/invoices/{invoice['id']}/mark-paid",
        headers=auth_headers(admin["access_token"]),
    )
    assert paid.status_code == 200
    assert paid.get_json()["status"] == "paid"


def test_void_returns_entries_to_approved(client: FlaskClient) -> None:
    admin = bootstrap_admin(client)
    customer = create_client_record(client, admin_token=admin["access_token"])
    project = create_project(
        client,
        admin_token=admin["access_token"],
        client_id=str(customer["id"]),
        default_rate_cents=10000,
    )
    _setup_approved_entry(client, admin_token=admin["access_token"], project_id=str(project["id"]))
    today = date.today()  # noqa: DTZ011
    invoice = client.post(
        "/api/v1/invoices",
        headers=auth_headers(admin["access_token"]),
        json={
            "client_id": str(customer["id"]),
            "start": (today - timedelta(days=7)).isoformat(),
            "end": today.isoformat(),
        },
    ).get_json()

    response = client.post(
        f"/api/v1/invoices/{invoice['id']}/void",
        headers=auth_headers(admin["access_token"]),
    )

    assert response.status_code == 200
    assert response.get_json()["status"] == "void"


def test_pdf_endpoint_returns_pdf(client: FlaskClient) -> None:
    admin = bootstrap_admin(client)
    customer = create_client_record(client, admin_token=admin["access_token"])
    project = create_project(
        client,
        admin_token=admin["access_token"],
        client_id=str(customer["id"]),
        default_rate_cents=10000,
    )
    _setup_approved_entry(client, admin_token=admin["access_token"], project_id=str(project["id"]))
    today = date.today()  # noqa: DTZ011
    invoice = client.post(
        "/api/v1/invoices",
        headers=auth_headers(admin["access_token"]),
        json={
            "client_id": str(customer["id"]),
            "start": (today - timedelta(days=7)).isoformat(),
            "end": today.isoformat(),
        },
    ).get_json()

    response = client.get(
        f"/api/v1/invoices/{invoice['id']}/pdf",
        headers=auth_headers(admin["access_token"]),
    )

    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF")
