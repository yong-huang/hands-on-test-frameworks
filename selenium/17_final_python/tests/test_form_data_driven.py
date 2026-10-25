"""表单数据驱动（5 组国际地址，数据复用项目 11 的 orders.json）。"""
import json
import time
from pathlib import Path

import pytest
from pages.form_page import FormPage

DATA = json.load(open(Path(__file__).parents[2] / "11_data_driven" / "orders.json", encoding="utf-8"))
VALID = [(i, d) for i, d in enumerate(DATA["valid"])]


@pytest.mark.parametrize("idx,data", VALID, ids=[d["label"] for _, d in VALID])
def test_form_roundtrip(shop_url, driver, idx, data):
    customer = f'🏁{data["customer"]}-{int(time.time() * 1000)}'
    received = FormPage(driver, shop_url).submit_order(customer, data["address"])
    assert received["customer"] == customer
    assert received["address"] == data["address"]
