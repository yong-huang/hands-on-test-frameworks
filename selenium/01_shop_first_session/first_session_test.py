"""项目 1 验收：三浏览器各自完成「打开靶场 → 断言标题 → 打印版本 → 退出」。"""
import pytest

from conftest import make_driver

ALL = ["chrome", "firefox", "safari"]


@pytest.mark.parametrize("name", ALL)
def test_first_session(name, shop_url):
    d = make_driver(name, headless=(name != "safari"))  # Safari 无无头模式
    try:
        d.get(shop_url)
        assert "Selenium 带病靶场" in d.title
        assert d.find_element("tag name", "h1").text == "Selenium 带病靶场"
        caps = d.capabilities
        print(f"[{name}] browser={caps.get('browserVersion')} "
              f"driver={caps.get('chrome', {}).get('chromedriverVersion', caps.get('moz:geckodriverVersion', 'safaridriver'))}")
    finally:
        d.quit()
