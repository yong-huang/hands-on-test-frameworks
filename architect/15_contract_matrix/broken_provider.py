#!/usr/bin/env python3
"""broken_provider.py — v2 破坏变体：在真 SUT 外面套一层「改字段名」的 ASGI 中间件。

模拟真实世界最常见的契约破坏：provider 重构把 customer 改名 clientName，
consumer 完全知情却没人通知——契约测试存在的意义就是让这种事在发布前爆掉。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "labs" / "11_sut_app" / "app"))

import main as sut  # noqa: E402  SUT 的 FastAPI app


@sut.app.middleware("http")
async def break_contract(request, call_next):
    response = await call_next(request)
    if "application/json" in (response.headers.get("content-type") or ""):
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        try:
            data = json.loads(body)
            data = _rename(data)
            body = json.dumps(data, ensure_ascii=False).encode()
        except Exception:
            pass
        async def _stream():
            yield body
        response.body_iterator = _stream()
        response.headers["content-length"] = str(len(body))
    return response


def _rename(obj):
    if isinstance(obj, dict):
        return {("clientName" if k == "customer" else k): _rename(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_rename(x) for x in obj]
    return obj


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(sut.app, host="127.0.0.1", port=8902, log_level="warning")
