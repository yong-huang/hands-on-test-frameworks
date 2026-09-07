"""lab 23 用例：Selenium 的显式等待 vs 无等待——亲手体会差距。

pytest fixture 起 Chrome（Selenium Manager 自动下载驱动）；
SUT 由脚本预先起在 8923。
"""
import uuid

import pytest
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


@pytest.fixture()
def driver():
    opts = Options()
    opts.add_argument("--headless=new")
    d = webdriver.Chrome(options=opts)   # Selenium Manager：驱动自动匹配下载
    d.implicitly_wait(0)                 # 关掉隐式等待，让"等待策略"的差异显性化
    yield d
    d.quit()


def _place_order(driver, customer: str) -> None:
    driver.get("http://127.0.0.1:8923/")
    driver.find_element(By.ID, "customer").send_keys(customer)
    driver.find_element(By.ID, "item").send_keys("selenium 商品")
    driver.find_element(By.ID, "price").send_keys("6.6")
    driver.find_element(By.XPATH, "//button[text()='创建订单']").click()


def test_basic_order_flow_chrome(driver):
    """基础用例：下单后轮询等订单上屏（显式等待版，稳定）"""
    uniq = uuid.uuid4().hex[:6]
    _place_order(driver, f"sel用户-{uniq}")
    WebDriverWait(driver, 10).until(
        EC.text_to_be_present_in_element((By.TAG_NAME, "tbody"), f"sel用户-{uniq}")
    )


def test_no_wait_fails_on_delayed_page(driver):
    """没有等待就必挂：点击后立刻找 2 秒后才渲染的元素 → NoSuchElementException"""
    driver.get("http://127.0.0.1:8923/slow.html")
    driver.find_element(By.ID, "load-late").click()
    with pytest.raises(Exception):        # NoSuchElementException（或其父类）
        driver.find_elements(By.CSS_SELECTOR, "#late-list .box") and None
        boxes = driver.find_element(By.CSS_SELECTOR, "#late-list .box")  # 立刻找：必挂
        assert boxes is None


def test_explicit_wait_survives_delayed_page(driver):
    """同一页面的显式等待版：WebDriverWait 稳定等到 3 条条目"""
    driver.get("http://127.0.0.1:8923/slow.html")
    driver.find_element(By.ID, "load-late").click()
    WebDriverWait(driver, 10).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, "#late-list .box")) == 3
    )
    assert len(driver.find_elements(By.CSS_SELECTOR, "#late-list .box")) == 3
