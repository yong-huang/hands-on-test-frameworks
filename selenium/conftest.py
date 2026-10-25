"""selenium 系列共享夹具：driver 工厂 + 靶场会话级拉起。

- SELENIUM_BROWSER 环境变量选浏览器（chrome/firefox/safari，默认 chrome）
- HEADLESS=0 关闭无头（默认无头；Safari 不支持无头，恒为有头）
"""
import os
import subprocess
import urllib.request

import pytest
from selenium import webdriver

SHOP_PORT = 8946
SHOP_URL = f"http://127.0.0.1:{SHOP_PORT}"


def make_driver(name: str = "chrome", headless: bool | None = None):
    """按名字造 driver。首会话等实验直接用它跑多浏览器。"""
    headless = (os.environ.get("HEADLESS", "1") == "1") if headless is None else headless
    if name == "chrome":
        opts = webdriver.ChromeOptions()
        if headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1400,1000")
        opts.add_argument("--disable-search-engine-choice-screen")
        return webdriver.Chrome(options=opts)
    if name == "firefox":
        opts = webdriver.FirefoxOptions()
        if headless:
            opts.add_argument("-headless")
        return webdriver.Firefox(options=opts)
    if name == "safari":
        return webdriver.Safari()  # Safari 无无头模式，恒有头
    raise ValueError(f"未知浏览器: {name}")


@pytest.fixture(scope="session", autouse=True)
def shop():
    """会话级确保靶场在线（幂等：已运行则直接用）。"""
    try:
        urllib.request.urlopen(f"{SHOP_URL}/api/health", timeout=2)
        yield SHOP_URL
        return
    except Exception:
        pass
    shop_sh = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shop", "shop.sh")
    subprocess.run(["bash", shop_sh, "apply"], check=True)
    yield SHOP_URL


@pytest.fixture
def shop_url(shop):
    return shop


@pytest.fixture
def driver(browser_name):
    d = make_driver(browser_name)
    d.set_window_size(1400, 1000)
    yield d
    d.quit()


@pytest.fixture
def browser_name():
    return os.environ.get("SELENIUM_BROWSER", "chrome")
