"""fallback 的 fixture：Playwright iPhone 14 设备描述符（视口+触屏+移动 UA）。"""
import os

import pytest
from playwright.sync_api import sync_playwright

SUT_URL = os.environ.get("SUT_URL", "http://127.0.0.1:8928")


@pytest.fixture(scope="session")
def playwright():
    with sync_playwright() as p:
        yield p


@pytest.fixture()
def iphone(playwright):
    """真机描述符：390×843 视口 + hasTouch + 移动 UA + 移动视口元数据"""
    device = playwright.devices["iPhone 14"]
    browser = playwright.chromium.launch()
    context = browser.new_context(**device)
    yield context
    context.close()
    browser.close()


@pytest.fixture()
def page(iphone):
    return iphone.new_page()
