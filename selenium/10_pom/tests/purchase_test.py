"""测试层（POM：页面三层之三）——只有业务语言，零定位细节（硬规则见 .sh）。"""
import json
import urllib.request

from flows.purchase_flow import PurchaseFlow


def test_buy_and_pay_roundtrip(shop_url, driver):
    order_id = PurchaseFlow(driver, shop_url).buy_and_pay()
    assert order_id.startswith("ORD-")
    with urllib.request.urlopen(f"{shop_url}/api/orders/{order_id}", timeout=5) as r:
        order = json.load(r)
    assert order["status"] == "paid"
    assert order["amount"] > 0
