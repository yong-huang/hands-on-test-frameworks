"""IndexPage：SUT 首页的页面对象——选择器只允许出现在这里。"""
from playwright.sync_api import Page, expect


class IndexPage:
    """业务语义的方法封装：用例读的是"做什么"，不是"怎么点"。"""

    def __init__(self, page: Page) -> None:
        self.page = page
        # 所有选择器收口在构造器里——UI 改版只改这一个文件
        self.customer_input = page.get_by_placeholder("客户名")
        self.item_input = page.get_by_placeholder("商品")
        self.price_input = page.get_by_placeholder("单价")
        self.submit_btn = page.get_by_role("button", name="创建订单")
        self.order_rows = page.locator("#orders tr")

    def open(self) -> "IndexPage":
        self.page.goto("/")
        return self

    def place_order(self, customer: str, item: str = "标准商品", price: str = "9.9") -> None:
        """下单（业务动作）：填三个框，点一次按钮"""
        self.customer_input.fill(customer)
        self.item_input.fill(item)
        self.price_input.fill(price)
        self.submit_btn.click()

    def expect_order_visible(self, customer: str) -> None:
        """业务断言：某客户的订单可见"""
        expect(self.page.get_by_text(customer)).to_be_visible()

    def expect_order_hidden(self, customer: str) -> None:
        expect(self.page.get_by_text(customer)).to_be_hidden()

    def delete_order(self, customer: str) -> None:
        """删除某客户的订单行"""
        row = self.page.locator("tr", has=self.page.get_by_text(customer))
        row.locator(".delete-btn").click()

    def row_count(self) -> int:
        return self.order_rows.count()
