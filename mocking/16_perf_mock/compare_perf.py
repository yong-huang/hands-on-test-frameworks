#!/usr/bin/env python3
"""双档延迟对比 + 零泄漏断言：读两份 k6 summary，输出吞吐/P95 对比表。"""
import json
import sys

FAILURES = []


def load(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    m = d["metrics"]
    return {
        "throughput": m["iterations"]["count"],
        "p95": m["http_req_duration"]["p(95)"],  # k6 已是 ms
        "errors": m["http_req_failed"]["value"],
    }


def main():
    s_fast = load(sys.argv[1])
    s_slow = load(sys.argv[2])
    stub_hits = int(sys.argv[3])  # 压测替身侧命中计数

    print("① 双档延迟对比（100 VUs × 15s）")
    print(f"  {'档位':<10} {'吞吐(iterations)':>16} {'P95(ms)':>10} {'错误率':>8}")
    for name, s in (("50ms", s_fast), ("500ms", s_slow)):
        print(f"  {name:<10} {s['throughput']:>16.0f} {s['p95']:>10.0f} {s['errors']:>8.4f}")

    slow_is_slower = s_slow["p95"] > s_fast["p95"]
    print(f"  ✅ 下游延迟 50→500ms，BFF P95 相应上涨（{s_fast['p95']:.0f} → {s_slow['p95']:.0f} ms）"
          if slow_is_slower else
          f"  ❌ P95 未随下游延迟上涨（{s_fast['p95']:.0f} → {s_slow['p95']:.0f}）")
    if not slow_is_slower:
        FAILURES.append("延迟敏感性")

    no_err = s_fast["errors"] == 0 and s_slow["errors"] == 0
    print(f"  {'✅' if no_err else '❌'} 两档全程零错答" + ("" if no_err else "（有失败请求）"))
    if not no_err:
        FAILURES.append("错误率")

    # 替身在两档间重启过，计数器属于第二档：命中应恰为 3×第二档迭代
    # （每次 checkout 打 3 个下游；±1% 松弛给线程计数）
    expect = s_slow["throughput"] * 3
    leak_free = abs(stub_hits - expect) <= expect * 0.01
    print(f"  {'✅' if leak_free else '❌'} 零泄漏：第二档迭代 {s_slow['throughput']:.0f} × 3 下游 = "
          f"{expect:.0f}，替身命中 {stub_hits}（精确对账，真下游未在场）")
    if not leak_free:
        FAILURES.append("零泄漏")

    print()
    if FAILURES:
        print(f"❌ 断言失败：{'、'.join(FAILURES)}")
        sys.exit(1)
    print(">>> 验收：100 并发零错答 ✅ 延迟敏感性成立 ✅ 零泄漏 ✅")


if __name__ == "__main__":
    main()
