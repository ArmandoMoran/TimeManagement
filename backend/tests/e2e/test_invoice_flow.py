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


def _setup(flask_server: str, admin_account: dict[str, str]) -> None:
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
        json={"client_id": customer["id"], "name": "Site", "default_rate_cents": 18000},
        timeout=10,
    ).json()
    now = datetime.now(UTC).replace(microsecond=0)
    entry = requests.post(
        f"{flask_server}/api/v1/entries",
        headers=headers,
        json={
            "project_id": project["id"],
            "started_at": (now - timedelta(hours=4)).isoformat(),
            "ended_at": (now - timedelta(hours=2)).isoformat(),
            "description": "discovery sprint",
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


def test_admin_previews_and_creates_invoice(
    page: Page,
    flask_server: str,
    admin_account: dict[str, str],
) -> None:
    _setup(flask_server, admin_account)

    LoginPage(page).goto(flask_server)
    LoginPage(page).sign_in(email=admin_account["email"], password=admin_account["password"])

    page.get_by_role("link", name="Invoices").click()
    expect(page.get_by_role("heading", name="Invoices")).to_be_visible()

    form = page.get_by_role("form", name="New invoice")
    form.get_by_label("Client").select_option(label="Acme")
    form.get_by_role("button", name="Preview").click()

    expect(page.get_by_role("region", name="Invoice preview")).to_be_visible()
    page.get_by_role("button", name="Create invoice").click()

    # Created invoice appears in the bottom list with an INV-… number.
    expect(page.get_by_role("cell").filter(has_text="INV-").first).to_be_visible()
    expect(page.get_by_role("link", name="PDF")).to_be_visible()
