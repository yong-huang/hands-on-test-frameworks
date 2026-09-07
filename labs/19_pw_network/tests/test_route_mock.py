"""lab 19 用例 A：page.route 网络桩——前端交互不依赖真实后端响应。

route 的回调要么 fulfill（给假响应）要么 abort（模拟断网），
被拦的请求根本不会到达 SUT——"后端挂了前端照样测"。
"""
import json

from playwright.sync_api import expect


def test_mock_slow_config_returns_instantly(page):
    """把 1.5s 的慢接口桩成 5ms：前端逻辑照常验证，测试提速 300 倍"""
    def fast_config(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"theme": "dark", "banner": "MOCKED", "loaded_after_ms": 5}),
        )
    page.route("**/api/slow-config", fast_config)

    page.goto("/")
    expect(page.locator("#banner")).to_contain_text("MOCKED", timeout=3000)


def test_inject_backend_down(page):
    """断网注入：abort 所有 /api/* 请求 → banner 停留在加载态、列表为空——优雅降级"""
    page.route("**/api/**", lambda route: route.abort("connectionrefused"))

    page.goto("/")
    expect(page.locator("#banner")).to_have_text("正在加载配置…")  # 永远等不到响应
    expect(page.locator("#orders tr")).to_have_count(0)


def test_inject_500_on_create(page):
    """500 注入：下单接口返回服务端错误，页面弹"下单失败"提示（对话框断言）"""
    import re

    def server_error(route):
        route.fulfill(status=500, content_type="application/json",
                      body=json.dumps({"detail": "内部错误（注入）"}))
    page.route("**/api/orders", lambda route: route.abort() if route.request.method != "POST"
               else server_error(route))

    page.goto("/")
    page.get_by_placeholder("客户名").fill("注入用户")
    page.get_by_placeholder("商品").fill("失败商品")
    page.get_by_placeholder("单价").fill("1")
    # expect_dialog 确定性等待 alert 弹出（注册监听+点击放同一个上下文里，无竞态）
    with page.expect_event("dialog") as dialog_info:
        page.get_by_role("button", name="创建订单").click()
    dialog = dialog_info.value
    assert "下单失败" in dialog.message
    dialog.dismiss()
