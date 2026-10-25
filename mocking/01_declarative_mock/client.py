#!/usr/bin/env python3
"""演示客户端：四档特异度阶梯 → 支付正反例 → 响亮未命中 → 并发正确性 → 统计。

每一步都自带断言，任何一步不符合预期即退出码 1——观察输出本身是验收。
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from urllib import error, request

BASE = "http://127.0.0.1:9100"
FAILURES = []


def req(method, path, body=None, headers=None):
    """发一个请求，返回 (status, response_headers, 解析后的 body 或 None)。"""
    data = json.dumps(body).encode() if body is not None else None
    r = request.Request(BASE + path, data=data, method=method,
                        headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with request.urlopen(r, timeout=10) as resp:
            return resp.status, dict(resp.headers), json.loads(resp.read() or b"null")
    except error.HTTPError as e:  # 404 等非 2xx 也要拿到 body 做诊断展示
        return e.code, dict(e.headers), json.loads(e.read() or b"null")


def check(name, ok, detail=""):
    print(f"  {'✅' if ok else '❌'} {name}{(' — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(name)


def ladder():
    """同一 URL 四档特异度：约束越细的规则应答，分数严格递增。"""
    print("\n① 特异度阶梯：同一个 POST /orders，四份请求四种应答")
    cases = [  # (说明, headers, body, 期望命中 stub, 期望分数)
        ("无附加条件",       {},                       {"amount": 50},   "order-any",         0),
        ("POS 渠道头",       {"X-Channel": "pos"},     {"amount": 50},   "order-pos-channel", 10),
        ("大额订单体",       {},                       {"amount": 5000}, "order-big-amount",  20),
        ("POS 头 + 大额体",  {"X-Channel": "pos"},     {"amount": 5000}, "order-pos-big",     30),
    ]
    prev_score = -1
    for desc, hs, body, want_stub, want_score in cases:
        status, hdrs, resp = req("POST", "/orders", body, hs)
        got, score = hdrs.get("X-Mocked-By"), int(hdrs.get("X-Match-Score", -1))
        check(f"{desc} → {got}（{score} 分）", got == want_stub and score == want_score,
              f"state={resp.get('state')} review={resp.get('review')}")
        check(f"{desc} 分数严格递增", score > prev_score,
              f"{prev_score} → {score}")
        prev_score = score


def payments():
    print("\n② 支付规则：Visa 直通、其他卡复核、缺幂等键响亮未命中")
    s, h, b = req("POST", "/payments", {"card_token": "tok_visa"},
                  {"Idempotency-Key": "K-1"})
    check("Visa + 幂等键 → 直通", h.get("X-Mocked-By") == "pay-visa-fast"
          and b.get("state") == "settled", f"score={h.get('X-Match-Score')}")
    s, h, b = req("POST", "/payments", {"card_token": "tok_amex"},
                  {"Idempotency-Key": "K-2"})
    check("Amex + 幂等键 → 复核", h.get("X-Mocked-By") == "pay-other-review"
          and b.get("state") == "under_review", f"score={h.get('X-Match-Score')}")
    s, h, b = req("POST", "/payments", {"card_token": "tok_visa"})
    reasons = [c["reason"] for c in b.get("candidates", [])]
    check("缺幂等键 → 404 响亮未命中", s == 404 and b.get("error") == "no_stub_matched",
          f"{len(reasons)} 条候选规则各自说明了失败原因")
    for r in reasons:
        print(f"     · {r}")
    check("404 带逐条失败诊断", len(reasons) == 2, "两条支付规则都在候选里")


def concurrent():
    """50 线程 × 20 轮 × 6 模板 = 1000 请求：并发下「谁应答」也必须确定。"""
    print("\n③ 并发正确性：50 线程 × 20 轮，1000 个请求零错答")
    templates = [
        ("POST", "/orders", {"amount": 50}, {}, "order-any"),
        ("POST", "/orders", {"amount": 50}, {"X-Channel": "pos"}, "order-pos-channel"),
        ("POST", "/orders", {"amount": 5000}, {}, "order-big-amount"),
        ("POST", "/orders", {"amount": 5000}, {"X-Channel": "pos"}, "order-pos-big"),
        ("POST", "/payments", {"card_token": "tok_visa"}, {"Idempotency-Key": "K"}, "pay-visa-fast"),
        ("POST", "/payments", {"card_token": "tok_amex"}, {"Idempotency-Key": "K"}, "pay-other-review"),
    ]

    def one(i):
        m, p, body, hs, want = templates[i % len(templates)]
        s, h, _ = req(m, p, body, hs)
        return h.get("X-Mocked-By") == want and s in (200, 201)

    with ThreadPoolExecutor(max_workers=50) as pool:
        results = list(pool.map(one, range(1000)))
    check("1000 并发请求全部命中预期规则", all(results),
          f"{results.count(False)} 个错答/失败")


def stats():
    print("\n④ 命中统计：每条规则的应答次数与未命中数")
    _, _, st = req("GET", "/__stats__")
    print("  " + json.dumps(st, ensure_ascii=False))
    # 模板按全局索引 i%6 轮转：1000 = 6×166 + 4，前 4 个模板 167 次、后 2 个 166 次；
    # 加上 ①② 顺序部分的每模板 1 次，得各规则总计数
    expect = {"order-any": 168, "order-pos-channel": 168, "order-big-amount": 168,
              "order-pos-big": 168, "pay-visa-fast": 167, "pay-other-review": 167}
    check("hits = 4+2+1000 = 1006", st.get("hits") == 1006, f"实际 {st.get('hits')}")
    check("misses = 1（只响过一次 404）", st.get("misses") == 1, f"实际 {st.get('misses')}")
    check("逐规则计数与模板分布一致", st.get("by_stub") == expect,
          "" if st.get("by_stub") == expect else f"实际 {st.get('by_stub')}")


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else BASE
    globals()["BASE"] = base
    ladder()
    payments()
    concurrent()
    stats()
    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 项断言失败：{'、'.join(FAILURES)}")
        sys.exit(1)
    print(">>> 验收：阶梯胜出 ✅ 未命中响亮 ✅ 并发零错答 ✅ 统计对账 ✅")


if __name__ == "__main__":
    main()
