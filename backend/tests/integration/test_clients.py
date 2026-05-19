from __future__ import annotations

from typing import TYPE_CHECKING

from tests.integration._factories import (
    auth_headers,
    bootstrap_admin,
    login,
    register_user,
)

if TYPE_CHECKING:
    from flask.testing import FlaskClient


def test_admin_can_create_client(client: FlaskClient) -> None:
    admin = bootstrap_admin(client)

    response = client.post(
        "/api/v1/clients",
        headers=auth_headers(admin["access_token"]),
        json={"name": "Acme", "email": "billing@acme.example.com", "currency": "USD"},
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body["name"] == "Acme"
    assert body["currency"] == "USD"


def test_employee_cannot_create_client(client: FlaskClient) -> None:
    admin = bootstrap_admin(client)
    register_user(client, admin_token=admin["access_token"], email="emp@example.com")
    emp_token = login(client, email="emp@example.com", password="long-enough-pw")

    response = client.post(
        "/api/v1/clients",
        headers=auth_headers(emp_token),
        json={"name": "Acme"},
    )

    assert response.status_code == 403


def test_employee_can_list_clients(client: FlaskClient) -> None:
    admin = bootstrap_admin(client)
    client.post(
        "/api/v1/clients",
        headers=auth_headers(admin["access_token"]),
        json={"name": "Acme"},
    )
    register_user(client, admin_token=admin["access_token"], email="emp@example.com")
    emp_token = login(client, email="emp@example.com", password="long-enough-pw")

    response = client.get("/api/v1/clients", headers=auth_headers(emp_token))

    assert response.status_code == 200
    assert len(response.get_json()["clients"]) == 1


def test_admin_can_update_client(client: FlaskClient) -> None:
    admin = bootstrap_admin(client)
    created = client.post(
        "/api/v1/clients",
        headers=auth_headers(admin["access_token"]),
        json={"name": "Acme"},
    ).get_json()

    response = client.patch(
        f"/api/v1/clients/{created['id']}",
        headers=auth_headers(admin["access_token"]),
        json={"notes": "annual contract"},
    )

    assert response.status_code == 200
    assert response.get_json()["notes"] == "annual contract"


def test_admin_can_delete_client(client: FlaskClient) -> None:
    admin = bootstrap_admin(client)
    created = client.post(
        "/api/v1/clients",
        headers=auth_headers(admin["access_token"]),
        json={"name": "Acme"},
    ).get_json()

    response = client.delete(
        f"/api/v1/clients/{created['id']}",
        headers=auth_headers(admin["access_token"]),
    )

    assert response.status_code == 200
    after = client.get(
        f"/api/v1/clients/{created['id']}",
        headers=auth_headers(admin["access_token"]),
    )
    assert after.status_code == 404


def test_invalid_client_currency_rejected(client: FlaskClient) -> None:
    admin = bootstrap_admin(client)

    response = client.post(
        "/api/v1/clients",
        headers=auth_headers(admin["access_token"]),
        json={"name": "Acme", "currency": "USDD"},
    )

    assert response.status_code == 422


def test_unauthenticated_request_returns_401(client: FlaskClient) -> None:
    response = client.get("/api/v1/clients")
    assert response.status_code == 401
