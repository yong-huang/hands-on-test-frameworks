#!/usr/bin/env python3
"""degrade_canary.py — canary 实例包装器：可在进程外注入劣化（错误率/延迟）。

真 SUT 原样包一层中间件：ERR_RATE=0 即健康 canary；ERR_RATE=0.2 LAT_MS=300 即劣化
实例。劣化在进程边界注入——被测对象（判定器）看到的就是「一个变差的 canary」。
"""
import asyncio
import json
import os
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "labs" / "11_sut_app" / "app"))
import main as sut  # noqa: E402

ERR_RATE = float(os.environ.get("ERR_RATE", "0"))
LAT_MS = int(os.environ.get("LAT_MS", "0"))


@sut.app.middleware("http")
async def degrade(request, call_next):
    if LAT_MS:
        await asyncio.sleep(LAT_MS / 1000)
    if ERR_RATE and random.random() < ERR_RATE:
        body = json.dumps({"error": f"canary degraded (rate={ERR_RATE})"}).encode()
        return __import__("starlette.responses", fromlist=["Response"]).Response(
            body, status_code=500, media_type="application/json")
    return await call_next(request)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(sut.app, host="127.0.0.1", port=int(os.environ.get("PORT", "8903")),
                log_level="warning")
