#!/usr/bin/env python3
"""GraphQL mock：schema 感知 + AB 场景切换 + 字段级结构化错误。

三块积木：
- schema 感知：SDL 由 graphql-core 加载，schema 外字段在执行前就被校验拒绝
  （200 + errors，而非 500）
- AB 场景：请求头 X-Mock-Scene: a|b 经 context 传进 resolver，同一 query
  返回两套预设数据——切换开关是请求的一部分，不是服务端配置
- 字段级错误：riskyOrder 的 resolver 故意抛错，错误带 path 定位到字段
"""
from pathlib import Path

from ariadne import QueryType, make_executable_schema
from ariadne.asgi import GraphQL

type_defs = (Path(__file__).parent / "schema.graphql").read_text(encoding="utf-8")

DATA = {
    "a": {"order": {"id": "ORD-A-1", "customer": "alice", "amount": 100.0,
                    "status": "created", "review": False},
          "orders": [{"id": "ORD-A-1", "customer": "alice", "amount": 100.0,
                      "status": "created", "review": False},
                     {"id": "ORD-A-2", "customer": "bob", "amount": 55.0,
                      "status": "created", "review": False}]},
    "b": {"order": {"id": "ORD-B-1", "customer": "alice", "amount": 9999.0,
                    "status": "created", "review": True},
          "orders": [{"id": "ORD-B-1", "customer": "alice", "amount": 9999.0,
                      "status": "created", "review": True}]},
}

query = QueryType()


def _scene(info) -> str:
    """从请求头取场景开关；未知值回落 a。

    Ariadne ASGI 的默认 context 是 {"request": Request, ...} 字典——
    场景开关从真实 Request 的头里取。
    """
    ctx = info.context
    request = ctx["request"] if isinstance(ctx, dict) else ctx
    return (request.headers.get("x-mock-scene") or "a").lower()


@query.field("order")
def resolve_order(_, info, id):
    return DATA[_scene(info)]["order"]


@query.field("orders")
def resolve_orders(_, info, limit=5):
    return DATA[_scene(info)]["orders"][:limit]


@query.field("riskyOrder")
def resolve_risky(_, info):
    raise RuntimeError("风控数据不可用（mock 注入的字段级错误）")


schema = make_executable_schema(type_defs, query)
app = GraphQL(schema)


async def serve(scope, receive, send):  # ASGI 入口：只挂 /graphql
    if scope["type"] == "http" and scope["path"] != "/graphql":
        await send({"type": "http.response.start", "status": 404,
                    "headers": [(b"content-type", b"application/json")]})
        await send({"type": "http.response.body", "body": b'{"error":"use /graphql"}'})
        return
    await app(scope, receive, send)
