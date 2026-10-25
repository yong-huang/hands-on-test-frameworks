"""项目 15 验收（Chromium-only）：CDP 拦截请求、弱网模拟、性能指标采集。

三条能力都走 chromedriver 的 execute_cdp_cmd——非 Chromium 内核直接 skip。
"""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


def _require_chrome(driver):
    if driver.capabilities.get("browserName") != "chrome":
        pytest.skip("CDP 能力仅 Chromium 内核（本机矩阵见 14_browser_matrix/COMPAT_NOTES.md）")


def _products_durations(driver) -> list[float]:
    """读 performance 资源条目里 /api/products 的耗时（ms）。"""
    return driver.execute_script(
        "return performance.getEntriesByType('resource')"
        ".filter(e => e.name.includes('/api/products'))"
        ".map(e => e.duration);")


def test_block_products_api(shop_url, driver):
    """Network.setBlockedURLs 拦截商品接口：页面拿不到数据，加载提示滞留。"""
    _require_chrome(driver)
    driver.execute_cdp_cmd("Network.enable", {})
    driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": ["*api/products*"]})
    try:
        driver.get(shop_url)
        time_view = WebDriverWait(driver, 6).until(
            lambda d: d.find_element(By.ID, "load-hint") if d.find_element(By.ID, "load-hint").is_displayed() else False)
        assert len(driver.find_elements(By.CLASS_NAME, "card")) == 0, "被拦截后不应有商品渲染"
        assert "正在加载" in time_view.text
    finally:
        driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": []})
    driver.get(shop_url)
    WebDriverWait(driver, 10).until(lambda d: len(d.find_elements(By.CLASS_NAME, "card")) >= 10)
    print("拦截生效：商品接口被断后页面停在加载态；解除后恢复")


def test_weak_network_slow_down(shop_url, driver):
    """Network.emulateNetworkConditions 模拟弱网：同一接口耗时显著劣化。"""
    _require_chrome(driver)
    driver.get(shop_url)
    WebDriverWait(driver, 10).until(lambda d: len(d.find_elements(By.CLASS_NAME, "card")) >= 10)
    base = max(_products_durations(driver))

    driver.execute_cdp_cmd("Network.enable", {})
    # 512B/s 下行 + 2s 往返延迟——响应体只有几百字节，档位不够狠拉不开差距（实测 50KB/s 仅 +437ms）
    driver.execute_cdp_cmd("Network.emulateNetworkConditions", {
        "offline": False, "latency": 2000,
        "downloadThroughput": 512, "uploadThroughput": 512})
    driver.get(shop_url)
    WebDriverWait(driver, 20).until(lambda d: len(d.find_elements(By.CLASS_NAME, "card")) >= 10)
    weak = max(_products_durations(driver))
    driver.execute_cdp_cmd("Network.emulateNetworkConditions", {
        "offline": False, "latency": 0,
        "downloadThroughput": -1, "uploadThroughput": -1})
    print(f"接口耗时：正常 {base:.0f}ms → 弱网 {weak:.0f}ms（×{weak / base:.1f}）")
    assert weak > base * 1.8 and weak > 2500, (base, weak)


def test_performance_metrics(shop_url, driver):
    """Performance.getMetrics 采集页面级指标 + DOM 时序。"""
    _require_chrome(driver)
    driver.execute_cdp_cmd("Performance.enable", {})
    driver.get(shop_url)
    WebDriverWait(driver, 10).until(lambda d: len(d.find_elements(By.CLASS_NAME, "card")) >= 10)
    metrics = {m["name"]: m["value"] for m in
               driver.execute_cdp_cmd("Performance.getMetrics", {})["metrics"]}
    for key in ("Nodes", "JSEventListeners", "Documents"):
        assert key in metrics, f"缺指标 {key}"
    assert metrics["Nodes"] > 30, "商品页节点数应 >30"
    dcl = driver.execute_script("return performance.timing.domContentLoadedEventEnd;")
    assert dcl > 0
    print(f"指标采集 OK：Nodes={metrics['Nodes']} Listeners={metrics['JSEventListeners']} DCL={dcl}")
