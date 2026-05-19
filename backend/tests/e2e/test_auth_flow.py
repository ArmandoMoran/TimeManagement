from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from playwright.sync_api import expect

from tests.e2e.pages.login_page import LoginPage

if TYPE_CHECKING:
    from playwright.sync_api import Page

pytestmark = pytest.mark.e2e


def test_login_lands_on_today_and_logout_blocks_protected_routes(
    page: Page,
    flask_server: str,
    admin_account: dict[str, str],
) -> None:
    login = LoginPage(page)
    login.goto(flask_server)
    login.sign_in(email=admin_account["email"], password=admin_account["password"])

    # Lands on the Today view; nav shows the user.
    expect(page.get_by_role("heading", name="Today", exact=True)).to_be_visible()
    expect(page.get_by_role("banner")).to_contain_text(admin_account["name"])

    # Log out.
    page.get_by_role("button", name="Log out").click()
    expect(page.get_by_role("heading", name="Sign in to TimeTrack")).to_be_visible()

    # Direct navigation to a protected route is blocked.
    page.goto(f"{flask_server}/")
    expect(page.get_by_role("heading", name="Sign in to TimeTrack")).to_be_visible()


def test_login_with_invalid_credentials_shows_error(
    page: Page,
    flask_server: str,
    admin_account: dict[str, str],  # ensures user exists
) -> None:
    _ = admin_account
    login = LoginPage(page)
    login.goto(flask_server)
    login.sign_in(email="admin@example.com", password="wrong-password-x")

    expect(page.get_by_role("alert")).to_contain_text("Invalid email or password")
