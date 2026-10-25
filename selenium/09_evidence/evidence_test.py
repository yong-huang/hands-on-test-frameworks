"""项目 9 验收：1 条通过（零附件）+ 1 条故意失败（自动留证）。"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


def test_pass_order_flow_leaves_no_evidence(shop_url, driver):
    """通过用例：结账页可打开，注入失败前的「正常路径」。"""
    driver.get(shop_url + "/checkout.html")
    WebDriverWait(driver, 10).until(lambda d: d.find_elements(By.ID, "frame-outer"))
    assert driver.find_elements(By.ID, "promo-btn")


def test_injected_failure_produces_evidence(shop_url, driver):
    """故意失败用例：断言一个页面上不存在的东西，触发证据链。"""
    driver.get(shop_url + "/checkout.html")
    WebDriverWait(driver, 10).until(lambda d: d.find_elements(By.ID, "frame-outer"))
    # ❌ 故意的错断言：靶场首页元素不可能出现在结账页
    assert driver.find_element(By.ID, "flash-banner"), "注入的失败：结账页不该有首页横幅"
