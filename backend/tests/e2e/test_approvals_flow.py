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


def _setup_submitted_entries(flask_server: str, admin_account: dict[str, str]) -> str:
    """Returns the submitted entry id."""
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
        json={"client_id": customer["id"], "name": "Site"},
        timeout=10,
    ).json()
    now = datetime.now(UTC)
    entry = requests.post(
        f"{flask_server}/api/v1/entries",
        headers=headers,
        json={
            "project_id": project["id"],
            "started_at": (now - timedelta(hours=2)).isoformat(),
            "ended_at": (now - timedelta(hours=1)).isoformat(),
            "description": "kickoff meeting",
        },
        timeout=10,
    ).json()
    requests.post(
        f"{flask_server}/api/v1/entries/{entry['id']}/submit",
        headers=headers,
        timeout=10,
    ).raise_for_status()
    return str(entry["id"])


def test_manager_bulk_approves_pending_entries(
    page: Page,
    flask_server: str,
    admin_account: dict[str, str],
) -> None:
    entry_id = _setup_submitted_entries(flask_server, admin_account)

    LoginPage(page).goto(flask_server)
    LoginPage(page).sign_in(email=admin_account["email"], password=admin_account["password"])
    expect(page.get_by_role("heading", name="Today", exact=True)).to_be_visible()

    page.get_by_role("link", name="Approvals").click()
    expect(page.get_by_role("heading", name="Approvals")).to_be_visible()

    expect(page.get_by_role("cell", name="kickoff meeting")).to_be_visible()

    page.get_by_label(f"Select entry {entry_id}").check()
    page.get_by_role("button", name="Approve selected").click()

    # Pending list empties after approval.
    expect(page.get_by_text("Nothing waiting for approval")).to_be_visible()


def test_manager_rejects_with_reason(
    page: Page,
    flask_server: str,
    admin_account: dict[str, str],
) -> None:
    entry_id = _setup_submitted_entries(flask_server, admin_account)

    LoginPage(page).goto(flask_server)
    LoginPage(page).sign_in(email=admin_account["email"], password=admin_account["password"])
    page.get_by_role("link", name="Approvals").click()

    page.get_by_label(f"Select entry {entry_id}").check()
    page.get_by_label("Rejection reason").fill("needs description")
    page.get_by_role("button", name="Reject selected").click()

    expect(page.get_by_text("Nothing waiting for approval")).to_be_visible()
