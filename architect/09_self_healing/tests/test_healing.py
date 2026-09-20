"""自愈定位器演示套件：5 个改版页面必须自愈，1 个语义全毁页面必须如实报红。

跑完写自愈报告（reports/healing_report.json）：改版自愈率 ≥0.8 为验收线。
故意失败（broken_semantics）会让套件退出码非 0——这是设计内的红。
"""
import sys
from pathlib import Path

import pytest
from playwright.sync_api import expect

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from healer import CUSTOMER, ITEM, SUBMIT, find, write_report  # noqa: E402

PAGES = Path(__file__).resolve().parents[1] / "pages"
REPORT: list = []


@pytest.fixture(scope="session")
def page(browser):
    ctx = browser.new_context()
    yield ctx.new_page()
    summary = write_report(REPORT)
    print(f"\n=====> [healer] 定位尝试 {summary['attempts']} 次："
          f"首选命中 {summary['first_try']}，自愈 {summary['healed']}，"
          f"失败 {summary['failed']}；改版自愈率 {summary['heal_rate_of_mutants']}")


def _fill_customer(page, file_name):
    page.goto(f"file://{PAGES / file_name}")
    cust = find(page, file_name, "客户名输入框", CUSTOMER, REPORT)
    cust.fill("自愈演示客户")
    expect(cust).to_have_value("自愈演示客户")
    item = find(page, file_name, "商品输入框", ITEM, REPORT)
    assert item.is_visible()


@pytest.mark.parametrize("fname", [
    "v1_class.html", "v2_id.html", "v3_noplaceholder.html",
    "v4_nested.html", "v5_rebrand.html",
])
def test_改版页面自愈(page, fname):
    _fill_customer(page, fname)


def test_语义全毁页面必须如实报红(page):
    """id/class/placeholder/aria-label 全变：任何自愈都是误愈——必须红。"""
    page.goto(f"file://{PAGES / 'broken_semantics.html'}")
    with pytest.raises(AssertionError):
        find(page, "broken_semantics.html", "客户名输入框", CUSTOMER, REPORT)
