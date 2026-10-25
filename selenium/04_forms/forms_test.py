"""项目 4 验收：靶场下单表单 8 类控件程序化操作 + 服务端回读逐字段断言。"""
import json

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait


def test_full_form_roundtrip(shop_url, driver, tmp_path):
    driver.get(shop_url + "/form.html")
    w = WebDriverWait(driver, 10)

    # ① 文本：中文 + 特殊字符
    driver.find_element(By.ID, "customer").send_keys("李雷 ⚡<testing>")

    # ② 下拉（单选）
    Select(driver.find_element(By.ID, "channel")).select_by_value("web")

    # ③ 下拉（多选）：加急 + 保价
    tags = Select(driver.find_element(By.ID, "tags"))
    tags.select_by_value("rush")
    tags.select_by_value("insure")

    # ④ 复选框
    driver.find_element(By.ID, "gift").click()

    # ⑤ 单选：EMS
    driver.find_element(By.CSS_SELECTOR, "input[name=express][value=ems]").click()

    # ⑥ 日期控件：键入顺序受浏览器 locale 段位顺序摆布（实测 zh/en 两种数字序列都翻出
    #    「110120-02-06」这类鬼日期），改用 JS 设值 + 派发 change——表单提交时读 .value，
    #    change 事件保证 onChange 型监听也同步（locale 坑详见 README 踩坑节）
    driver.execute_script(
        "const el = document.getElementById('date');"
        "el.value = '2026-11-01';"
        "el.dispatchEvent(new Event('change', {bubbles: true}));"
    )
    assert driver.find_element(By.ID, "date").get_attribute("value") == "2026-11-01"

    # ⑦ 滑块：5 → 点选聚焦后按 3 次右箭头 = 8
    weight = driver.find_element(By.ID, "weight")
    weight.click()
    weight.send_keys(Keys.ARROW_RIGHT * 3)
    assert weight.get_attribute("value") == "8"

    # ⑧ 文件上传：send_keys 直接投递绝对路径
    att = tmp_path / "凭证-李雷.txt"
    att.write_text("订单凭证内容", encoding="utf-8")
    driver.find_element(By.ID, "attachment").send_keys(str(att))

    driver.find_element(By.ID, "submit-btn").click()
    echo_el = w.until(lambda d: d.find_element(By.ID, "echo") if d.find_element(By.ID, "echo").is_displayed() else False)
    received = json.loads(echo_el.text)

    assert received["customer"] == "李雷 ⚡<testing>"
    assert received["channel"] == "web"
    assert received["tags"] == ["rush", "insure"]
    assert received["gift"] is True
    assert received["express"] == "ems"
    assert received["date"] == "2026-11-01"
    assert received["weight"] == "8"
    assert received["attachment"]["name"] == "凭证-李雷.txt"
    assert received["attachment"]["size"] > 0
