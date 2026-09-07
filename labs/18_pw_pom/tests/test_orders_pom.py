"""重构后的用例：业务语言 + 一行一个动作。对比 lab 16 的原始版——
断言语义与用例数量不变，页面细节全部沉到 pages/ 里。"""
import uuid


def test_place_order(index_page):
    uniq = uuid.uuid4().hex[:6]
    index_page.open().place_order(f"POM用户-{uniq}")
    index_page.expect_order_visible(f"POM用户-{uniq}")


def test_delete_order(index_page):
    uniq = uuid.uuid4().hex[:6]
    index_page.open().place_order(f"待删用户-{uniq}")
    index_page.delete_order(f"待删用户-{uniq}")
    index_page.expect_order_hidden(f"待删用户-{uniq}")


def test_slow_page_race_flow(slow_page):
    slow_page.open().trigger_race()
    slow_page.expect_race_done()
