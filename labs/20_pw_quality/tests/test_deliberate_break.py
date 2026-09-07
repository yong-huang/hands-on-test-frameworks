"""人为失败用例：给 lab 20 的留痕演示（截图+trace+video）当靶子。正常套件不跑它。"""
from playwright.sync_api import expect


def test_deliberately_wrong(page):
    page.goto("/")
    expect(page.get_by_role("heading", name="不存在的主观标题")).to_be_visible()
