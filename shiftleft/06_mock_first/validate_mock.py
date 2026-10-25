#!/usr/bin/env python3
"""validate_mock.py —— 验收③：挡板的每个响应逐一对契约 schema 校验，零错误才放行。

做法：对契约里每个操作构造一次真实请求（路径参数用 1，POST 体从请求 schema
生成示例），拿到 2xx 响应后用 jsonschema 按该操作声明的响应 schema 校验。
$ref 通过 RefResolver 挂整份契约解析。
"""
import json
import sys
from pathlib import Path

import httpx
import yaml
from jsonschema import Draft202012Validator, RefResolver

ROOT = Path(__file__).resolve().parent
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8934"
SPEC = yaml.safe_load((ROOT / "configs/contract.yaml").read_text())
resolver = RefResolver.from_schema(SPEC)  # $ref 解析挂整份契约


def gen_example(schema: dict) -> object:
    """与 mock_server 同源的示例生成（校验方独立实现一遍，防「自己校验自己」）。"""
    if "$ref" in schema:
        node = SPEC
        for part in schema["$ref"].lstrip("#/").split("/"):
            node = node[part]
        return gen_example(node)
    t = schema.get("type")
    if t == "object":
        return {k: gen_example(s) for k, s in schema.get("properties", {}).items()
                if k in schema.get("required", [])}
    if t == "array":
        return [gen_example(schema.get("items", {}))]
    if t == "integer":
        return 1
    if t == "number":
        return 9.9
    if t == "boolean":
        return True
    return "validate"


def main():
    client = httpx.Client(base_url=BASE, timeout=10)
    errors = 0
    for cpath, item in SPEC["paths"].items():
        for method, op in item.items():
            success = next((c for c in op["responses"] if c.startswith("2")), None)
            if success is None:
                continue
            kwargs = {}
            real_path = cpath
            if method == "post":
                body_schema = (op.get("requestBody", {}).get("content", {})
                               .get("application/json", {}).get("schema"))
                if body_schema:
                    kwargs["json"] = gen_example(body_schema)
            media = op["responses"][success].get("content", {}).get("application/json", {})
            schema = media.get("schema")
            r = client.request(method.upper(), real_path, **kwargs)
            label = f"{method.upper()} {cpath} → {r.status_code}"
            if r.status_code >= 300:
                print(f"⛔ {label}：非 2xx，挡板没按契约给成功响应")
                errors += 1
                continue
            if schema is None:
                print(f"✅ {label}：204 无响应体，无需校验")
                continue
            v = Draft202012Validator(schema, resolver=resolver)
            fails = list(v.iter_errors(r.json()))
            if fails:
                errors += 1
                print(f"⛔ {label}：{len(fails)} 处 schema 违规——{fails[0].message[:80]}")
            else:
                print(f"✅ {label}：响应符合契约 schema")
    print(f"\n校验结论：{'零错误，挡板结构合法（exit 0）' if errors == 0 else f'{errors} 个操作违规（exit 1）'}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
