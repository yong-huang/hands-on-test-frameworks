"""项目 2 验收：八种定位策略实战 + 定位器健壮性打分表。

策略口径（8 种）：id / class name / css selector / tag name / link text /
partial link text / 相对定位器（relative）/ xpath（仅对比实验允许）。
"""
import csv
import os

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.relative_locator import locate_with
from selenium.webdriver.support.ui import WebDriverWait

ROBUST = {"id": 5, "relative": 4, "css": 4, "link_text": 3, "partial_link_text": 3,
          "class_name": 2, "tag_name": 1, "xpath": 1}
ROWS = []  # (元素, 策略, 命中数, 健壮性分)


def _probe(driver, shop_url, label, strategy, by, selector, expect_min=1):
    driver.get(shop_url)
    WebDriverWait(driver, 15).until(lambda d: len(d.find_elements(By.CLASS_NAME, "card")) >= 10)
    hits = len(driver.find_elements(by, selector))
    ROWS.append((label, strategy, hits, ROBUST[strategy]))
    assert hits >= expect_min, f"{label} / {strategy}: 命中 {hits} < {expect_min}"
    return hits


def test_eight_strategies_on_index(shop_url, driver):
    """首页元素上逐一验证 7 种策略（xpath 单独对比用例）。"""
    _probe(driver, shop_url, "秒杀横幅", "id", By.ID, "flash-banner")
    _probe(driver, shop_url, "商品卡", "class_name", By.CLASS_NAME, "card", expect_min=10)
    _probe(driver, shop_url, "商品价格", "css", By.CSS_SELECTOR, ".card .price", expect_min=10)
    _probe(driver, shop_url, "页头", "tag_name", By.TAG_NAME, "h1")
    _probe(driver, shop_url, "结账链接", "link_text", By.LINK_TEXT, "下单结账")
    _probe(driver, shop_url, "结账链接(部分)", "partial_link_text", By.PARTIAL_LINK_TEXT, "结账")
    # 相对定位器：位于「商品列表」标题下方的商品网格卡片（锚元素必须可见：
    # 隐藏或零尺寸的锚会让 chromedriver 直接抛 unknown error）
    near = driver.find_elements(locate_with(By.CLASS_NAME, "card").below({By.TAG_NAME: "h2"}))
    ROWS.append(("商品卡", "relative", len(near), ROBUST["relative"]))
    assert len(near) >= 10


def test_xpath_demo_only(shop_url, driver):
    """XPath 只允许出现在对比实验里——验证它能用，但主套件不采用。"""
    _probe(driver, shop_url, "页头", "xpath", By.XPATH, "//header/h1")


def test_buy_button_in_iframe_six_strategies(shop_url, driver):
    """同一购买按钮 ≥6 种策略全部命中（三层 frame 内）。"""
    driver.get(shop_url + "/checkout.html")
    for fid in ("frame-outer", "frame-middle", "frame-inner"):
        WebDriverWait(driver, 10).until(lambda d, f=fid: d.find_elements(By.ID, f))
        driver.switch_to.frame(driver.find_element(By.ID, fid))
    assert len(driver.find_elements(By.ID, "buy-btn")) == 1
    ROWS.append(("购买按钮(iframe)", "id", 1, ROBUST["id"]))
    ROWS.append(("购买按钮(iframe)", "css", len(driver.find_elements(By.CSS_SELECTOR, "button#buy-btn")), ROBUST["css"]))
    ROWS.append(("购买按钮(iframe)", "xpath", len(driver.find_elements(By.XPATH, "//button[text()='确认购买']")), ROBUST["xpath"]))
    ROWS.append(("购买按钮(iframe)", "tag_name", len(driver.find_elements(By.TAG_NAME, "button")), ROBUST["tag_name"]))
    ROWS.append(("购买按钮(iframe)", "class_name", len(driver.find_elements(By.CLASS_NAME, "primary")), ROBUST["class_name"]))
    near = driver.find_elements(locate_with(By.TAG_NAME, "button").near({By.ID: "order-id"}))
    ROWS.append(("购买按钮(iframe)", "relative", len(near), ROBUST["relative"]))
    strategies = [r for r in ROWS if r[0].startswith("购买按钮")]
    assert len(strategies) >= 6 and all(r[2] >= 1 for r in strategies)
    assert len(near) == 1  # 锚可见时 near 精确命中唯一按钮


def test_score_table():
    """产出定位器健壮性打分表 CSV（改版存活率为主观分：id>相对≈css>链接文本>class>tag≈xpath）。"""
    assert len(ROWS) >= 14, f"采样行数不足: {len(ROWS)}（7 首页 + 1 xpath + 6 iframe）"
    out = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "locator_scores.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(("element", "strategy", "hits", "robustness_score"))
        w.writerows(ROWS)
    assert os.path.getsize(os.path.join(out, "locator_scores.csv")) > 100
