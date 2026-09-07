"""Playwright 版统一场景套件：5 条同语义用例（框架对比矩阵的 PW 一列）。"""
import uuid

from playwright.sync_api import expect


def test_1_home_loads(page):
    page.goto("/")
    expect(page.get_by_role("heading", name="Ministore 订单管理")).to_be_visible()


def test_2_create_order(page):
    uniq = uuid.uuid4().hex[:6]
    page.goto("/")
    page.get_by_placeholder("客户名").fill(f"对比-{uniq}")
    page.get_by_placeholder("商品").fill("对比商品")
    page.get_by_placeholder("单价").fill("5.5")
    page.get_by_role("button", name="创建订单").click()
    expect(page.get_by_text(f"对比-{uniq}")).to_be_visible()


def test_3_list_has_rows(page):
    page.goto("/")
    expect(page.locator("#orders tr").first).to_be_visible()


def test_4_delete_created(page):
    uniq = uuid.uuid4().hex[:6]
    page.goto("/")
    page.get_by_placeholder("客户名").fill(f"删除-{uniq}")
    page.get_by_placeholder("商品").fill("x")
    page.get_by_placeholder("单价").fill("1")
    page.get_by_role("button", name="创建订单").click()
    expect(page.get_by_text(f"删除-{uniq}")).to_be_visible()
    page.locator("tr", has=page.get_by_text(f"删除-{uniq}")).locator(".delete-btn").click()
    expect(page.get_by_text(f"删除-{uniq}")).to_be_hidden()


def test_5_slow_banner(page):
    page.goto("/")
    expect(page.locator("#banner")).to_contain_text("Banner:", timeout=15_000)
