"""lab 12 conftest：SUT 客户端 fixture + 数据生命周期管理。

测试数据自造自清：每条用例造自己的订单（fixture 提供 factory），
teardown 时删除——保证用例互相独立、可乱序执行（xdist 安全）。
"""
import os
import uuid

import httpx
import pytest

BASE_URL = os.environ.get("SUT_BASE_URL", "http://127.0.0.1:8899")


@pytest.fixture(scope="session")
def client():
    """session 级 httpx 客户端：连接池复用，30 条用例共享一个 TCP 通道"""
    with httpx.Client(base_url=BASE_URL, timeout=10) as c:
        assert c.get("/api/health").status_code == 200, "SUT 未就绪：先跑 labs/11_sut_app/sut_app.sh"
        yield c


@pytest.fixture()
def order_factory(client):
    """造单工厂：自动带唯一标记，注册 teardown 清理——'自造自清'的核心"""
    created: list[int] = []

    def _make(**overrides) -> dict:
        uniq = uuid.uuid4().hex[:6]
        payload = {
            "customer": f"测试员-{uniq}",
            "item": "测试商品",
            "qty": 1,
            "price": 9.9,
            **overrides,
        }
        r = client.post("/api/orders", json=payload)
        assert r.status_code == 201, r.text
        order = r.json()
        created.append(order["id"])
        return order

    yield _make

    for oid in created:  # teardown：无论用例成败都清理
        client.delete(f"/api/orders/{oid}")
