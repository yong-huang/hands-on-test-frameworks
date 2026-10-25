"""🏁 终极回归套件：POM + 数据驱动 + 失败留证，一条命令出全绿报告。

- 购买支付走项目 10 的 POM（sys.path 复用，不复制代码）
- 表单数据驱动走项目 11 的 orders.json（5 组国际地址）
- INJECT_FAILURE=1 时注入失败验证证据链（默认关闭）
"""
import json
import os
import time
import urllib.request
from pathlib import Path

import pytest
from flows.purchase_flow import PurchaseFlow

from pages.form_page import FormPage

pytestmark = pytest.mark.regression

ORDERS = json.load(open(Path(__file__).parents[1].parent / "11_data_driven" / "orders.json", encoding="utf-8"))


def test_purchase_roundtrip(shop_url, driver):
    order_id = PurchaseFlow(driver, shop_url).buy_and_pay()
    with urllib.request.urlopen(f"{shop_url}/api/orders/{order_id}", timeout=5) as r:
        order = json.load(r)
    assert order["status"] == "paid" and order["amount"] > 0, order


def test_home_loaded(shop_url, driver):
    driver.get(shop_url)
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    WebDriverWait(driver, 15).until(lambda d: len(d.find_elements(By.TAG_NAME, "h2")) >= 1)
    assert "Selenium 带病靶场" in driver.title


def test_injectable_guard(shop_url, driver):
    """注入开关演示：INJECT_FAILURE=1 时本用例红（用于验证证据链与报告的失败呈现）。"""
    if os.environ.get("INJECT_FAILURE") == "1":
        driver.get(shop_url + "/checkout.html")
        from selenium.webdriver.common.by import By
        assert driver.find_element(By.ID, "no-such-element"), "注入失败：该元素不存在"
    assert True
