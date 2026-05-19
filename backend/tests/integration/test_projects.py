from __future__ import annotations

from typing import TYPE_CHECKING

from tests.integration._factories import (
    auth_headers,
    bootstrap_admin,
    create_client_record,
    create_project,
    register_user,
)

if TYPE_CHECKING:
    from flask.testing import FlaskClient


def test_admin_can_create_project_under_client(client: FlaskClient) -> None:
    admin = bootstrap_admin(client)
    acme = create_client_record(client, admin_token=admin["access_token"])

    response = client.post(
        "/api/v1/projects",
        headers=auth_headers(admin["access_token"]),
        json={
            "client_id": acme["id"],
            "name": "Acme Site",
            "default_rate_cents": 12000,
        },
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body["name"] == "Acme Site"
    assert body["client_id"] == acme["id"]
    assert body["default_rate_cents"] == 12000
    assert body["rounding_minutes"] == 6


def test_project_cannot_be_created_with_unknown_client(client: FlaskClient) -> None:
    admin = bootstrap_admin(client)

    response = client.post(
        "/api/v1/projects",
        headers=auth_headers(admin["access_token"]),
        json={"client_id": "11111111-1111-1111-1111-111111111111", "name": "X"},
    )

    assert response.status_code == 422


def test_list_projects_can_filter_by_client(client: FlaskClient) -> None:
    admin = bootstrap_admin(client)
    acme = create_client_record(client, admin_token=admin["access_token"], name="Acme")
    other = create_client_record(client, admin_token=admin["access_token"], name="Other")
    create_project(client, admin_token=admin["access_token"], client_id=str(acme["id"]))
    create_project(
        client,
        admin_token=admin["access_token"],
        client_id=str(other["id"]),
        name="Other Site",
    )

    response = client.get(
        f"/api/v1/projects?client_id={acme['id']}",
        headers=auth_headers(admin["access_token"]),
    )

    assert response.status_code == 200
    projects = response.get_json()["projects"]
    assert len(projects) == 1
    assert projects[0]["client_id"] == acme["id"]


def test_admin_can_add_and_remove_member_with_rate_override(client: FlaskClient) -> None:
    admin = bootstrap_admin(client)
    acme = create_client_record(client, admin_token=admin["access_token"])
    project = create_project(client, admin_token=admin["access_token"], client_id=str(acme["id"]))
    emp = register_user(client, admin_token=admin["access_token"], email="emp@example.com")

    add = client.post(
        f"/api/v1/projects/{project['id']}/members",
        headers=auth_headers(admin["access_token"]),
        json={"user_id": emp["id"], "rate_override_cents": 18000},
    )
    assert add.status_code == 201
    assert add.get_json()["rate_override_cents"] == 18000

    members = client.get(
        f"/api/v1/projects/{project['id']}/members",
        headers=auth_headers(admin["access_token"]),
    )
    assert members.status_code == 200
    assert len(members.get_json()["members"]) == 1

    remove = client.delete(
        f"/api/v1/projects/{project['id']}/members/{emp['id']}",
        headers=auth_headers(admin["access_token"]),
    )
    assert remove.status_code == 200


def test_setting_member_twice_updates_rate(client: FlaskClient) -> None:
    admin = bootstrap_admin(client)
    acme = create_client_record(client, admin_token=admin["access_token"])
    project = create_project(client, admin_token=admin["access_token"], client_id=str(acme["id"]))
    emp = register_user(client, admin_token=admin["access_token"], email="emp@example.com")

    client.post(
        f"/api/v1/projects/{project['id']}/members",
        headers=auth_headers(admin["access_token"]),
        json={"user_id": emp["id"], "rate_override_cents": 10000},
    )
    update = client.post(
        f"/api/v1/projects/{project['id']}/members",
        headers=auth_headers(admin["access_token"]),
        json={"user_id": emp["id"], "rate_override_cents": 22000},
    )

    assert update.status_code == 201
    assert update.get_json()["rate_override_cents"] == 22000

    members = client.get(
        f"/api/v1/projects/{project['id']}/members",
        headers=auth_headers(admin["access_token"]),
    ).get_json()["members"]
    assert len(members) == 1


def test_employee_cannot_create_project(client: FlaskClient) -> None:
    admin = bootstrap_admin(client)
    acme = create_client_record(client, admin_token=admin["access_token"])
    register_user(client, admin_token=admin["access_token"], email="emp@example.com")
    from tests.integration._factories import login

    emp_token = login(client, email="emp@example.com", password="long-enough-pw")

    response = client.post(
        "/api/v1/projects",
        headers=auth_headers(emp_token),
        json={"client_id": acme["id"], "name": "X"},
    )

    assert response.status_code == 403
