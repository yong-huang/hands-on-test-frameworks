"""fixture 注入页面对象：用例只声明"我要哪个页面"。"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pages.index_page import IndexPage  # noqa: E402
from pages.slow_page import SlowPage  # noqa: E402


@pytest.fixture()
def index_page(page) -> IndexPage:
    return IndexPage(page)


@pytest.fixture()
def slow_page(page) -> SlowPage:
    return SlowPage(page)
