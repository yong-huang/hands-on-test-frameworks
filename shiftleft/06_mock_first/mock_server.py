#!/usr/bin/env python3
"""mock_server.py —— 从契约动态生成的挡板服务：provider 还不存在，消费方先开发。

「从契约生成」的含义：本文件不写死任何业务路由——启动时解析 contract.yaml，
用一个 catch-all 路由接住所有请求，按 方法+路径 模板匹配到契约操作，再从该
操作的成功响应 schema 递归生成合法示例响应。契约加接口，挡板自动跟上。

挡板语义（消费方测试必须按此写作）：
  - 只保证「结构符合契约」：字段齐全、类型正确，不保证业务状态（无记忆）。
  - 错误注入：请求头 X-Mock-Fault: 500 → 返回该状态码（演练消费方的容错分支）。
  - 延迟注入：请求头 X-Mock-Delay: 2 → 睡 2 秒（演练超时与重试）。

用法：python mock_server.py [--port 8934]
"""
import json
import re
import time
from pathlib import Path

import uvicorn
import yaml
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

ROOT = Path(__file__).resolve().parent
SPEC = yaml.safe_load((ROOT / "configs/contract.yaml").read_text())
app = FastAPI(title="contract-first mock (从契约动态生成)")


def resolve_ref(schema: dict) -> dict:
    """解析 $ref（本契约只用了 #/components/schemas/... 一种形态）。"""
    ref = schema.get("$ref")
    if not ref:
        return schema
    node = SPEC
    for part in ref.lstrip("#/").split("/"):
        node = node[part]
    return node


def gen_example(schema: dict) -> object:
    """按 schema 递归生成一个合法示例值——挡板「结构合法」的根基。"""
    schema = resolve_ref(schema)
    if "enum" in schema:
        return schema["enum"][0]
    t = schema.get("type")
    if t == "object":
        return {k: gen_example(sub) for k, sub in schema.get("properties", {}).items()
                if k in schema.get("required", []) or len(schema.get("required", [])) == 0}
    if t == "array":
        return [gen_example(schema.get("items", {}))]
    if t == "integer":
        return 1
    if t == "number":
        return 9.9
    if t == "boolean":
        return True
    return f"mock-{schema.get('title', 'string')}"  # string 及未声明类型兜底


def find_operation(method: str, path: str):
    """把契约的路径模板编译成正则，找到 方法+路径 对应的操作。"""
    for cpath, item in SPEC["paths"].items():
        m = method.lower()
        if m not in item:
            continue
        pattern = re.sub(r"\{(\w+)\}", r"[^/]+", cpath)  # {id} → 任意非斜杠段
        if re.fullmatch(pattern, path):
            return item[m]
    return None


def success_response(op: dict) -> tuple[int, dict | None]:
    """取操作的第一个 2xx 响应：返回 (状态码, JSON schema 或 None[如 204])。"""
    for code, resp in op["responses"].items():
        if code.startswith("2"):
            media = resp.get("content", {}).get("application/json", {})
            return int(code), media.get("schema")
    return 204, None


@app.api_route("/{api_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def mock_handler(api_path: str, request: Request):
    delay = request.headers.get("x-mock-delay")
    if delay:
        time.sleep(float(delay))
    fault = request.headers.get("x-mock-fault")
    if fault:
        return JSONResponse(status_code=int(fault),
                            content={"detail": f"mock 注入错误 {fault}"})
    op = find_operation(request.method, "/" + api_path)
    if op is None:
        return JSONResponse(status_code=501,
                            content={"detail": f"契约未定义 {request.method} {request.url.path}"})
    status, schema = success_response(op)
    if status == 204 or schema is None:
        return Response(status_code=status)
    return JSONResponse(status_code=status, content=gen_example(schema))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=int(__import__("os").environ.get("MOCK_PORT", "8934")))
