"""项目 14 验收：下单冒烟 × Chrome/Safari/Firefox 三浏览器矩阵。"""
import json
import time

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from conftest import make_driver

BROWSERS = ["chrome", "firefox", "safari"]


@pytest.fixture(params=BROWSERS)
def matrix_driver(request):
    d = make_driver(request.param, headless=(request.param != "safari"))
    d.set_window_size(1400, 1000)
    yield request.param, d
    d.quit()


def _click(d, name, el):
    """Safari 的原生 click 在非前台时不产生 click 事件（激活前台反而阻塞，实测）——
    矩阵要验证的是表单逻辑跨浏览器一致，Safari 分支用 JS click 兜底。"""
    if name == "safari":
        d.execute_script("arguments[0].click();", el)
    else:
        el.click()


def test_order_smoke_matrix(shop_url, matrix_driver):
    """同一冒烟用例跑遍矩阵：填单 → 提交 → 回读断言。"""
    name, d = matrix_driver
    suffix = int(time.time() * 1000)
    d.get(shop_url + "/form.html")
    d.find_element(By.ID, "customer").send_keys(f"矩阵-{name}-{suffix}")
    addr = d.find_element(By.ID, "address")
    addr.clear()
    addr.send_keys(f"矩阵测试地址 {name}")
    _click(d, name, d.find_element(By.ID, "submit-btn"))
    echo_el = WebDriverWait(d, 8).until(
        lambda dd: dd.find_element(By.ID, "echo") if dd.find_element(By.ID, "echo").is_displayed() else False)
    received = json.loads(echo_el.text)
    assert received["customer"] == f"矩阵-{name}-{suffix}"
    assert received["address"] == f"矩阵测试地址 {name}"
    print(f"[{name}] 冒烟通过")


def test_title_matrix(shop_url, matrix_driver):
    """最薄的一致性用例：标题断言跑遍矩阵。"""
    name, d = matrix_driver
    d.get(shop_url)
    assert "Selenium 带病靶场" in d.title
