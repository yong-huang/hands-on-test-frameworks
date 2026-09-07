"""模拟真实工作量的 4 条用例（各 1.5s I/O 睡眠）——让 Grid 并行收益可测量。"""
import os
import sys
import time
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pages.order_page import OrderPage  # noqa: E402


@pytest.mark.parametrize("i", range(4))
def test_workload_order(driver, i):
    time.sleep(1.5)  # 模拟一次真实 I/O 密集操作
    page = OrderPage(driver, os.environ.get("SUT_URL", "http://127.0.0.1:8924"))
    uniq = uuid.uuid4().hex[:6]
    page.open().place_order(f"负载{i}-{uniq}")
    assert page.order_visible(f"负载{i}-{uniq}")
