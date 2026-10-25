"""项目 7 验收：JS 执行三连——懒加载滚动全载、scrollIntoView 入视口、事件陷阱实测。"""
import json
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


def _card_count(d):
    return len(d.find_elements(By.CLASS_NAME, "card"))


def test_lazy_load_all_30(shop_url, driver):
    """循环滚动到底 → 等卡片增长 → 直至 30 件全部加载。"""
    driver.get(shop_url)
    WebDriverWait(driver, 15).until(lambda d: _card_count(d) >= 10)
    deadline = time.time() + 20
    while _card_count(driver) < 30 and time.time() < deadline:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        WebDriverWait(driver, 8).until(lambda d, n=len(driver.find_elements(By.CLASS_NAME, "card")):
                                       _card_count(d) > n or d.find_element(By.ID, "load-done").is_displayed())
    assert _card_count(driver) == 30
    assert driver.find_element(By.ID, "load-done").is_displayed()


def test_scroll_into_view_brings_card_to_viewport(shop_url, driver):
    """scrollIntoView 把第 25 张卡片带进视口（不滚动页面本身）。"""
    driver.get(shop_url)
    WebDriverWait(driver, 15).until(lambda d: _card_count(d) >= 10)
    # 先滚出足够多的卡片
    deadline = time.time() + 20
    while _card_count(driver) < 25 and time.time() < deadline:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)
    cards = driver.find_elements(By.CLASS_NAME, "card")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", cards[24])
    rect = driver.execute_script(
        "const r = arguments[0].getBoundingClientRect();"
        "return {top: r.top, bottom: r.bottom, inner: window.innerHeight};", cards[24])
    assert 0 <= rect["top"] and rect["bottom"] <= rect["inner"], rect


def test_js_set_value_event_trap(shop_url, driver):
    """陷阱实测：JS 直改 value 不派发 input 事件 → 走事件同步的券码读不到。

    服务端回读 coupon 两次：JS 直改 = 空（旧状态）；sendKeys = 正常（事件触发）。
    """
    def submit_and_read(seq):
        driver.find_element(By.ID, "submit-btn").click()
        el = WebDriverWait(driver, 8).until(
            lambda d: d.find_element(By.ID, "echo")
            if d.find_element(By.ID, "echo").is_displayed()
            and d.find_element(By.ID, "echo").get_attribute("data-seq") == str(seq)
            else False)
        return json.loads(el.text)["coupon"]

    driver.get(shop_url + "/form.html")
    driver.find_element(By.ID, "customer").send_keys("事件陷阱实验员")

    # ① JS 直改 value（不派发事件）
    driver.execute_script(
        "document.getElementById('coupon').value = 'SELENIUM500';")
    got = submit_and_read(1)
    print(f"JS 直改 value → 服务端读到的券码: {got!r}（空——状态没同步）")
    assert got == ""

    # ② sendKeys（触发 input 事件）
    box = driver.find_element(By.ID, "coupon")
    box.clear()
    box.send_keys("SELENIUM500")
    got = submit_and_read(2)
    print(f"sendKeys       → 服务端读到的券码: {got!r}（事件已同步）")
    assert got == "SELENIUM500"
