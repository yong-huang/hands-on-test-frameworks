"""lab 19 用例 B：storageState 登录态复用 + admin/user 双角色不串号。

第一次用 UI 登录取 token 存为 .auth/admin.json / .auth/user.json（session 级）；
之后的用例直接带状态新建 context——零登录成本。
"""
from pathlib import Path

import pytest
from playwright.sync_api import expect

AUTH_DIR = Path(".auth")

USERS = {
    "admin": ("admin", "admin123"),
    "user": ("user", "user123"),
}


def _ui_login(context, username: str) -> None:
    """真实 UI 登录一次，把 localStorage（token/role）落成 storageState"""
    page = context.new_page()
    page.goto("/login.html")
    page.get_by_placeholder("用户名（admin / user）").fill(USERS[username][0])
    page.get_by_placeholder("密码（admin123 / user123）").fill(USERS[username][1])
    page.get_by_role("button", name="登录").click()
    expect(page.locator("#msg")).to_contain_text("登录成功")
    context.storage_state(path=str(AUTH_DIR / f"{username}.json"))
    page.close()


@pytest.fixture(scope="session")
def auth_states(browser, base_url):
    """session 级：为两个角色各保存一份登录态"""
    AUTH_DIR.mkdir(exist_ok=True)
    states = {}
    for role in ("admin", "user"):
        ctx = browser.new_context(base_url=base_url)
        _ui_login(ctx, role)
        ctx.close()
        states[role] = str(AUTH_DIR / f"{role}.json")
    return states


@pytest.fixture()
def logged_in(browser, base_url, auth_states, request):
    """参数化夹具：request.param 是角色名，返回带登录态的 context"""
    role = request.param
    ctx = browser.new_context(base_url=base_url, storage_state=auth_states[role])
    yield ctx
    ctx.close()


@pytest.mark.parametrize("logged_in", ["admin"], indirect=True)
def test_admin_sees_stats(logged_in):
    """admin 会话打开控制台：看到总订单数"""
    page = logged_in.new_page()
    page.goto("/admin.html")
    expect(page.locator("#stats")).to_contain_text("总订单数")


@pytest.mark.parametrize("logged_in", ["user"], indirect=True)
def test_user_is_denied_admin_console(logged_in):
    """user 会话打开同一页：403，页面显示拒绝文案——角色不串号"""
    page = logged_in.new_page()
    page.goto("/admin.html")
    expect(page.locator("#stats")).to_contain_text("访问被拒")


@pytest.mark.parametrize("logged_in", ["user"], indirect=True)
def test_user_token_cannot_call_admin_api(logged_in, base_url):
    """用 user 会话里的 token 直接打 admin API：403（双重验证不串号）"""
    import httpx
    page = logged_in.new_page()
    page.goto("/")  # localStorage 依赖站点 origin：about:blank 上读取会被拒
    token = page.evaluate("localStorage.getItem('token')")
    assert token
    r = httpx.get(f"{str(base_url).rstrip('/')}/api/admin/stats",
                  headers={"Authorization": f"Bearer {token}"},
                  trust_env=False, timeout=5)
    assert r.status_code == 403
