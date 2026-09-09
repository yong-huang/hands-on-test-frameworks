"""perf-shop 修复版（lab 34 产物）：三处缺陷全部治理。

- D1 N+1 → 一条 JOIN 带回库存
- D2 打分 → 预计算入库（启动时算一次，请求路径零 CPU）
- D3 假风控 sleep → 移除，下单路径只剩纯 DB 写
"""
import os
from contextlib import contextmanager

import psycopg
from psycopg_pool import ConnectionPool
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "host=postgres port=5432 dbname=shop user=shop password=shop",
)

pool = ConnectionPool(DATABASE_URL, min_size=2, max_size=10, open=True, name="shop-pool")

app = FastAPI(title="perf-shop")
Instrumentator().instrument(app).expose(app)  # GET /metrics


@contextmanager
def get_conn():
    with pool.connection() as conn:
        yield conn


@app.on_event("startup")
def precompute_scores():
    """D2 修复：推荐打分是纯派生数据，在启动时算一次写库，请求路径不再付 CPU。"""
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO recommend_scores (product_id, score)
            SELECT id,
                   ('x' || md5(id::text))::bit(16)::int  -- 便宜且确定的打分
            FROM products
            ON CONFLICT (product_id) DO UPDATE SET score = EXCLUDED.score
            """
        )


@app.get("/health")
def health():
    with get_conn() as conn:
        conn.execute("SELECT 1")
    return {"status": "ok"}


@app.get("/api/products")
def list_products(limit: int = 50, offset: int = 0):
    """D1 修复：一条 JOIN 带回库存，51 条 SQL → 1 条。"""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT p.id, p.name, p.price, COALESCE(s.qty, 0)
            FROM products p LEFT JOIN stock s ON s.product_id = p.id
            ORDER BY p.id LIMIT %s OFFSET %s
            """,
            (min(limit, 200), offset),
        ).fetchall()
    items = [{"id": r[0], "name": r[1], "price": r[2], "stock": r[3]} for r in rows]
    return {"items": items, "total": len(items)}


@app.get("/api/products/{pid}")
def product_detail(pid: int):
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT p.id, p.name, p.price, COALESCE(r.score, 0)
            FROM products p LEFT JOIN recommend_scores r ON r.product_id = p.id
            WHERE p.id = %s
            """,
            (pid,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="product not found")
    return {"id": row[0], "name": row[1], "price": row[2], "recommend_score": row[3]}


class OrderIn(BaseModel):
    user_id: int
    product_id: int
    qty: int = 1


@app.post("/api/orders", status_code=201)
def create_order(order: OrderIn):
    """D3 修复：假风控已移除；真实场景应异步化（消息队列），而非同步 sleep。"""
    with get_conn() as conn:
        row = conn.execute(
            "UPDATE stock SET qty = qty - %s WHERE product_id = %s AND qty >= %s RETURNING qty",
            (order.qty, order.product_id, order.qty),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=409, detail="insufficient stock")
        order_id = conn.execute(
            "INSERT INTO orders (user_id, product_id, qty) VALUES (%s, %s, %s) RETURNING id",
            (order.user_id, order.product_id, order.qty),
        ).fetchone()
    return {"order_id": order_id[0]}
