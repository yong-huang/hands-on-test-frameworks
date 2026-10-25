#!/usr/bin/env python3
"""漂移巡检器：真响应 vs mock 响应的双向结构 diff，漂移即退出码 1。

三类漂移（相对真服务）：
- mock_missing   真服务有的字段 mock 没了（mock 落后于现实）
- mock_extra     mock 多出来的字段（mock 声明了不存在的东西）
- type_changed   两边都有但类型不同（number/string/bool/…；int 与 float 同算 number）

清单原计划用 jsondiff——选型时放弃：门禁需要按「漂移类别」分类报告，
通用 diff 库的输出还要二次解析，自研递归 60 行反而更短更可控。
"""
import json
import sys

import httpx
import yaml

NUMBER = {"int", "float"}


def kind(v):
    return "number" if type(v).__name__ in NUMBER else type(v).__name__


def diff(real, mock, path="$", out=None):
    """递归对比：real 为基准（现实），mock 相对它归类漂移。"""
    out = out if out is not None else []
    if isinstance(real, dict):
        if not isinstance(mock, dict):
            return out + [{"path": path, "kind": "type_changed",
                           "detail": f"真服务是 object，mock 是 {kind(mock)}"}]
        for k in real:
            if k not in mock:
                out.append({"path": f"{path}.{k}", "kind": "mock_missing",
                            "detail": "真服务有、mock 没有"})
            else:
                diff(real[k], mock[k], f"{path}.{k}", out)
        for k in mock:
            if k not in real:
                out.append({"path": f"{path}.{k}", "kind": "mock_extra",
                            "detail": "mock 多出、真服务没有"})
        return out
    if kind(real) != kind(mock):
        out.append({"path": path, "kind": "type_changed",
                    "detail": f"真服务 {kind(real)}，mock {kind(mock)}（值：{mock!r}）"})
    return out


def call(base, method, path, body=None):
    r = httpx.request(method, base + path, json=body if body else None,
                      timeout=10, trust_env=False)
    return r.status_code, (r.json() if r.content else {})


PROBES = [
    ("GET /orders/{id}", "GET", "/orders/ORD-001", None, 200),
    ("POST /orders", "POST", "/orders", {"customer": "alice", "amount": 88.5}, 201),
]


def main():
    real_base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:9900"
    mock_base = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:9901"
    contract = sys.argv[3] if len(sys.argv) > 3 else "contracts/orders_ok.yaml"
    spec = yaml.safe_load(open(contract, encoding="utf-8"))

    print(f"① 巡检：真服务 {real_base} vs mock {mock_base}（契约 {contract}）")
    all_drifts, report = [], ["# 漂移巡检报告", "", f"契约：{contract}", ""]
    for name, method, path, body, want in PROBES:
        rs, rb = call(real_base, method, path, body)
        ms, mb = call(mock_base, method, path, body)
        status_ok = rs == ms == want
        drifts = diff(rb, mb)
        all_drifts += [{"probe": name, **d} for d in drifts]
        mark = "✅" if (status_ok and not drifts) else "❌"
        print(f"  {mark} [{name}] status {rs}/{ms}，漂移 {len(drifts)} 处")
        for d in drifts:
            print(f"     · {d['kind']}: {d['path']}（{d['detail']}）")
        report += [f"## {name}", f"- status：real {rs} / mock {ms}"
                   + ("" if status_ok else "（不一致）")]
        report += [f"- `{d['kind']}`: `{d['path']}`（{d['detail']}）" for d in drifts]
        report += ["- 无漂移"] if not drifts else []

    verdict = "无漂移，门禁放行" if not all_drifts else f"漂移 {len(all_drifts)} 处，门禁拦截"
    report += ["", f"**结论：{verdict}**"]
    with open("reports/drift.md", "w", encoding="utf-8") as f:
        f.write("\n".join(report) + "\n")

    print(f"\n② 结论：{verdict}（报告已写入 reports/drift.md）")
    sys.exit(1 if all_drifts else 0)


if __name__ == "__main__":
    main()
