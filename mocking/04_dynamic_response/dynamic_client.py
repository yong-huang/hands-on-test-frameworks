#!/usr/bin/env python3
"""动态响应演示客户端：① 100 次请求 → 100 个不重复订单号全过 JSON Schema、
请求参数逐笔回填核对；② 延迟 stub 实测 P95 ≥ 800ms。

每一步自带断言，任何一步不符即退出码 1。
"""
import json
import statistics
import sys
import time
from urllib import error, request

from jsonschema import validate as schema_validate

BASE = "http://127.0.0.1:9400"
FAILURES = []

ORDER_SCHEMA = {
    "type": "object",
    "required": ["order_id", "state", "customer", "amount", "created_at"],
    "properties": {
        "order_id": {"type": "string", "pattern": "^ORD-[a-z0-9]{10}$"},
        "state": {"const": "created"},
        "customer": {"type": "string", "minLength": 1},
        "amount": {"type": "number"},
        "created_at": {"type": "string", "minLength": 1},
    },
}


def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = request.Request(BASE + path, data=data, method=method,
                        headers={"Content-Type": "application/json"})
    try:
        with request.urlopen(r, timeout=15) as resp:
            return resp.status, json.loads(resp.read() or b"null")
    except error.HTTPError as e:
        return e.code, json.loads(e.read() or b"null")


def check(name, ok, detail=""):
    print(f"  {'✅' if ok else '❌'} {name}{(' — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(name)


def uniqueness_and_echo():
    """100 次同 stub 请求：订单号全不重复、全部过 Schema、参数逐笔回填。"""
    print("\n① 同一 stub 连打 100 次：动态生成 + 请求参数回填")
    ids, schema_errors, echo_errors = set(), [], []
    customers = ["alice", "bob", "charlie", "dora", "eve"]
    for i in range(100):
        amount = round(10 + i * 3.7, 2)
        _, body = req("POST", "/orders",
                      {"customer": customers[i % 5], "amount": amount})
        ids.add(body.get("order_id"))
        try:
            schema_validate(body, ORDER_SCHEMA)
        except Exception as e:  # noqa: BLE001 — 单条校验失败记下继续
            schema_errors.append(f"#{i}: {e.message}")
        if body.get("customer") != customers[i % 5] or abs(body.get("amount", 0) - amount) > 1e-9:
            echo_errors.append(i)
    check("100 次返回 100 个不重复订单号", len(ids) == 100, f"去重后 {len(ids)}")
    check("全部响应过 JSON Schema 零错误", not schema_errors,
          f"{len(schema_errors)} 条失败" if schema_errors else "schema: ORD-[a-z0-9]{10}")
    check("customer/amount 逐笔回填正确", not echo_errors,
          f"{len(echo_errors)} 笔不符" if echo_errors else "100 笔全对")

    _, pay = req("POST", "/payments", {"order_id": ids.pop()})
    check("UUID 帮手生成 payment_id", str(pay.get("payment_id", "")).startswith("PAY-")
          and len(pay["payment_id"]) > 20, pay.get("payment_id", "?")[:26] + "…")


def delay_p95():
    """延迟 stub（固定 800ms）连打 20 次，实测 P95 ≥ 800ms。"""
    print("\n② 延迟注入实测：stub 固定延迟 800ms，连打 20 次量 P95")
    samples = []
    for _ in range(20):
        t0 = time.monotonic()
        s, body = req("GET", "/reports/slow")
        samples.append((time.monotonic() - t0) * 1000)
        assert s == 200
    p95 = sorted(samples)[int(0.95 * 20) - 1]
    mean = statistics.mean(samples)
    check(f"P95 ≥ 800ms（实测 {p95:.0f}ms，均值 {mean:.0f}ms）", p95 >= 800)


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else BASE
    globals()["BASE"] = base
    uniqueness_and_echo()
    delay_p95()
    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 项断言失败：{'、'.join(FAILURES)}")
        sys.exit(1)
    print(">>> 验收：100 订单号唯一且过 Schema ✅ 参数回填 ✅ P95 ≥ 800ms ✅")


if __name__ == "__main__":
    main()
