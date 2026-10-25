#!/usr/bin/env python3
"""等价对账引擎：同一份 10 场景请求序列分别打 自研声明式 mock 与 WireMock，
逐字段比对 status / X-Mocked-By / JSON body；再演示 WireMock verify 抓未预期请求。

两实现的 404 语义刻意不同（自研=带诊断 body，WireMock=空 body），
所以 404 场景只对账状态码，body 差异记入能力差距表而非算失败。
"""
import json
import sys
from urllib import error, request

FAILURES = []


def req(base, method, path, body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    r = request.Request(base + path, data=data, method=method,
                        headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with request.urlopen(r, timeout=10) as resp:
            raw = resp.read()
            return resp.status, dict(resp.headers), raw
    except error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


def parse_json(raw):
    try:
        return json.loads(raw or b"null")
    except json.JSONDecodeError:
        return None


def check(name, ok, detail=""):
    print(f"  {'✅' if ok else '❌'} {name}{(' — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(name)


# (说明, method, path, body, headers, 期望状态, 期望命中的 stub)
SCENARIOS = [
    ("兜底弱规则",        "POST", "/orders",   {"amount": 50},    {},                        201, "order-any"),
    ("POS 渠道头",        "POST", "/orders",   {"amount": 50},    {"X-Channel": "pos"},      201, "order-pos-channel"),
    ("大额订单体",        "POST", "/orders",   {"amount": 5000},  {},                        201, "order-big-amount"),
    ("POS 头 + 大额体",   "POST", "/orders",   {"amount": 5000},  {"X-Channel": "pos"},      201, "order-pos-big"),
    ("边界 amount=1000",  "POST", "/orders",   {"amount": 1000},  {},                        201, "order-any"),
    ("web 渠道（非 pos）", "POST", "/orders",   {"amount": 5000},  {"X-Channel": "web"},      201, "order-big-amount"),
    ("Visa 直通",         "POST", "/payments", {"card_token": "tok_visa"}, {"Idempotency-Key": "K-1"}, 200, "pay-visa-fast"),
    ("Amex 复核",         "POST", "/payments", {"card_token": "tok_amex"}, {"Idempotency-Key": "K-2"}, 200, "pay-other-review"),
    ("缺幂等键",          "POST", "/payments", {"card_token": "tok_visa"}, {},                        404, None),
    ("未建 stub 的路径",   "DELETE", "/orders/42", None,           {},                        404, None),
]


def equivalence(base_a, base_b):
    print("\n① 等价对账：10 个场景，自研 vs WireMock 逐字段比对")
    for i, (desc, m, p, body, hs, want_status, want_stub) in enumerate(SCENARIOS, 1):
        sa, ha, ba = req(base_a, m, p, body, hs)
        sb, hb, bb = req(base_b, m, p, body, hs)
        ja, jb = parse_json(ba), parse_json(bb)

        ok = sa == sb == want_status
        detail = f"status {sa}/{sb}"
        if want_stub is not None:  # 命中场景：三重对账
            got_a, got_b = ha.get("X-Mocked-By"), hb.get("X-Mocked-By")
            ok = ok and got_a == got_b == want_stub
            ok = ok and ja == jb
            detail += f" stub {got_a}/{got_b} body{'=' if ja == jb else '≠'}"
        else:  # 404 场景：状态码对账，body 语义差异是已知差距
            detail += "（404 body 语义差异见差距表）"
        check(f"[{i:>2}] {desc}", ok, detail)


def verify_unmatched(base_b):
    """WireMock 把每个请求留痕：/__admin/requests?unmatched=true 查『没被任何 stub 接住』的请求。"""
    print("\n② verify 断言：抓出一次未被任何 stub 预期的真实请求")
    req(base_b, "DELETE", "/orders/42")  # 制造一次未预期请求（场景 10 的重放）
    with request.urlopen(base_b + "/__admin/requests?unmatched=true", timeout=10) as r:
        found = json.loads(r.read())
    items = found.get("requests", [])
    hit = any(x["request"]["method"] == "DELETE" and x["request"]["url"] == "/orders/42"
              for x in items)
    check("DELETE /orders/42 出现在 unmatched 留痕", hit, f"unmatched 共 {len(items)} 条")
    if items:
        print("     · WireMock 记录的未预期请求（节选）：")
        print("       " + json.dumps(items[0]["request"], ensure_ascii=False)[:110] + " …")


def main():
    base_a = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:9110"
    base_b = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:9200"
    equivalence(base_a, base_b)
    verify_unmatched(base_b)
    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 项失败：{'、'.join(FAILURES)}")
        sys.exit(1)
    print(">>> 验收：10 场景逐字段等价 ✅ verify 抓到未预期请求 ✅")


if __name__ == "__main__":
    main()
