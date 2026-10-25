"""被篡改的实现（实验道具，勿模仿）：两处违反 contract.yaml 的植入缺陷。

缺陷 A（响应缺字段）：POST /api/items 的响应漏掉契约必填的 price——
                  response_schema_conformance 检查每次 POST 都会命中。
缺陷 B（未声明的状态码）：GET /api/items/{id} 查不存在时返回 400，
                  而契约只声明了 200/404——status_code_conformance 命中。
真实世界对应：重构时顺手"优化"了响应结构、错误处理改了码没人通知契约。
"""
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Ministore Items API (bad)")
_ITEMS: dict[int, dict] = {}


class ItemIn(BaseModel):
    name: str = Field(min_length=1)
    price: float = Field(ge=0)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/items", status_code=201)
def create_item(body: ItemIn):
    iid = abs(hash(uuid.uuid4())) % 10_000_000
    _ITEMS[iid] = {"id": iid, "name": body.name, "price": body.price}
    # 缺陷 A：漏掉 price 字段
    return {"id": iid, "name": body.name}


@app.get("/api/items")
def list_items():
    return {"items": list(_ITEMS.values()), "total": len(_ITEMS)}


@app.get("/api/items/{iid}")
def get_item(iid: int):
    item = _ITEMS.get(iid)
    if item is None:
        # 缺陷 B：400 未在契约中声明
        raise HTTPException(400, f"商品 {iid} 不存在")
    return item


@app.delete("/api/items/{iid}", status_code=204)
def delete_item(iid: int):
    _ITEMS.pop(iid, None)
