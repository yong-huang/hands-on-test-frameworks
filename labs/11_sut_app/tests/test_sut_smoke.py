"""SUT 自测冒烟：应用起不来，后面 19 个实验全白搭——所以它自己得先过"""
import os

import httpx

BASE = os.environ.get("SUT_BASE_URL", "http://127.0.0.1:8899")


def test_health():
    r = httpx.get(f"{BASE}/api/health", timeout=5)
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_create_and_delete_roundtrip():
    r = httpx.post(f"{BASE}/api/orders", json={
        "customer": "冒烟测试员", "item": "自检商品", "qty": 1, "price": 1.0,
    }, timeout=5)
    assert r.status_code == 201
    oid = r.json()["id"]
    assert httpx.delete(f"{BASE}/api/orders/{oid}", timeout=5).status_code == 204
