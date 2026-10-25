"""消费方测试：同一套用例，PACT_BASE_URL 指向谁就打谁（真 provider 或 pact stub）。

test_unexpected_interaction 标记 stub_only——「契约外请求回 500」是 stub 的
语义，真 provider 会按自己的路由回 404，两者本就不该一致（这正是本篇与
labs/15 双向闭环的分工点）。
"""
import os
import sys

import httpx
import pytest

sys.path.insert(0, os.path.join("..", "..", "labs", "15_pact", "consumer"))
from frontend_client import create_order, get_orders  # noqa: E402

BASE = os.environ.get("PACT_BASE_URL", "http://127.0.0.1:9701")


def test_get_orders_status():
    body = get_orders(BASE)
    assert isinstance(body.get("items"), list)


def test_get_orders_shape():
    body = get_orders(BASE)
    assert "total" in body
    for item in body["items"]:
        assert item["status"] == "created"
        assert isinstance(item["customer"], str)


def test_post_order():
    body = create_order(BASE, customer="alice", item="apple", qty=2, price=3.5)
    assert body  # POST 契约应答非空


def test_query_type_match():
    # match:type：10 录制、5 重放——同为数字串即命中
    r = httpx.get(f"{BASE}/api/orders", params={"limit": 5},
                  timeout=10, trust_env=False)
    assert r.status_code == 200


@pytest.mark.stub_only
def test_unexpected_interaction():
    r = httpx.get(f"{BASE}/api/nonexistent", timeout=10, trust_env=False)
    assert r.status_code == 500
    assert r.json()["error"] == "interaction_not_found"
