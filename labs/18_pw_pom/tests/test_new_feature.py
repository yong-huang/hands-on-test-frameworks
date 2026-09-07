"""演示"新增一条用例只需 10 行"：页面对象齐备时，新用例就是这么短。"""
import uuid


def test_place_two_orders_in_a_row(index_page):
    """新需求：连续下两单都要出现在列表里——10 行搞定"""
    uniq = uuid.uuid4().hex[:6]
    page = index_page.open()
    page.place_order(f"连续下单A-{uniq}")
    page.expect_order_visible(f"连续下单A-{uniq}")  # 先等 A 上屏，避免前端刷新竞态
    page.place_order(f"连续下单B-{uniq}")
    page.expect_order_visible(f"连续下单B-{uniq}")
