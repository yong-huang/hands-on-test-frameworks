"""lab 24 用例：Selenium POM + ActionChains + JS 执行器。

SELENIUM_REMOTE_URL 存在时自动切到 Grid（远程 Chrome），否则本地起 Chrome——
同一套用例两种执行位置的开关就是这一个环境变量。
"""
import os
import uuid
from urllib.parse import quote

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pages.order_page import OrderPage  # noqa: E402

DRAG_PAGE = """
<html><body style="margin:40px">
<div id="src" style="width:80px;height:80px;background:#268bd2;position:absolute;left:40px;top:40px">拖我</div>
<div id="dst" style="width:120px;height:120px;background:#eee;position:absolute;left:260px;top:120px">放到这</div>
<script>
const src = document.getElementById('src'), dst = document.getElementById('dst');
let dragging = false;
src.addEventListener('mousedown', e => { dragging = true; e.preventDefault(); });
document.addEventListener('mousemove', e => {
  if (!dragging) return;
  src.style.left = e.clientX - 40 + 'px'; src.style.top = e.clientY - 40 + 'px';
});
document.addEventListener('mouseup', e => {
  if (!dragging) return; dragging = false;
  const r = dst.getBoundingClientRect();
  if (e.clientX > r.left && e.clientX < r.right && e.clientY > r.top && e.clientY < r.bottom)
    dst.textContent = '拖放完成 ✅';
});
</script></body></html>
"""


def test_pom_order_flow(driver):
    page = OrderPage(driver, os.environ.get("SUT_URL", "http://127.0.0.1:8924"))
    uniq = uuid.uuid4().hex[:6]
    page.open().place_order(f"grid用户-{uniq}")
    assert page.order_visible(f"grid用户-{uniq}")
    page.delete_order(f"grid用户-{uniq}")
    assert not page.order_visible(f"grid用户-{uniq}")


def test_actionchains_drag_and_drop(driver):
    """拖拽：ActionChains 原生鼠标事件（HTML5 DnD API 要 JS 注入，注释见 README）"""
    driver.get("data:text/html;charset=utf-8," + quote(DRAG_PAGE))  # 必须编码：# 色值会被当 URL fragment 截断
    src = driver.find_element(By.ID, "src")
    dst = driver.find_element(By.ID, "dst")
    ActionChains(driver).click_and_hold(src).move_to_element(dst).release().perform()
    assert "拖放完成" in dst.text


def test_actionchains_hover_and_js_executor(driver):
    """悬停 + JS 执行器：滚动到元素并读取 SUT 版本号"""
    driver.get(os.environ.get("SUT_URL", "http://127.0.0.1:8924") + "/slow.html")
    btn = driver.find_element(By.ID, "race-btn")
    ActionChains(driver).move_to_element(btn).perform()          # 悬停
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
    version = driver.execute_script("return document.title;")
    assert version
