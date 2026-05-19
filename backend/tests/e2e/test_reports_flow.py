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


def test_reports_load_with_outstanding_totals(
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
        json={"client_id": customer["id"], "name": "Site", "default_rate_cents": 15000},
        timeout=10,
    ).json()
    now = datetime.now(UTC).replace(microsecond=0)
    entry = requests.post(
        f"{flask_server}/api/v1/entries",
        headers=headers,
        json={
            "project_id": project["id"],
            "started_at": (now - timedelta(hours=3)).isoformat(),
            "ended_at": (now - timedelta(hours=1)).isoformat(),
        },
        timeout=10,
    ).json()
    requests.post(
        f"{flask_server}/api/v1/entries/{entry['id']}/submit",
        headers=headers,
        timeout=10,
    ).raise_for_status()
    requests.post(
        f"{flask_server}/api/v1/approvals/approve",
        headers=headers,
        json={"entry_ids": [entry["id"]]},
        timeout=10,
    ).raise_for_status()

    LoginPage(page).goto(flask_server)
    LoginPage(page).sign_in(email=admin_account["email"], password=admin_account["password"])
    page.get_by_role("link", name="Reports").click()
    expect(page.get_by_role("heading", name="Reports")).to_be_visible()

    # Outstanding section shows the unbilled approved time (~2h).
    outstanding_region = page.get_by_role("region", name="Outstanding time")
    expect(outstanding_region).to_be_visible()
    expect(outstanding_region).to_contain_text("1 entries")

    # Utilization section renders.
    expect(page.get_by_role("region", name="Utilization")).to_be_visible()
