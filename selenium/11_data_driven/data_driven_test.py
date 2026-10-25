"""项目 11 验收：外部 JSON 数据驱动的下单表单——5 组国际地址全过 + 1 组非法负向断言。

每组收件人带唯一毫秒后缀：证明服务端回读的是「这一组」的数据，不是上一次的缓存。
"""
import json
import os
import time

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

DATA = json.load(open(os.path.join(os.path.dirname(__file__), "orders.json"), encoding="utf-8"))
VALID = [(i, d) for i, d in enumerate(DATA["valid"])]
INVALID = DATA["invalid"][0]


def _fill_and_submit(d, customer, address):
    d.find_element(By.ID, "customer").clear()
    d.find_element(By.ID, "customer").send_keys(customer)
    addr = d.find_element(By.ID, "address")
    addr.clear()
    addr.send_keys(address)
    d.find_element(By.ID, "submit-btn").click()


@pytest.mark.parametrize("idx,data", VALID, ids=[d["label"] for _, d in VALID])
def test_valid_addresses_roundtrip(shop_url, driver, idx, data):
    customer = f'{data["customer"]}-{int(time.time() * 1000)}'  # 唯一毫秒后缀：证明读的是本轮数据
    driver.get(shop_url + "/form.html")
    _fill_and_submit(driver, customer, data["address"])
    echo_el = WebDriverWait(driver, 8).until(
        lambda d: d.find_element(By.ID, "echo") if d.find_element(By.ID, "echo").is_displayed() else False)
    received = json.loads(echo_el.text)
    assert received["customer"] == customer, f"第 {idx} 组回读不匹配"
    assert received["address"] == data["address"], f"第 {idx} 组地址回读不匹配"


def test_invalid_empty_address_blocked(shop_url, driver):
    """负向：空地址（纯空白）被客户端拦截——出现错误提示，回读区不出现。"""
    driver.get(shop_url + "/form.html")
    _fill_and_submit(driver, INVALID["customer"], INVALID["address"])
    err = WebDriverWait(driver, 5).until(
        lambda d: d.find_element(By.ID, "form-error") if d.find_element(By.ID, "form-error").is_displayed() else False)
    assert "地址必填" in err.text
    assert not driver.find_element(By.ID, "echo").is_displayed()
