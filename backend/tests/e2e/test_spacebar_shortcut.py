from __future__ import annotations

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
    requests.post(
        f"{flask_server}/api/v1/projects",
        headers=headers,
        json={"client_id": customer["id"], "name": "Site"},
        timeout=10,
    ).raise_for_status()


def test_spacebar_starts_and_stops_timer(
    page: Page,
    flask_server: str,
    admin_account: dict[str, str],
) -> None:
    _setup(flask_server, admin_account)

    LoginPage(page).goto(flask_server)
    LoginPage(page).sign_in(email=admin_account["email"], password=admin_account["password"])
    expect(page.get_by_role("heading", name="Today", exact=True)).to_be_visible()

    # Wait for projects to load so the shortcut has a default project.
    expect(
        page.get_by_role("form", name="Start timer").get_by_role("option", name="Site")
    ).to_be_attached()

    # Press space outside an input → starts a timer using the first project.
    page.locator("body").press("Space")
    expect(page.get_by_role("status", name="Active timer")).to_be_visible()

    # Press space again → stops the timer.
    page.locator("body").press("Space")
    expect(page.get_by_role("status", name="Active timer")).not_to_be_visible()


def test_spacebar_is_ignored_in_text_input(
    page: Page,
    flask_server: str,
    admin_account: dict[str, str],
) -> None:
    _setup(flask_server, admin_account)

    LoginPage(page).goto(flask_server)
    LoginPage(page).sign_in(email=admin_account["email"], password=admin_account["password"])

    form = page.get_by_role("form", name="Start timer")
    description = form.get_by_label("What are you working on?")
    description.focus()
    description.press("Space")

    # No timer should have started — value should just contain a space.
    expect(page.get_by_role("status", name="Active timer")).not_to_be_visible()
    expect(description).to_have_value(" ")
