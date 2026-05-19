from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import requests
from playwright.sync_api import expect

from tests.e2e.pages.login_page import LoginPage

if TYPE_CHECKING:
    from playwright.sync_api import Page

pytestmark = pytest.mark.e2e


def test_admin_creates_client_then_project_with_member_rate_override(
    page: Page,
    flask_server: str,
    admin_account: dict[str, str],
) -> None:
    # Seed an employee whose user_id we'll add as a project member.
    headers = {"Authorization": f"Bearer {admin_account['access_token']}"}
    seed = requests.post(
        f"{flask_server}/api/v1/auth/register",
        headers=headers,
        json={
            "email": "dev@example.com",
            "password": "long-enough-pw",
            "name": "Dev",
            "role": "employee",
        },
        timeout=10,
    )
    seed.raise_for_status()
    employee_id = seed.json()["id"]

    # Log in as admin.
    LoginPage(page).goto(flask_server)
    LoginPage(page).sign_in(email=admin_account["email"], password=admin_account["password"])
    expect(page.get_by_role("heading", name="Today", exact=True)).to_be_visible()

    # Create a client.
    page.get_by_role("link", name="Clients").click()
    page.get_by_label("Name", exact=True).fill("Acme")
    page.get_by_label("Email").fill("billing@acme.example.com")
    page.get_by_role("button", name="Create client").click()
    expect(page.get_by_role("cell", name="Acme", exact=True)).to_be_visible()

    # Create a project under that client.
    page.get_by_role("link", name="Projects").click()
    page.get_by_label("Client").select_option(label="Acme")
    page.get_by_label("Name", exact=True).fill("Acme Site Refresh")
    page.get_by_label("Rate ($/hr)").fill("180")
    page.get_by_role("button", name="Create project").click()
    expect(page.get_by_role("cell", name="Acme Site Refresh")).to_be_visible()

    # Open member panel and add the employee with an override.
    page.get_by_role("button", name="Manage").click()
    panel = page.get_by_role("region", name="Project members")
    expect(panel).to_be_visible()

    page.get_by_label("User ID").fill(employee_id)
    page.get_by_label("Rate override ($/hr)").fill("220")
    page.get_by_role("button", name="Add member").click()

    expect(page.get_by_text("$220.00/hr override")).to_be_visible()
