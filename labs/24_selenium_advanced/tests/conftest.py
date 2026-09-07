"""lab 24 共享 fixture：本地 Chrome 或 Grid 远程（SELENIUM_REMOTE_URL 切换）。"""
import os

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


@pytest.fixture()
def driver():
    remote = os.environ.get("SELENIUM_REMOTE_URL")
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    if remote:
        d = webdriver.Remote(command_executor=remote, options=opts)
    else:
        d = webdriver.Chrome(options=opts)
    yield d
    d.quit()
