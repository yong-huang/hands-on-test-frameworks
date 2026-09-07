"""SlowPage：慢加载演示页的页面对象。"""
from playwright.sync_api import Page, expect


class SlowPage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.race_btn = page.get_by_role("button", name="点我触发竞态")
        self.late_btn = page.get_by_role("button", name="加载延迟列表（2 秒后渲染）")
        self.race_box = page.locator("#race-box")
        self.late_items = page.locator("#late-list .box")

    def open(self) -> "SlowPage":
        self.page.goto("/slow.html")
        return self

    def trigger_race(self) -> None:
        self.race_btn.click()

    def expect_race_done(self) -> None:
        expect(self.race_box).to_have_text("竞态完成：状态已更新 ✅", timeout=15_000)

    def load_late_list(self) -> None:
        self.late_btn.click()

    def expect_late_items(self, count: int = 3) -> None:
        expect(self.late_items).to_have_count(count, timeout=15_000)
