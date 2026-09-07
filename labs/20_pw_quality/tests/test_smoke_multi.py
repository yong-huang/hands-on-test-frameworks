"""lab 20 用例：跨三核（Chromium/Firefox/WebKit）的冒烟回归。

由脚本以 --browser chromium --browser firefox --browser webkit 参数化三次执行。
"""
from playwright.sync_api import expect


def test_home_loads_all_browsers(page):
    """首页加载 + 核心区可见：三核都能过的最小冒烟"""
    page.goto("/")
    expect(page.get_by_role("heading", name="Ministore 订单管理")).to_be_visible()


def test_banner_eventually_loads(page):
    """慢接口 banner：WebKit 上 fetch 时序略不同——expect 等到为准（兼容性差异记录点）"""
    page.goto("/")
    expect(page.locator("#banner")).to_contain_text("Banner:", timeout=15_000)


def test_order_roundtrip(page):
    """下单主流程在三核上等价（自动化商品 + 删除）"""
    import uuid
    uniq = uuid.uuid4().hex[:6]
    page.goto("/")
    page.get_by_placeholder("客户名").fill(f"三核-{uniq}")
    page.get_by_placeholder("商品").fill("跨核商品")
    page.get_by_placeholder("单价").fill("3.3")
    page.get_by_role("button", name="创建订单").click()
    expect(page.get_by_text(f"三核-{uniq}")).to_be_visible()
    row = page.locator("tr", has=page.get_by_text(f"三核-{uniq}"))
    row.locator(".delete-btn").click()
    expect(page.get_by_text(f"三核-{uniq}")).to_be_hidden()
