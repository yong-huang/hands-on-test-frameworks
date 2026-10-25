#!/usr/bin/env python3
"""Prism 契约驱动 mock 的演示客户端：Schema 校验 / 422 拒绝 / example 优先级。

「独立 schema 校验器」= jsonschema 库 + 契约文件里的响应 schema（客户端用
PyYAML 自取），与 Prism 的内部校验互不依赖——mock 给的应答要经得起契约
之外的第三方核对。
"""
import json
import sys

import httpx
import yaml
from jsonschema import validate as schema_validate

BASE = "http://127.0.0.1:9800"
CONTRACT = "contracts/orders_v1.yaml"
FAILURES = []


def req(method, path, body=None, headers=None):
    r = httpx.request(method, BASE + path, json=body, headers=headers or {},
                      timeout=10, trust_env=False)
    return r.status_code, r.json() if r.content else {}


def check(name, ok, detail=""):
    print(f"  {'✅' if ok else '❌'} {name}{(' — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(name)


def valid_and_schema():
    print("\n① 合法请求全绿 + 响应过独立 Schema 校验（jsonschema + 契约内 schema）")
    contract = yaml.safe_load(open(CONTRACT, encoding="utf-8"))
    resp_schema = (contract["paths"]["/orders"]["post"]["responses"]["201"]
                   ["content"]["application/json"]["schema"])
    schema_errors = 0
    for i, (customer, amount) in enumerate([("alice", 88.5), ("bob", 1200), ("carol", 66)]):
        s, body = req("POST", "/orders", {"customer": customer, "amount": amount})
        if s != 201:
            check(f"合法请求 #{i} → 201", False, f"实际 {s}")
            continue
        try:
            schema_validate(body, resp_schema)
        except Exception as e:  # noqa: BLE001
            schema_errors += 1
            print(f"     ❌ schema: {e.message}")
        if body.get("customer") is not None:
            check(f"合法请求 #{i} → 201", True, f"order_id={body.get('order_id')}")
    check("响应过独立 Schema 校验零错误", schema_errors == 0, f"{schema_errors} 条失败")
    s, body = req("GET", "/orders/ORD-EX-0001")
    check("GET /orders/{id} → 200", s == 200 and body.get("state") == "created",
          f"state={body.get('state')}")


def prefer_example():
    print("\n② example 优先级：Prefer 头切换同一 201 的两套示例")
    _, default_body = req("POST", "/orders", {"customer": "alice", "amount": 88.5})
    _, risk_body = req("POST", "/orders", {"customer": "alice", "amount": 88.5},
                       {"Prefer": "example=risk-review"})
    check("默认取第一个 example（review=false）", default_body.get("review") is False,
          f"order_id={default_body.get('order_id')}")
    check("Prefer: example=risk-review 切到第二套（review=true）",
          risk_body.get("review") is True, f"order_id={risk_body.get('order_id')}")


def invalid_rejected():
    print("\n③ 非法请求拒绝：缺字段 / 错类型都被 422 拦在门外")
    s, body = req("POST", "/orders", {"customer": "alice"})
    check("缺 amount → 422", s == 422, str(body.get("title", "")))
    s, body = req("POST", "/orders", {"customer": "alice", "amount": "不是数字"})
    check("amount 错类型 → 422", s == 422, str(body.get("title", "")))
    detail = json.dumps(body, ensure_ascii=False)[:90]
    print(f"     · Prism 的拒绝理由（节选）：{detail}…")
    check("拒绝理由指向具体违规字段", "amount" in json.dumps(body, ensure_ascii=False))


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else BASE
    globals()["BASE"] = base
    valid_and_schema()
    prefer_example()
    invalid_rejected()
    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 项断言失败：{'、'.join(FAILURES)}")
        sys.exit(1)
    print(">>> 验收：合法全绿过独立 Schema ✅ example 优先级 ✅ 非法请求 422 ✅")


if __name__ == "__main__":
    main()
