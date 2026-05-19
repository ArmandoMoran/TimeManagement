from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Locator, Page


class LoginPage:
    """Page object for the sign-in screen."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def goto(self, base_url: str) -> None:
        self.page.goto(f"{base_url}/login")

    @property
    def email_field(self) -> Locator:
        return self.page.get_by_label("Email")

    @property
    def password_field(self) -> Locator:
        return self.page.get_by_label("Password")

    @property
    def submit_button(self) -> Locator:
        return self.page.get_by_role("button", name="Sign in")

    def sign_in(self, *, email: str, password: str) -> None:
        self.email_field.fill(email)
        self.password_field.fill(password)
        self.submit_button.click()
