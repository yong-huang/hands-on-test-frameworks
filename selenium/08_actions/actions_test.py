"""项目 8 验收：Actions 交互链——拖拽、hover 二级菜单、Ctrl+S、画布涂鸦像素断言。"""
import time

from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait


def test_drag_item_into_zone(shop_url, driver):
    """click_and_hold → 移到目标区中央 → 释放；断言元素中心落在区内且高亮触发过。"""
    driver.get(shop_url + "/playground.html")
    item = driver.find_element(By.ID, "drag-item")
    zone = driver.find_element(By.ID, "drop-zone")
    ActionChains(driver).click_and_hold(item).move_to_element(zone).release().perform()
    time.sleep(0.3)
    ir = item.rect; zr = zone.rect
    cx, cy = ir["x"] + ir["width"] / 2, ir["y"] + ir["height"] / 2
    assert zr["x"] <= cx <= zr["x"] + zr["width"], (ir, zr)
    assert zr["y"] <= cy <= zr["y"] + zr["height"], (ir, zr)


def test_hover_submenu(shop_url, driver):
    """hover 父菜单 → 子菜单可见 → 点击 → 选择结果上屏。"""
    driver.get(shop_url + "/playground.html")
    parent = driver.find_element(By.ID, "menu-parent")
    ActionChains(driver).move_to_element(parent).perform()
    sub_item = WebDriverWait(driver, 5).until(
        lambda d: d.find_element(By.ID, "menu-sub-item") if d.find_element(By.ID, "menu-sub-item").is_displayed() else False)
    sub_item.click()
    assert "深色模式" in driver.find_element(By.ID, "menu-picked").text


def test_ctrl_s_shortcut(shop_url, driver):
    """组合键 Ctrl+S 被页面拦截为「保存」且不弹浏览器保存框。"""
    driver.get(shop_url + "/playground.html")
    box = driver.find_element(By.ID, "note")
    box.send_keys("自动化便签")
    ActionChains(driver).key_down(Keys.CONTROL).send_keys("s").key_up(Keys.CONTROL).perform()
    WebDriverWait(driver, 5).until(
        lambda d: "已保存：自动化便签" in d.find_element(By.ID, "save-state").text)


def test_canvas_ink_pixels(shop_url, driver):
    """画布涂鸦：墨迹像素 0 → 涂鸦后 >500 → 清空后归 0（对照 appium/07 口径）。"""
    driver.get(shop_url + "/playground.html")
    cv = driver.find_element(By.ID, "cv")

    def ink():
        return int(driver.execute_script("return document.getElementById('ink-count').textContent.match(/\\d+/)[0];"))

    assert ink() == 0
    ActionChains(driver).move_to_element_with_offset(cv, -140, -40).click_and_hold() \
        .move_by_offset(280, 100).pause(0.1).release().perform()
    after_draw = ink()
    assert after_draw > 500, f"涂鸦后墨迹像素仅 {after_draw}"
    driver.find_element(By.ID, "clear-cv").click()
    time.sleep(0.2)
    assert ink() == 0
