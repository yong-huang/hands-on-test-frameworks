"""契约的忠实实现：contract.yaml 写什么，这里就做什么——一行不越界。

数据在内存字典里（教学够用）；与契约的唯一关系是"行为一致"：
POST /api/items 返回 201 与完整 Item（id/name/price 一个不少），
GET /api/items/{id} 查不到返回契约声明的 404。
"""
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Ministore Items API (good)")
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
    return _ITEMS[iid]


@app.get("/api/items")
def list_items():
    return {"items": list(_ITEMS.values()), "total": len(_ITEMS)}


@app.get("/api/items/{iid}")
def get_item(iid: int):
    item = _ITEMS.get(iid)
    if item is None:
        raise HTTPException(404, f"商品 {iid} 不存在")
    return item


@app.delete("/api/items/{iid}", status_code=204)
def delete_item(iid: int):
    _ITEMS.pop(iid, None)
