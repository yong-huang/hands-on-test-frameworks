"""SUT 应用入口：FastAPI 订单管理。

这是后续 19 个实验的公共被测对象，接口契约务必稳定：
  POST   /api/orders          创建订单 → 201 + Location
  GET    /api/orders          列表（status/limit/offset 分页）→ 200 + X-Total-Count
  GET    /api/orders/{id}     详情 → 200 / 404
  PATCH  /api/orders/{id}     改状态 → 200 / 400（非法状态）/ 404
  DELETE /api/orders/{id}     删除 → 204 / 404
  POST   /api/login           演示登录（admin/admin123、user/user123）→ {token, role}
  GET    /api/config          慢接口（sleep 1.5s，lab 17 等待训练专用）
  GET    /                    静态下单页
启动：uvicorn main:app --port 8899（在 app/ 目录下）
"""
import os
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Query, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import store

DB_PATH = Path(os.environ.get("SUT_DB", Path(__file__).parent / "orders.db"))
STATIC_DIR = Path(__file__).parent / "static"

VALID_STATUS = {"created", "paid", "shipped", "cancelled"}
TOKENS: dict[str, str] = {}  # token -> role（内存态，重启即失效——教学够用）


@asynccontextmanager
async def lifespan(_: FastAPI):
    store.init_db(DB_PATH)  # 启动即建表，幂等
    yield


app = FastAPI(title="Ministore Orders API", version="1.0.0", lifespan=lifespan)


class OrderIn(BaseModel):
    customer: str = Field(min_length=1, max_length=40)
    item: str = Field(min_length=1, max_length=80)
    qty: int = Field(gt=0)
    price: float = Field(ge=0)


class StatusIn(BaseModel):
    status: str


class LoginIn(BaseModel):
    username: str
    password: str


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "ministore", "version": "1.0.0"}


@app.post("/api/orders", status_code=201)
def create_order(order: OrderIn, response: Response):
    created = store.create_order(DB_PATH, order.customer, order.item, order.qty, order.price)
    response.headers["Location"] = f"/api/orders/{created['id']}"
    return created


@app.get("/api/orders")
def list_orders(
    status: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    response: Response = None,
):
    if status and status not in VALID_STATUS:
        raise HTTPException(400, f"非法状态: {status}，可选 {sorted(VALID_STATUS)}")
    items, total = store.list_orders(DB_PATH, status, limit, offset)
    response.headers["X-Total-Count"] = str(total)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@app.get("/api/orders/{order_id}")
def get_order(order_id: int):
    order = store.get_order(DB_PATH, order_id)
    if order is None:
        raise HTTPException(404, f"订单 {order_id} 不存在")
    return order


@app.patch("/api/orders/{order_id}")
def update_order(order_id: int, body: StatusIn):
    if body.status not in VALID_STATUS:
        raise HTTPException(400, f"非法状态: {body.status}，可选 {sorted(VALID_STATUS)}")
    updated = store.update_status(DB_PATH, order_id, body.status)
    if updated is None:
        raise HTTPException(404, f"订单 {order_id} 不存在")
    return updated


@app.delete("/api/orders/{order_id}", status_code=204)
def delete_order(order_id: int):
    if not store.delete_order(DB_PATH, order_id):
        raise HTTPException(404, f"订单 {order_id} 不存在")
    return Response(status_code=204)


@app.post("/api/login")
def login(body: LoginIn):
    users = {"admin": "admin123", "user": "user123"}
    if users.get(body.username) != body.password:
        raise HTTPException(401, "用户名或密码错误")
    token = secrets.token_hex(16)
    role = "admin" if body.username == "admin" else "user"
    TOKENS[token] = role
    return {"token": token, "role": role}


@app.get("/api/admin/stats")
def admin_stats(authorization: str = Header(default="")):
    """admin 专属端点：lab 19/22 的双角色会话用它验证'不串号'"""
    token = authorization.removeprefix("Bearer ").strip()
    if TOKENS.get(token) != "admin":
        raise HTTPException(403, "需要 admin 角色")
    orders, total = store.list_orders(DB_PATH, limit=1, offset=0)
    return {"total_orders": total, "role": "admin"}


@app.get("/api/slow-config")
def slow_config():
    """故意慢 1.5s：lab 17 训练'等待'的靶子"""
    time.sleep(1.5)
    return {"theme": "dark", "banner": "welcome", "loaded_after_ms": 1500}


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
