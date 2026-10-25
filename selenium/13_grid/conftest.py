"""项目 13 局部夹具：driver 打向 Grid（Remote），覆盖系列共享夹具。

注意双 127.0.0.1 陷阱：Grid 容器里的 Chrome 访问 127.0.0.1 是容器自己——
浏览器侧要用 host.docker.internal 打宿主机上的靶场（server 已绑 0.0.0.0）。
"""
import os

import pytest
from selenium import webdriver

GRID_URL = os.environ.get("GRID_URL", "http://127.0.0.1:4444/wd/hub")
BROWSER_SHOP_URL = "http://host.docker.internal:8946"


@pytest.fixture
def shop_url():
    """覆盖系列夹具：返回容器浏览器可达的靶场地址。"""
    return BROWSER_SHOP_URL


@pytest.fixture
def driver():
    opts = webdriver.ChromeOptions()
    opts.add_argument("--no-sandbox")
    d = webdriver.Remote(command_executor=GRID_URL, options=opts)
    d.set_window_size(1400, 1000)
    yield d
    d.quit()
