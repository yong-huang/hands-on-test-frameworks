"""lab 12 用例：对 SUT 的 30 条 API 用例（CRUD 12 + 分页/列表 6 + 负向 7 + 登录/慢接口 5）。

约定：每条用例通过 order_factory 造数据、自动清理——互相独立、可乱序、可并行。
"""
import time

import pytest
from pydantic import BaseModel, Field, ValidationError


# ---------- 响应模型：pydantic schema 校验（字段有且类型对） ----------
class OrderOut(BaseModel):
    id: int
    customer: str
    item: str
    qty: int = Field(gt=0)
    price: float = Field(ge=0)
    status: str
    created_at: str


def test_order_schema_contract(client, order_factory):
    """每个端点的响应都必须过模型——契约测试的轻量替代（重型版见 lab 15 Pact）"""
    order = order_factory()
    OrderOut.model_validate(order)


def test_create_returns_location_header(client, order_factory):
    order = order_factory()
    # factory 里已 POST 过一次；这里直接断言 Location 规则
    r = client.post("/api/orders", json={
        "customer": "定位头测试员", "item": "x", "qty": 1, "price": 1})
    assert r.status_code == 201
    assert r.headers["location"] == f"/api/orders/{r.json()['id']}"
    client.delete(f"/api/orders/{r.json()['id']}")


def test_create_is_queryable(client, order_factory):
    order = order_factory(qty=7)
    r = client.get(f"/api/orders/{order['id']}")
    assert r.status_code == 200
    assert r.json()["qty"] == 7


# ---------- CRUD ----------
def test_get_missing_returns_404(client):
    assert client.get("/api/orders/999999").status_code == 404


def test_patch_status_created_to_paid(client, order_factory):
    order = order_factory()
    r = client.patch(f"/api/orders/{order['id']}", json={"status": "paid"})
    assert r.status_code == 200 and r.json()["status"] == "paid"


def test_patch_status_to_shipped(client, order_factory):
    order = order_factory()
    client.patch(f"/api/orders/{order['id']}", json={"status": "paid"})
    r = client.patch(f"/api/orders/{order['id']}", json={"status": "shipped"})
    assert r.json()["status"] == "shipped"


def test_patch_cancelled(client, order_factory):
    order = order_factory()
    r = client.patch(f"/api/orders/{order['id']}", json={"status": "cancelled"})
    assert r.json()["status"] == "cancelled"


def test_patch_missing_order_404(client):
    assert client.patch("/api/orders/999999", json={"status": "paid"}).status_code == 404


def test_delete_then_get_404(client, order_factory):
    order = order_factory()
    assert client.delete(f"/api/orders/{order['id']}").status_code == 204
    assert client.get(f"/api/orders/{order['id']}").status_code == 404


def test_delete_missing_404(client):
    assert client.delete("/api/orders/999999").status_code == 404


def test_delete_twice_second_404(client, order_factory):
    order = order_factory()
    client.delete(f"/api/orders/{order['id']}")
    assert client.delete(f"/api/orders/{order['id']}").status_code == 404


# ---------- 列表与分页 ----------
def test_list_has_total_count_header(client, order_factory):
    order_factory()
    r = client.get("/api/orders")
    assert int(r.headers["x-total-count"]) >= 1


def test_list_total_matches_items_math(client, order_factory):
    for _ in range(3):
        order_factory()
    r = client.get("/api/orders?limit=2")
    body = r.json()
    assert len(body["items"]) == 2
    assert body["total"] == int(r.headers["x-total-count"])


@pytest.mark.serial  # 数据窗口类断言依赖"全库静止"——并行写入会平移窗口（xdist 下跳过）
def test_list_limit_offset_window(client, order_factory):
    for _ in range(3):
        order_factory()
    page1 = client.get("/api/orders?limit=2&offset=0").json()["items"]
    page2 = client.get("/api/orders?limit=2&offset=2").json()["items"]
    ids1 = {o["id"] for o in page1}
    ids2 = {o["id"] for o in page2}
    assert ids1.isdisjoint(ids2)  # 窗口不重叠


def test_list_orders_desc_by_id(client, order_factory):
    a, b = order_factory(), order_factory()
    items = client.get("/api/orders?limit=5").json()["items"]
    ids = [o["id"] for o in items]
    assert ids == sorted(ids, reverse=True)


def test_list_filter_by_status(client, order_factory):
    o = order_factory()
    client.patch(f"/api/orders/{o['id']}", json={"status": "paid"})
    body = client.get("/api/orders?status=paid").json()
    assert any(x["id"] == o["id"] for x in body["items"])


def test_list_limit_upper_bound_100(client, order_factory):
    r = client.get("/api/orders?limit=1000")
    assert r.status_code == 422  # 超出 le=100 被 pydantic 拦下


# ---------- 负向用例：4xx 家族 ----------
def test_create_missing_field_422(client):
    assert client.post("/api/orders", json={"customer": "a"}).status_code == 422


def test_create_negative_qty_422(client):
    r = client.post("/api/orders", json={
        "customer": "x", "item": "y", "qty": -1, "price": 1})
    assert r.status_code == 422


def test_create_negative_price_422(client):
    r = client.post("/api/orders", json={
        "customer": "x", "item": "y", "qty": 1, "price": -0.5})
    assert r.status_code == 422


def test_create_empty_customer_422(client):
    r = client.post("/api/orders", json={"customer": "", "item": "y", "qty": 1, "price": 1})
    assert r.status_code == 422


def test_patch_illegal_status_400(client, order_factory):
    order = order_factory()
    r = client.patch(f"/api/orders/{order['id']}", json={"status": "flying"})
    assert r.status_code == 400
    assert "非法状态" in r.json()["detail"]


def test_list_illegal_status_filter_400(client):
    assert client.get("/api/orders?status=nope").status_code == 400


def test_404_detail_contains_id(client):
    r = client.get("/api/orders/999999")
    assert "999999" in r.json()["detail"]


# ---------- 登录与角色 ----------
def test_login_ok_returns_token_role(client):
    r = client.post("/api/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200
    assert r.json()["role"] == "admin"
    assert len(r.json()["token"]) >= 16


def test_login_wrong_password_401(client):
    r = client.post("/api/login", json={"username": "admin", "password": "nope"})
    assert r.status_code == 401


def test_admin_stats_requires_admin(client):
    user_login = client.post("/api/login", json={"username": "user", "password": "user123"}).json()
    r = client.get("/api/admin/stats", headers={
        "Authorization": f"Bearer {user_login['token']}"})
    assert r.status_code == 403  # user 角色被拒


def test_admin_stats_with_admin_ok(client):
    admin_login = client.post("/api/login", json={"username": "admin", "password": "admin123"}).json()
    r = client.get("/api/admin/stats", headers={
        "Authorization": f"Bearer {admin_login['token']}"})
    assert r.status_code == 200
    assert "total_orders" in r.json()


def test_admin_stats_without_token_403(client):
    assert client.get("/api/admin/stats").status_code == 403


# ---------- 慢接口：超时预算意识 ----------
def test_slow_config_takes_about_1_5s(client):
    t0 = time.perf_counter()
    r = client.get("/api/slow-config")
    elapsed = time.perf_counter() - t0
    assert r.status_code == 200
    assert 1.4 <= elapsed < 3.0  # 真实测出 SUT 的慢——性能测试前的直觉校准
