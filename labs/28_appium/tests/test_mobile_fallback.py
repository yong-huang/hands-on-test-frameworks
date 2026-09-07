"""移动端 fallback 用例：Playwright 移动视口 + 触屏模拟（tap 而非 click）。

覆盖与 Appium 版同等的验收语义：启动 → 触屏操作 → 断言，全流程自动化。
"""
from playwright.sync_api import expect


def test_mobile_order_via_tap(page):
    """触屏下单：tap 交互 + 小屏视口上完成完整业务流"""
    import uuid
    uniq = uuid.uuid4().hex[:6]
    page.goto(f"{os.environ.get('SUT_URL', 'http://127.0.0.1:8928')}/")
    page.get_by_placeholder("客户名").tap()
    page.get_by_placeholder("客户名").fill(f"手机用户-{uniq}")
    page.get_by_placeholder("商品").tap()
    page.get_by_placeholder("商品").fill("移动端商品")
    page.get_by_placeholder("单价").tap()
    page.get_by_placeholder("单价").fill("8.8")
    page.get_by_role("button", name="创建订单").tap()
    expect(page.get_by_text(f"手机用户-{uniq}")).to_be_visible()


import os


def test_mobile_viewport_layout(page):
    """小屏布局：无横向滚动（内容宽度 ≤ 视口）——移动端基本盘"""
    page.goto(f"{os.environ.get('SUT_URL', 'http://127.0.0.1:8928')}/")
    scroll_w = page.evaluate("document.documentElement.scrollWidth")
    inner_w = page.evaluate("window.innerWidth")
    assert scroll_w <= inner_w + 2, f"出现横向滚动: {scroll_w} > {inner_w}"


def test_mobile_touch_race_button(page):
    """触屏竞态按钮：slow.html 的 touch 交互在移动视口下同样稳定"""
    page.goto(f"{os.environ.get('SUT_URL', 'http://127.0.0.1:8928')}/slow.html")
    page.get_by_role("button", name="点我触发竞态").tap()
    expect(page.locator("#race-box")).to_have_text("竞态完成：状态已更新 ✅", timeout=15_000)
