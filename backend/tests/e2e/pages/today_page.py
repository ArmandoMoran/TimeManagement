from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Locator, Page


class TodayPage:
    def __init__(self, page: Page) -> None:
        self.page = page

    @property
    def heading(self) -> Locator:
        return self.page.get_by_role("heading", name="Today", exact=True)

    @property
    def timer_bar(self) -> Locator:
        return self.page.get_by_role("status", name="Active timer")

    def start_timer(self, *, project_name: str, description: str = "") -> None:
        form = self.page.get_by_role("form", name="Start timer")
        form.get_by_label("Project").select_option(label=project_name)
        if description:
            form.get_by_label("What are you working on?").fill(description)
        form.get_by_role("button", name="Start timer").click()

    def pause(self) -> None:
        self.timer_bar.get_by_role("button", name="Pause").click()

    def resume(self) -> None:
        self.timer_bar.get_by_role("button", name="Resume").click()

    def stop(self) -> None:
        self.timer_bar.get_by_role("button", name="Stop").click()
