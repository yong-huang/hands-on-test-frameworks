"""订单应用回归套件：8 个测试对应 requirements.yaml 的 8 条需求（REQ-001 ~ REQ-008）。

打的是 labs/11 的应用本体（TestClient 内进程，不起服务），数据库落在 conftest
指定的临时文件——需求→测试的映射关系由 configs/test_mapping.yaml 外挂声明。
"""
import uuid

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="session")
def client():
    # 必须 with 进上下文：lifespan（建表）只在 enter 时执行，模块级裸 client 不触发
    with TestClient(app) as c:
        yield c


def _order(**over):
    body = {"customer": "追溯矩阵", "item": "需求验证商品", "qty": 1, "price": 9.9}
    body.update(over)
    return body


def test_health_ok(client):
    """REQ-001：健康检查可用。"""
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_create_order_returns_201_and_id(client):
    """REQ-002：创建订单返回 201 与订单号。"""
    r = client.post("/api/orders", json=_order(customer=f"创建-{uuid.uuid4().hex[:6]}"))
    assert r.status_code == 201
    assert isinstance(r.json()["id"], int)


def test_list_orders_returns_items_and_total(client):
    """REQ-003：列表带 items/total/limit/offset 与 X-Total-Count 头。"""
    client.post("/api/orders", json=_order(customer=f"列表-{uuid.uuid4().hex[:6]}"))
    r = client.get("/api/orders", params={"limit": 5, "offset": 0})
    assert r.status_code == 200
    body = r.json()
    assert {"items", "total", "limit", "offset"} <= set(body)
    assert body["limit"] == 5 and r.headers["X-Total-Count"] == str(body["total"])


def test_get_order_detail_by_id(client):
    """REQ-004：按单号查详情，不存在的单号返回 404。"""
    oid = client.post("/api/orders", json=_order()).json()["id"]
    got = client.get(f"/api/orders/{oid}")
    assert got.status_code == 200 and got.json()["id"] == oid
    assert client.get("/api/orders/999999999").status_code == 404


@pytest.mark.parametrize("status", ["paid", "shipped", "cancelled"])
def test_patch_order_status_flows(status, client):
    """REQ-005：状态在 created→paid→shipped→cancelled 间流转。"""
    oid = client.post("/api/orders", json=_order()).json()["id"]
    r = client.patch(f"/api/orders/{oid}", json={"status": status})
    assert r.status_code == 200 and r.json()["status"] == status


def test_delete_order_returns_204_then_404(client):
    """REQ-006：取消订单 204，取消后查询 404。"""
    oid = client.post("/api/orders", json=_order()).json()["id"]
    assert client.delete(f"/api/orders/{oid}").status_code == 204
    assert client.get(f"/api/orders/{oid}").status_code == 404


def test_login_issues_token(client):
    """REQ-007：正确帐密签发 token 与角色。"""
    r = client.post("/api/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200
    assert r.json()["role"] == "admin" and len(r.json()["token"]) >= 16
    assert client.post("/api/login",
                       json={"username": "admin", "password": "wrong"}).status_code == 401


def test_admin_stats_requires_admin_role(client):
    """REQ-008：无令牌/普通用户令牌都拿不到管理统计（403），admin 令牌可拿。"""
    assert client.get("/api/admin/stats").status_code == 403
    user_token = client.post(
        "/api/login", json={"username": "user", "password": "user123"}).json()["token"]
    assert client.get("/api/admin/stats",
                      headers={"Authorization": f"Bearer {user_token}"}).status_code == 403
    admin_token = client.post(
        "/api/login", json={"username": "admin", "password": "admin123"}).json()["token"]
    assert client.get("/api/admin/stats",
                      headers={"Authorization": f"Bearer {admin_token}"}).status_code == 200
