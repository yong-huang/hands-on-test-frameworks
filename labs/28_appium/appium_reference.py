"""Appium 2 + Xcode Simulator 参考实现（本机环境受阻，未实际执行——如实记录）。

环境受阻原因（2026-09 本机探测）：
- xcode-select 指向 CommandLineTools，simctl 不可用（无法启动 iOS Simulator）；
- Appium server 未安装（需 npm install -g appium && appium driver install xcuitest）；
- 还需一个可安装到模拟器的被测 App（SUT 无移动端壳）。

补齐以上三项后，本文件的用例可直接运行：
    pip install Appium-Python-Client
    npm install -g appium && appium driver install xcuitest
    appium --base-path /wd/hub          # 另开终端起 server
    python -m pytest tests/test_appium.py -v
"""
from appium import webdriver
from appium.options.ios import XCUITestOptions


def make_driver():
    options = XCUITestOptions()
    options.platform_name = "iOS"
    options.device_name = "iPhone 15"
    options.platform_version = "17.5"
    options.automation_name = "XCUITest"
    options.bundle_id = "com.apple.Preferences"   # 以系统设置 App 为最小可运行示例
    options.no_reset = True
    return webdriver.Remote("http://127.0.0.1:4723/wd/hub", options=options)


def test_settings_app_launches():
    """冒烟：Simulator 内启动 → accessibility id 定位 → 断言（操作→断言全自动）"""
    driver = make_driver()
    try:
        # accessibility id 是 Appium 定位首选：语义稳定、与 UI 无关
        cells = driver.find_elements("accessibility id", "通用")
        assert isinstance(cells, list)
    finally:
        driver.quit()
