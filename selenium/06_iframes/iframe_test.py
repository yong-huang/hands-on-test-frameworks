"""项目 6 验收：三层 iframe 逐层切入 → 购买 → 支付 → 切回主文档断言订单号。"""
import json
import urllib.request

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

ORDER_ID_JS = "return document.getElementById('order-id').textContent;"


def _wait_order_text(d, needle):
    return needle in d.find_element(By.ID, "order-id").text


def test_three_level_frame_purchase(shop_url, driver):
    driver.get(shop_url + "/checkout.html")
    # 逐层切入：outer → middle → inner（每层等它加载出下一层）
    for fid in ("frame-outer", "frame-middle", "frame-inner"):
        WebDriverWait(driver, 10).until(lambda d, f=fid: d.find_elements(By.ID, f))
        driver.switch_to.frame(driver.find_element(By.ID, fid))

    driver.find_element(By.ID, "buy-btn").click()
    WebDriverWait(driver, 10).until(lambda d: _wait_order_text(d, "ORD-"))
    order_id = driver.find_element(By.ID, "order-id").text.replace("订单号 ", "").strip()
    assert order_id.startswith("ORD-")

    driver.find_element(By.ID, "pay-btn").click()
    WebDriverWait(driver, 10).until(lambda d: _wait_order_text(d, "已支付"))

    # 回到主文档后，从 API 侧确认状态（不只信页面自说自话）
    driver.switch_to.default_content()
    with urllib.request.urlopen(f"{shop_url}/api/orders/{order_id}", timeout=5) as r:
        order = json.load(r)
    assert order["status"] == "paid", order
    print(f"三层 iframe 内完成购买+支付，API 复核 status=paid（{order_id}, ${order['amount']}）")


def test_frame_by_index_switch(shop_url, driver):
    """frame 也可按序号（index）切换：checkout 主文档的第一个 frame 就是 outer。"""
    driver.get(shop_url + "/checkout.html")
    WebDriverWait(driver, 10).until(lambda d: d.find_elements(By.ID, "frame-outer"))
    driver.switch_to.frame(0)  # index 切换
    assert len(driver.find_elements(By.ID, "frame-middle")) == 1
    driver.switch_to.default_content()

    # 反例（保留注释）：不切 frame 直接找内层按钮 → NoSuchElementException
    # driver.find_element(By.ID, "buy-btn")   # ❌ NoSuchElementException


def test_alert_blocking_demo(shop_url, driver):
    """陷阱③：原生 alert 不处理，页面上的后续操作全部阻塞。"""
    driver.get(shop_url + "/checkout.html")
    driver.find_element(By.ID, "promo-btn").click()
    alert = driver.switch_to.alert
    assert "已开启促销提醒" in alert.text
    alert.accept()
    WebDriverWait(driver, 5).until(
        lambda d: d.find_element(By.ID, "promo-state").text == "已开启")
