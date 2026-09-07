"""lab 25 共享 fixture：Selenium driver + SUT 地址。"""
import os

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


@pytest.fixture()
def sut_url():
    return os.environ.get("SUT_URL", "http://127.0.0.1:8925")


@pytest.fixture()
def driver():
    opts = Options()
    opts.add_argument("--headless=new")
    d = webdriver.Chrome(options=opts)
    yield d
    d.quit()
