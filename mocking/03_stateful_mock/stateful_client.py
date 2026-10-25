#!/usr/bin/env python3
"""状态机演示客户端：happy path 流转 → 终态断言 → 非法跳转全表 → 重置复用。

被测对象是 WireMock scenario（order-lifecycle）：同一 URL 的应答由当前
状态决定。每一步都自带断言；非法跳转额外断言「拒绝不改状态」。
"""
import json
import sys
from urllib import error, request

BASE = "http://127.0.0.1:9300"
FAILURES = []


def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = request.Request(BASE + path, data=data, method=method,
                        headers={"Content-Type": "application/json"})
    try:
        with request.urlopen(r, timeout=10) as resp:
            return resp.status, json.loads(resp.read() or b"null")
    except error.HTTPError as e:
        return e.code, json.loads(e.read() or b"null")


def check(name, ok, detail=""):
    print(f"  {'✅' if ok else '❌'} {name}{(' — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(name)


def scenario_state():
    return req("GET", "/orders/state")[1].get("state")


def reset():
    # 注意：WireMock 3.13 没有 /__admin/scenarios/{name}/reset（实测 404），
    # 只有全量重置端点——本实验单场景，语义等价
    req("POST", "/__admin/scenarios/reset")


def happy_path(verbose=True):
    """合法三步：创建→支付→发货，每步后查状态断言流转。"""
    steps = [
        ("POST", "/orders", 201, "created", "order_id"),
        ("POST", "/orders/pay", 200, "paid", "payment_id"),
        ("POST", "/orders/ship", 200, "shipped", "tracking_no"),
    ]
    for method, path, want_status, want_state, key in steps:
        status, body = req(method, path)
        state = scenario_state()
        ok = status == want_status and state == want_state and key in body
        if verbose:
            check(f"{method} {path} → {status}，场景状态 = {state}",
                  ok, f"{key}={body.get(key)}")
        if not ok:
            return False
    return True


def terminal_assert():
    print("\n② 终态断言：SHIPPED 是终点，发货后一切写操作都该被拒")
    status, body = req("POST", "/orders/ship")
    check("ship@SHIPPED → 409", status == 409 and body.get("code") == "DUPLICATE_SHIP",
          body.get("error", ""))
    check("终态不被非法请求改写", scenario_state() == "shipped")


def illegal_table():
    """9 个非法跳转逐格核对：reset → 合法前缀 → 非法动作 → 409 + code + 状态不变。"""
    print("\n③ 非法跳转全表：4 态 × 3 动作里除 3 个合法转移外的 9 格")
    prefix_actions = [("POST", "/orders"), ("POST", "/orders/pay"), ("POST", "/orders/ship")]
    cells = [
        # (动作, 前缀步数, 期望所在态, 期望业务码)
        ("POST", "/orders",      1, "created", "DUPLICATE_ORDER"),
        ("POST", "/orders",      2, "paid",    "ALREADY_PAID"),
        ("POST", "/orders",      3, "shipped", "ORDER_CLOSED"),
        ("POST", "/orders/pay",  0, "empty",   "NO_ORDER"),
        ("POST", "/orders/pay",  2, "paid",    "DUPLICATE_PAY"),
        ("POST", "/orders/pay",  3, "shipped", "ORDER_CLOSED"),
        ("POST", "/orders/ship", 0, "empty",   "NO_ORDER"),
        ("POST", "/orders/ship", 1, "created", "NOT_PAID"),
        ("POST", "/orders/ship", 3, "shipped", "DUPLICATE_SHIP"),
    ]
    for method, path, prefix_len, state_name, want_code in cells:
        reset()
        for m, p in prefix_actions[:prefix_len]:
            req(m, p)
        before = scenario_state()
        status, body = req(method, path)
        after = scenario_state()
        ok = (status == 409 and body.get("code") == want_code
              and before == after == state_name)
        prefix_desc = "→".join(f"{m} {p}" for m, p in prefix_actions[:prefix_len]) or "（无前置）"
        check(f"{method} {path} @ {state_name} → 409 {want_code}", ok,
              f"前缀: {prefix_desc}；拒绝后状态仍为 {after}")
    return True


def reset_reuse():
    print("\n④ 重置复用：admin API 一键回 Started，状态机可以反复用")
    reset()
    check("reset 后场景状态回到 empty", scenario_state() == "empty",
          f"实际 {scenario_state()}")
    check("重置后 happy path 复跑全绿", happy_path(verbose=False))


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else BASE
    globals()["BASE"] = base
    print("① happy path：创建→支付→发货，同一 URL 每步应答随状态变化")
    happy_path()
    terminal_assert()
    illegal_table()
    reset_reuse()
    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 项断言失败：{'、'.join(FAILURES)}")
        sys.exit(1)
    print(">>> 验收：状态流转 ✅ 终态拒绝 ✅ 9 格非法跳转全拒 ✅ 重置可复用 ✅")


if __name__ == "__main__":
    main()
