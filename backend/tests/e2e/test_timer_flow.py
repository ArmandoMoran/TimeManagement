from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest
import requests
from playwright.sync_api import expect

from tests.e2e.pages.login_page import LoginPage
from tests.e2e.pages.today_page import TodayPage

if TYPE_CHECKING:
    from playwright.sync_api import Page

pytestmark = pytest.mark.e2e


def _seed_admin_with_project(flask_server: str, admin_account: dict[str, str]) -> dict[str, str]:
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
            "name": "Acme Site Refresh",
            "default_rate_cents": 18000,
            "rounding_minutes": 6,
        },
        timeout=10,
    ).json()
    return {"client_id": customer["id"], "project_id": project["id"]}


def test_timer_start_pause_resume_stop_appears_in_today(
    page: Page,
    flask_server: str,
    admin_account: dict[str, str],
) -> None:
    _seed_admin_with_project(flask_server, admin_account)

    LoginPage(page).goto(flask_server)
    LoginPage(page).sign_in(email=admin_account["email"], password=admin_account["password"])

    today = TodayPage(page)
    expect(today.heading).to_be_visible()
    today.start_timer(project_name="Acme Site Refresh", description="initial discovery")
    expect(today.timer_bar).to_be_visible()

    today.pause()
    expect(today.timer_bar.get_by_role("button", name="Resume")).to_be_visible()

    today.resume()
    expect(today.timer_bar.get_by_role("button", name="Pause")).to_be_visible()

    today.stop()
    expect(today.timer_bar).not_to_be_visible()

    # Entry appears in today's list.
    expect(page.get_by_role("cell", name="initial discovery")).to_be_visible()
    expect(page.get_by_role("cell", name="draft")).to_be_visible()


def test_manual_entry_creation(
    page: Page,
    flask_server: str,
    admin_account: dict[str, str],
) -> None:
    _seed_admin_with_project(flask_server, admin_account)

    LoginPage(page).goto(flask_server)
    LoginPage(page).sign_in(email=admin_account["email"], password=admin_account["password"])

    today_page = TodayPage(page)
    expect(today_page.heading).to_be_visible()

    now = datetime.now(UTC).replace(microsecond=0)
    started = (now - timedelta(hours=2)).astimezone().replace(tzinfo=None)
    ended = (now - timedelta(hours=1)).astimezone().replace(tzinfo=None)

    form = page.get_by_role("form", name="Add manual entry")
    form.get_by_label("Project").select_option(label="Acme Site Refresh")
    form.get_by_label("Start").fill(started.strftime("%Y-%m-%dT%H:%M"))
    form.get_by_label("End").fill(ended.strftime("%Y-%m-%dT%H:%M"))
    form.get_by_label("Description").fill("retro write-up")
    form.get_by_role("button", name="Add entry").click()

    expect(page.get_by_role("cell", name="retro write-up")).to_be_visible()
    expect(page.get_by_role("cell", name="1h")).to_be_visible()
