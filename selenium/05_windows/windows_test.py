"""项目 5 验收：多标签/窗口句柄、newWindow API、窗口尺寸、往返操作。"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


def test_compare_opens_new_tab_and_roundtrip(shop_url, driver):
    """点比价 → 新 tab → 那边操作 → 切回原窗口 → 再切过去（句柄往返）。"""
    driver.get(shop_url)
    origin = driver.current_window_handle
    driver.find_element(By.ID, "compare-btn").click()
    WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) == 2)
    driver.switch_to.window([h for h in driver.window_handles if h != origin][0])
    WebDriverWait(driver, 10).until(lambda d: "价格对照" in d.title)
    rows = driver.find_elements(By.CSS_SELECTOR, "#price-table tbody tr")
    assert len(rows) == 3
    assert "2/3 商品本店更便宜" in driver.find_element(By.ID, "verdict").text

    driver.switch_to.window(origin)
    assert "带病靶场" in driver.title
    driver.switch_to.window([h for h in driver.window_handles if h != origin][0])
    driver.close()                       # 关掉比价 tab
    driver.switch_to.window(origin)      # 回主页，只剩一个句柄
    assert len(driver.window_handles) == 1


def test_new_window_api(shop_url, driver):
    """Selenium 4 的 newWindow API：不用 window.open 也能造新标签页。
    注：chromedriver 对 NEW_WINDOW 返回 null，句柄从 window_handles 差集取。"""
    driver.get(shop_url)
    origin = driver.current_window_handle
    driver.switch_to.new_window("tab")
    assert len(driver.window_handles) == 2
    driver.switch_to.window([h for h in driver.window_handles if h != origin][0])
    driver.get(shop_url + "/compare.html")
    assert "价格对照" in driver.title
    driver.close()
    driver.switch_to.window(origin)


def test_window_size(shop_url, driver):
    """尺寸可设可读；无头模式 inner 尺寸=外框尺寸（无浏览器镶边）。"""
    d = driver
    d.set_window_size(1200, 800)
    assert abs(d.get_window_size()["width"] - 1200) <= 40
    inner = d.execute_script("return [window.innerWidth, window.innerHeight];")
    assert 1000 <= inner[0] <= 1200 and inner[1] >= 600
