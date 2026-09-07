"""lab 17 用例：竞态/延迟渲染/慢接口 三类场景的稳定等待写法。

核心思想：**永远断言结果，不断言时刻**。expect 的自动重试把"等多久"交给框架。
"""
import uuid

from playwright.sync_api import expect


def test_delayed_render_list(page):
    """延迟渲染：列表 2 秒后才出现——expect 默认等 5s，稳稳等到"""
    page.goto("/slow.html")
    page.get_by_role("button", name="加载延迟列表（2 秒后渲染）").click()
    expect(page.locator("#late-list .box")).to_have_count(3, timeout=15_000)  # 已知慢 UI：显式给足超时


def test_race_button_state_machine(page):
    """竞态按钮：点击后 1 秒才变化——断言最终状态而非中间状态"""
    page.goto("/slow.html")
    page.get_by_role("button", name="点我触发竞态").click()
    box = page.locator("#race-box")
    expect(box).to_have_text("竞态完成：状态已更新 ✅", timeout=10_000)  # 已知 1s 变化，余量给足
    expect(page.get_by_role("button", name="再点一次")).to_be_enabled()


def test_slow_config_banner(page):
    """慢接口：首页 banner 由 1.5s 的 /api/slow-config 返回——expect 等到内容替换"""
    page.goto("/")
    expect(page.locator("#banner")).to_contain_text("welcome", timeout=15_000)


def test_role_locator_preferred(page):
    """role 定位器优先：语义定位对重构最鲁棒（改 CSS 类名不影响）"""
    page.goto("/slow.html")
    expect(page.get_by_role("heading", name="慢加载演示页")).to_be_visible()
    expect(page.get_by_role("button", name="点我触发竞态")).to_be_visible()


def test_form_positive_flow(page):
    """回归一遍主流程：用 role + placeholder 定位保持可读性"""
    uniq = uuid.uuid4().hex[:6]
    page.goto("/")
    page.get_by_placeholder("客户名").fill(f"等待练习-{uniq}")
    page.get_by_placeholder("商品").fill("等待商品")
    page.get_by_placeholder("单价").fill("7.7")
    page.get_by_role("button", name="创建订单").click()
    expect(page.get_by_text(f"等待练习-{uniq}")).to_be_visible()
