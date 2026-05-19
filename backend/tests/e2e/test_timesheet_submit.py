from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest
import requests
from playwright.sync_api import expect

from tests.e2e.pages.login_page import LoginPage

if TYPE_CHECKING:
    from playwright.sync_api import Page

pytestmark = pytest.mark.e2e


def test_user_submits_week_changes_status_to_submitted(
    page: Page,
    flask_server: str,
    admin_account: dict[str, str],
) -> None:
    headers = {"Authorization": f"Bearer {admin_account['access_token']}"}
    customer = requests.post(
        f"{flask_server}/api/v1/clients",
        headers=headers,
        json={"name": "Acme"},
        timeout=10,
    ).json()
    project = requests.post(
        f"{flask_server}/api/v1/projects",
        headers=headers,
        json={
            "client_id": customer["id"],
            "name": "Refresh",
            "default_rate_cents": 18000,
        },
        timeout=10,
    ).json()

    # Seed a draft entry in this week.
    now = datetime.now(UTC).replace(microsecond=0)
    requests.post(
        f"{flask_server}/api/v1/entries",
        headers=headers,
        json={
            "project_id": project["id"],
            "started_at": (now - timedelta(hours=2)).isoformat(),
            "ended_at": (now - timedelta(hours=1)).isoformat(),
            "description": "discovery",
        },
        timeout=10,
    ).raise_for_status()

    LoginPage(page).goto(flask_server)
    LoginPage(page).sign_in(email=admin_account["email"], password=admin_account["password"])
    expect(page.get_by_role("heading", name="Today", exact=True)).to_be_visible()

    page.get_by_role("link", name="Timesheet").click()
    expect(page.get_by_role("heading", name="Timesheet")).to_be_visible()

    expect(page.get_by_text("discovery").first).to_be_visible()

    page.get_by_role("button", name="Submit week").click()

    expect(page.get_by_text("submitted").first).to_be_visible()
