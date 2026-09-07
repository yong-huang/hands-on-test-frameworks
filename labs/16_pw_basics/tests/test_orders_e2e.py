"""lab 16 用例：SUT 首页的 下单 → 查询 → 删除 三部曲（Chromium）。

pytest-playwright 提供 page fixture（每用例全新页面，自动等待）；
--base-url 由脚本传入，page.goto("/") 即首页。
"""
import re
import uuid

from playwright.sync_api import expect


def test_create_order(page):
    """下单：填表 → 提交 → 新订单出现在列表（自动等待渲染，无 sleep）"""
    uniq = uuid.uuid4().hex[:6]
    page.goto("/")
    page.get_by_placeholder("客户名").fill(f"E2E用户-{uniq}")
    page.get_by_placeholder("商品").fill("自动化商品")
    page.get_by_placeholder("单价").fill("42.5")
    page.get_by_role("button", name="创建订单").click()
    # web-first 断言：expect 会自动等待元素出现（is_visible() 不等待，是常见坑）
    expect(page.get_by_text(f"E2E用户-{uniq}")).to_be_visible()


def test_order_list_shows_seed_data(page):
    """查询：列表至少有一行订单，且含表头列"""
    page.goto("/")
    assert page.locator("table thead th").count() >= 7
    # 等列表接口返回（行数 > 0），而非盲等固定时长
    page.wait_for_function("document.querySelectorAll('#orders tr').length > 0")


def test_delete_created_order(page):
    """删除：创建一行，再删掉它，行从列表消失"""
    uniq = uuid.uuid4().hex[:6]
    page.goto("/")
    page.get_by_placeholder("客户名").fill(f"待删-{uniq}")
    page.get_by_placeholder("商品").fill("即抛商品")
    page.get_by_placeholder("单价").fill("1")
    page.get_by_role("button", name="创建订单").click()
    row = page.locator("tr", has=page.get_by_text(f"待删-{uniq}"))
    row.locator(".delete-btn").click()
    # 断言"行最终消失"——expect 自带重试语义
    expect(page.get_by_text(f"待删-{uniq}")).to_be_hidden()
