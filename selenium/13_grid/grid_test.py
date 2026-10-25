"""项目 13 验收用例池：20 条轻量首页用例，供串行 vs 并行计时对照。"""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


@pytest.mark.parametrize("n", range(1, 21))
def test_home_page_ready(shop_url, driver, n):
    driver.get(shop_url)
    WebDriverWait(driver, 15).until(lambda d: len(d.find_elements(By.CLASS_NAME, "card")) >= 10)
    assert "Selenium 带病靶场" in driver.title
    assert driver.find_element(By.TAG_NAME, "h1").text == "Selenium 带病靶场"
    assert n > 0  # 占位断言：参数化体量
