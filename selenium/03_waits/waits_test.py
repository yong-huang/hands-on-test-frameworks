"""项目 3 验收：等待机制全集。

靶场素材：秒杀横幅固定在页面打开 2.5s 后现身（index.html）。
- sleep 是对时序的下注：赌少了必挂，赌多了白等
- 显式等待：等的是「条件成立」，连跑不红
- 隐式+显式叠加：超时时间会被隐性放大（经典陷阱）
"""
import csv
import os
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

BANNER = (By.ID, "flash-banner")
REPORT = []


def _banner_visible(d):
    els = d.find_elements(*BANNER)
    return bool(els) and els[0].is_displayed()


def test_sleep_is_a_bet(shop_url, driver):
    """固定 sleep 后检查横幅：赌 1s/2s 全挂、赌 3s 全过——时序一变结论就翻车。"""
    for sleep_s in (1, 2, 3):
        passes = 0
        for _ in range(3):
            driver.get(shop_url)
            time.sleep(sleep_s)
            passes += _banner_visible(driver)
        REPORT.append((f"sleep({sleep_s}s)", 3, passes, f"{sleep_s:.1f}"))
        print(f"sleep({sleep_s}s): {passes}/3 通过")
    assert passes == 3  # 赌得足够大总能过——但那是最慢的失败方式


def test_explicit_wait_ten_runs(shop_url, driver):
    """显式等待：等「条件成立」而不是赌时长——连跑 10 次不红。"""
    elapsed = []
    for i in range(10):
        driver.get(shop_url)
        t0 = time.time()
        WebDriverWait(driver, 10).until(_banner_visible)
        elapsed.append(time.time() - t0)
        assert _banner_visible(driver)
    avg = sum(elapsed) / len(elapsed)
    REPORT.append(("explicit_wait", 10, 10, f"{avg:.2f}"))
    print(f"显式等待 10/10 通过，平均现身耗时 {avg:.2f}s（横幅 2.5s + 加载开销）")
    assert all(2.0 <= e <= 6.0 for e in elapsed), elapsed


def test_fluent_wait_custom_polling(shop_url, driver):
    """FluentWait 式轮询：自定义轮询间隔与忽略异常，尽早返回。"""
    driver.get(shop_url)
    t0 = time.time()
    WebDriverWait(driver, 10, poll_frequency=0.2,
                  ignored_exceptions=[NoSuchError()]).until(_banner_visible)
    took = time.time() - t0
    REPORT.append(("fluent_wait(0.2s poll)", 1, 1, f"{took:.2f}"))
    print(f"FluentWait 0.2s 轮询：{took:.2f}s 拿到横幅（更贴近 2.5s 真值）")
    assert took < 4.0


def test_implicit_plus_explicit_trap(shop_url, driver):
    """陷阱：隐式 5s + 显式 2s 找一个不存在的元素——实际耗时远超显式的 2s。"""
    driver.get(shop_url)
    driver.implicitly_wait(5)
    try:
        t0 = time.time()
        try:
            WebDriverWait(driver, 2).until(lambda d: d.find_elements(By.ID, "no-such-thing"))
        except Exception:
            pass
        took = time.time() - t0
        REPORT.append(("implicit5+explicit2 找不存在元素", 1, 0, f"{took:.1f}"))
        print(f"显式只给 2s，实际耗时 {took:.1f}s（每次轮询的 findElement 都被隐式拖 5s）")
        assert took >= 4.0  # 至少翻倍——隐式等待把显式超时隐性放大
    finally:
        driver.implicitly_wait(0)  # 还原，避免污染同 driver 的后续用例


class NoSuchError(Exception):
    """占位：被忽略的异常类型（find_elements 不抛 NoSuch，故用空实现）。"""


def test_report():
    out = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "waits_report.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(("strategy", "runs", "passed", "avg_seconds"))
        w.writerows(REPORT)
    assert len(REPORT) >= 4
