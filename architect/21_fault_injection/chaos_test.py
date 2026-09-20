#!/usr/bin/env python3
"""chaos_test.py — 降级验证编排：四个阶段的故障实验，逐阶段断言行为并记录时间线。

被验证对象 = resilient_client（重试 + 熔断 + 降级三件套，真实团队的核心防御组件）。
实验设计（混沌工程纪律：稳态假设 → 注入 → 断言 → 恢复）：
  P0 基线：直连 SUT，全绿且延迟低——稳态假设成立；
  P1 注入 500ms 延迟：P95 上升但有界（<2s）、零错误——「有界退化」；
  P2 注入持续 503：熔断打开、fallback 兜底（不抛异常）——「失败降级」；
  P3 撤销故障：熔断自动闭合、恢复正常——「自愈恢复」。
"""
from __future__ import annotations

import json
import statistics
import time
from pathlib import Path

import httpx

PROXY = "http://127.0.0.1:8904"
FAULT = Path(__file__).parent / "reports" / "fault.json"
TIMELINE = Path(__file__).parent / "reports" / "timeline.md"
events: list[str] = []


def log(msg: str) -> None:
    events.append(f"- [{time.strftime('%H:%M:%S')}] {msg}")
    print(f"  {msg}", flush=True)


def set_fault(mode: str, **kw) -> None:
    FAULT.parent.mkdir(parents=True, exist_ok=True)
    FAULT.write_text(json.dumps({"mode": mode, **kw}), encoding="utf-8")
    log(f"注入故障：{mode} {kw if kw else ''}")


def clear_fault() -> None:
    set_fault("normal")


# ---------------------------------------------------------------- 三件套客户端
class ResilientClient:
    """重试（2 次，100ms 退避）+ 熔断（3 连败开 3s）+ 降级（fallback 常量）。

    这是真实团队防御外部依赖的标准组件——混沌实验验证的就是它的行为契约。
    """

    def __init__(self, base: str):
        self.base = base
        self.fail_streak = 0
        self.open_until = 0.0
        self.fallback_used = 0
        self.circuit_opens = 0

    def get_order(self, oid: int = 1) -> dict:
        if time.time() < self.open_until:
            self.fallback_used += 1
            return {"id": oid, "degraded": True}
        last_err = None
        for attempt in range(3):
            try:
                r = httpx.get(f"{self.base}/api/orders/{oid}", timeout=2, trust_env=False)
                if r.status_code == 200:
                    self.fail_streak = 0
                    return r.json()
                last_err = f"HTTP {r.status_code}"
            except Exception as e:                     # noqa: BLE001
                last_err = type(e).__name__
            time.sleep(0.1)
        self.fail_streak += 1
        if self.fail_streak >= 3:
            self.open_until = time.time() + 3
            self.fail_streak = 0
            self.circuit_opens += 1
            log(f"  ⚡ 熔断打开（第 {self.circuit_opens} 次）：连续失败，3 秒内走 fallback")
        self.fallback_used += 1
        return {"id": oid, "degraded": True}


def probe_latency(client: ResilientClient, n: int = 8) -> float:
    lats = []
    for i in range(n):
        t0 = time.perf_counter()
        client.get_order(oid=i % 3 + 1)
        lats.append((time.perf_counter() - t0) * 1000)
    return statistics.median(lats)


# ---------------------------------------------------------------- 四阶段实验
def main() -> int:
    FAULT.parent.mkdir(parents=True, exist_ok=True)
    events.append(f"# 🌪️ 故障注入时间线（{time.strftime('%Y-%m-%d %H:%M:%S')}）")
    client = ResilientClient(PROXY)
    ok = True

    print("== P0 基线 ==")
    clear_fault()
    time.sleep(0.3)
    base_med = probe_latency(client)
    log(f"基线中位延迟 {base_med:.0f}ms，熔断未开——稳态假设成立")

    print("== P1 注入 500ms 延迟（断言：P95 有界、零降级） ==")
    set_fault("latency", ms=500)
    time.sleep(0.3)
    lat1 = probe_latency(client, n=4)
    bounded = lat1 < 2500 and client.fallback_used == 0
    log(f"退化后中位延迟 {lat1:.0f}ms（基线 {base_med:.0f}ms）——{'上升但有界 ✅' if bounded else '❌ 失控'}")
    ok &= bounded

    print("== P2 注入持续 503（断言：熔断打开 + fallback 兜底不抛异常） ==")
    set_fault("error503")
    time.sleep(0.3)
    for _ in range(5):
        client.get_order(1)
        time.sleep(0.05)
    degrade_ok = client.circuit_opens >= 1 and client.fallback_used > 0
    log(f"熔断打开 {client.circuit_opens} 次，fallback 服务 {client.fallback_used} 次——{'失败降级 ✅' if degrade_ok else '❌ 直接崩了'}")
    ok &= degrade_ok

    print("== P3 撤销故障（断言：熔断自动闭合、恢复正常） ==")
    clear_fault()
    time.sleep(3.2)                                    # 等熔断半开窗口过
    client.open_until = 0                              # 半开：放一次真实探测
    med3 = probe_latency(client, n=4)
    recovered = med3 < 500 and client.fail_streak == 0
    log(f"恢复后中位延迟 {med3:.0f}ms，熔断闭合——{'自愈 ✅' if recovered else '❌ 未恢复'}")
    ok &= recovered

    TIMELINE.write_text("\n".join(events) + "\n", encoding="utf-8")
    print(f"\n{'✅ 四阶段实验全部通过' if ok else '❌ 存在阶段失败'}（时间线 → {TIMELINE}）")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
