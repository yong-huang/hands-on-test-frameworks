"""消费方测试：断言只到「契约保证的结构」层面——这让它能同时通过挡板与未来
的真实现（provider 换装不动一行）。业务级断言（echo、状态迁移）等 provider
就位后再补，挡板阶段不写挡板做不到的断言——这是 mock-first 的纪律。
"""
import pytest

from consumer_client import ItemsClient


@pytest.fixture(scope="module")
def client():
    return ItemsClient()


def test_health(client):
    """契约：GET /api/health → 200 且含 status 字段。"""
    r = client.health()
    assert r.status_code == 200
    assert "status" in r.json()


def test_create_item_returns_full_item(client):
    """契约：POST /api/items → 201，响应含 id/name/price 三个必填字段。"""
    r = client.create_item("消费方先写测试的商品", 19.9)
    assert r.status_code == 201
    body = r.json()
    assert {"id", "name", "price"} <= set(body)


def test_get_item_roundtrip(client):
    """契约：GET /api/items/{id} → 200 且 id 为整数。"""
    oid = client.create_item("详情商品", 1.0).json()["id"]
    r = client.get_item(oid)
    assert r.status_code == 200
    assert isinstance(r.json()["id"], int)


def test_list_items_shape(client):
    """契约：GET /api/items → 200，items 为数组且 total 为整数。"""
    r = client.list_items()
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body["items"], list)
    assert isinstance(body["total"], int)


def test_delete_item_204(client):
    """契约：DELETE /api/items/{id} → 204。"""
    oid = client.create_item("待删商品", 2.0).json()["id"]
    assert client.delete_item(oid).status_code == 204
