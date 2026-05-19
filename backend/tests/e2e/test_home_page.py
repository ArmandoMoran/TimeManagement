from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from playwright.sync_api import expect

if TYPE_CHECKING:
    from playwright.sync_api import Page

pytestmark = pytest.mark.e2e


def test_home_page_renders_timetrack_brand(page: Page, flask_server: str) -> None:
    page.goto(flask_server)

    expect(page.get_by_role("banner")).to_contain_text("TimeTrack")
