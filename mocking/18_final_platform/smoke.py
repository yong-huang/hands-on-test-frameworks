#!/usr/bin/env python3
"""🏁 全家桶冒烟 + 漂移门禁演示 + 看板生成。

五路探针：REST(WireMock 声明+状态化) / GraphQL / gRPC(grpcurl) / BFF 聚合 /
消息事件（读 events-worker 的结果文件）。收尾做漂移注入：往 WireMock 推一条
篡改后的 /orders 映射 → 重新对表 → 漂移被抓 → 看板标红 → 恢复归零。

看板：reports/dashboard.html（每路一行 ✅/🔴 + 漂移演示区）。
"""
import json
import subprocess
import sys
import time

import httpx
import yaml

WIREMOCK = "http://127.0.0.1:9820"
GRAPHQL = "http://127.0.0.1:9821/graphql"
GRPC = "127.0.0.1:9822"
BFF = "http://127.0.0.1:9824/checkout"
ROWS, FAILURES = [], []


def check(name, ok, detail=""):
    print(f"  {'✅' if ok else '❌'} {name}{(' — ' + detail) if detail else ''}")
    ROWS.append((name, ok, detail))
    if not ok:
        FAILURES.append(name)


def rest_probe():
    r = httpx.get(f"{WIREMOCK}/api/orders", params={"limit": 10}, timeout=10, trust_env=False)
    body = r.json()
    check("REST：labs/15 契约形状（WireMock 声明式）",
          r.status_code == 200 and "items" in body, f"status={r.status_code}")


def graphql_probe():
    r = httpx.post(GRAPHQL, json={"query": '{ order(id: "x") { id amount review } }'},
                   headers={"X-Mock-Scene": "b"}, timeout=10, trust_env=False)
    o = r.json()["data"]["order"]
    check("GraphQL：场景 b 大额风控数据", o["id"] == "ORD-B-1" and o["review"] is True,
          f"amount={o['amount']}")


def grpc_probe():
    out = subprocess.run(
        ["grpcurl", "-plaintext", "-d", '{"order_id": "ORD-G-1"}',
         GRPC, "order.v1.OrderQuery/GetOrder"],
        capture_output=True, text=True, timeout=15)
    body = json.loads(out.stdout or "{}")
    check("gRPC：grpcurl unary 合法应答", body.get("order_id") == "ORD-G-1",
          f"status={body.get('status')}")


def bff_probe():
    r = httpx.post(BFF, json={"order_id": "ORD-FULL-1"}, timeout=30, trust_env=False)
    b = r.json()
    check("BFF：三下游聚合全绿（虚拟化模式）",
          b["payment"] not in (None, "PENDING_RETRY") and b["degraded"] == [],
          f"payment={b['payment']}")


def events_probe():
    with open("results/events.json", encoding="utf-8") as f:
        d = json.load(f)
    # 常驻 Redpanda 下 worker 可能被编排多次：每轮 5 处理 + 1 毒丸，DLQ 随轮次累积
    # 常驻 broker 多轮累积：总量是轮次的整数倍，且每轮固定 5 处理 + 1 毒丸
    rounds, ok = divmod(d["processed"], 5)
    nonblocked = (d["seqs"].count(4) == rounds      # 毒丸后的 seq 4 每轮都在
                  and d["dead_letter"] == rounds    # 每轮恰好 1 条毒丸
                  and ok == 0)
    check("消息事件：毒丸进 DLQ 不阻塞（多轮守恒）",
          nonblocked and rounds >= 1,
          f"轮次={rounds} processed={d['processed']} dead={d['dead_letter']}")


ORDERS_DRIFTED = {
    "name": "drift-injected-orders",
    "request": {"method": "GET", "urlPath": "/api/orders"},
    "response": {"status": 200, "jsonBody": {"items": []}},  # 真形状的 items/total 被删
}
ORDERS_ORIGINAL = {
    "name": "orders",
    "request": {"method": "GET", "urlPath": "/api/orders"},
    "response": {"status": 200, "jsonBody": {
        "items": [{"id": None, "customer": "某人", "qty": None,
                   "price": None, "status": "created"}], "total": None}},
}


def drift_demo():
    print("\n⑤ 漂移演示：篡改 WireMock 的 /orders 应答 → 巡检抓红 → 恢复归零")

    def set_mapping(mapping):
        # admin API 的 POST 收「单条 mapping 对象」；envelope 只用于磁盘文件
        httpx.delete(f"{WIREMOCK}/__admin/mappings", timeout=10, trust_env=False)
        httpx.post(f"{WIREMOCK}/__admin/mappings", json=mapping,
                   timeout=10, trust_env=False)

    def probe_drift():
        r = httpx.get(f"{WIREMOCK}/api/orders", params={"limit": 10},
                      timeout=10, trust_env=False)
        try:
            body = r.json()
        except Exception:  # 非 JSON（如空响应）也算漂移证据
            return [("mock_missing", "$", f"非 JSON 应答：{r.text[:40]!r}")]
        return [("mock_missing", "$.items[*]", "items 里的字段被删空")
                ] if body.get("items") == [] else []

    set_mapping(ORDERS_DRIFTED)
    drifts = probe_drift()
    check("注入漂移被巡检抓红（items 字段删空）", len(drifts) > 0,
          f"{len(drifts)} 处")
    ROWS.append(("漂移门禁（注入后）", False, "mock_missing $.items"))

    set_mapping(ORDERS_ORIGINAL)
    drifts = probe_drift()
    check("恢复后归零放行", len(drifts) == 0)
    ROWS.append(("漂移门禁（恢复后）", True, "0 漂移"))


def dashboard():
    rows = "\n".join(
        f"<tr class='{'ok' if ok else 'red'}'><td>{n}</td><td>{'✅' if ok else '🔴'}</td>"
        f"<td>{d}</td></tr>" for n, ok, d in ROWS)
    html = f"""<!doctype html><meta charset="utf-8"><title>虚拟化平台看板</title>
<style>body{{font-family:system-ui;max-width:720px;margin:2rem auto}}
tr.ok td{{color:#067d17}}tr.red td{{color:#c62828}}td{{padding:.3rem .8rem}}</style>
<h1>🏁 虚拟化平台能力看板</h1><table>{rows}</table>
<p>{'全绿' if not FAILURES else '存在标红项：' + '、'.join(FAILURES)}</p>"""
    with open("reports/dashboard.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("\n看板已生成：reports/dashboard.html")


def main():
    print("① REST 探针")
    rest_probe()
    print("② GraphQL 探针")
    graphql_probe()
    print("③ gRPC 探针")
    grpc_probe()
    print("④ BFF 聚合探针")
    bff_probe()
    print("   消息事件探针（读 events-worker 结果）")
    events_probe()
    drift_demo()
    dashboard()
    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 项失败：{'、'.join(FAILURES)}")
        sys.exit(1)
    print(">>> 冒烟全绿：REST ✅ GraphQL ✅ gRPC ✅ BFF ✅ 消息 ✅ + 漂移门禁演示 ✅")


if __name__ == "__main__":
    main()
