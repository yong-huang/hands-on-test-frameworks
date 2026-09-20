#!/usr/bin/env python3
"""probe.py — 合成监控探针：定时合成事务 + sqlite 时序 + 连续失败告警 + 恢复消除。

架构师视角的一句话：**右移回答的问题是「上线之后还活着吗」**——合成监控用脚本
模拟真实用户走关键链路（登录/下单），探针失败 = 用户即将失败，比等客诉快一个量级。
告警语义：连续 N 次失败才触发（单次抖动不吵人），一次成功即恢复（活过来了就闭嘴）。
状态持久化在 sqlite——探针进程随时死掉重启，告警状态不能丢。
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import time
from pathlib import Path

import httpx

DB = Path(__file__).parent / "reports" / "probe.db"
ALERT_THRESHOLD = 2          # 连续失败 N 次触发告警
BASE = "http://127.0.0.1:8899"

SCHEMA = """
CREATE TABLE IF NOT EXISTS results(
    ts REAL, probe TEXT, ok INTEGER, latency_ms REAL, error TEXT);
CREATE TABLE IF NOT EXISTS alerts(
    probe TEXT PRIMARY KEY, active INTEGER, opened_at TEXT, closed_at TEXT, reason TEXT);
"""


def db() -> sqlite3.Connection:
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB)
    c.executescript(SCHEMA)
    return c


# ---------------------------------------------------------------- 合成事务
def txn_health(c: httpx.Client) -> tuple[bool, str]:
    r = c.get(f"{BASE}/api/health", timeout=3)
    return r.status_code == 200, f"HTTP {r.status_code}"


def txn_login_page(c: httpx.Client) -> tuple[bool, str]:
    r = c.get(f"{BASE}/login.html", timeout=3)
    ok = r.status_code == 200 and "form" in r.text.lower()
    return ok, f"HTTP {r.status_code}" + ("" if ok else "（页面异常）")


def txn_order_flow(c: httpx.Client) -> tuple[bool, str]:
    """下单→查询→删单 全链路合成事务（自清理，不污染数据）。"""
    r = c.post(f"{BASE}/api/orders", json={
        "customer": "probe", "item": "探针商品", "qty": 1, "price": 1.0}, timeout=5)
    if r.status_code != 201:
        return False, f"下单 HTTP {r.status_code}"
    oid = r.json()["id"]
    g = c.get(f"{BASE}/api/orders/{oid}", timeout=3)
    d = c.delete(f"{BASE}/api/orders/{oid}", timeout=3)
    ok = g.status_code == 200 and d.status_code == 204
    return ok, f"下单{r.status_code}/查询{g.status_code}/删除{d.status_code}"


PROBES = {"health": txn_health, "login_page": txn_login_page, "order_flow": txn_order_flow}


# ---------------------------------------------------------------- 告警状态机
def update_alert(cur: sqlite3.Cursor, probe: str, ok: bool, reason: str) -> str | None:
    row = cur.execute("SELECT active FROM alerts WHERE probe=?", (probe,)).fetchone()
    active = bool(row[0]) if row else False
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    if not ok:
        streak = consecutive_fails(cur, probe)
        if not active and streak >= ALERT_THRESHOLD:
            cur.execute("INSERT INTO alerts(probe,active,opened_at,reason) VALUES(?,1,?,?) "
                        "ON CONFLICT(probe) DO UPDATE SET active=1, opened_at=?, reason=?",
                        (probe, now, reason, now, reason))
            return f"🚨 ALERT 触发：{probe} 连续 {streak} 次失败（{reason}）"
    else:
        if active:
            cur.execute("UPDATE alerts SET active=0, closed_at=? WHERE probe=?", (now, probe))
            return f"✅ RECOVERED 告警消除：{probe} 探针恢复"
        cur.execute("INSERT INTO alerts(probe,active,closed_at,reason) VALUES(?,0,?,?) "
                    "ON CONFLICT(probe) DO UPDATE SET active=0, closed_at=?",
                    (probe, now, "ok", now))
    return None


def consecutive_fails(cur: sqlite3.Cursor, probe: str) -> int:
    rows = cur.execute(
        "SELECT ok FROM results WHERE probe=? ORDER BY ts DESC LIMIT ?",
        (probe, ALERT_THRESHOLD)).fetchall()
    if len(rows) < ALERT_THRESHOLD:
        return 0
    for i, (ok,) in enumerate(rows):
        if ok:
            return 0
        if i > 0:
            break
    return ALERT_THRESHOLD


# ---------------------------------------------------------------- 主循环
def run(rounds: int, interval: float) -> None:
    con = db()
    cur = con.cursor()
    with httpx.Client(trust_env=False) as client:
        for r in range(rounds):
            ts = time.time()
            for name, fn in PROBES.items():
                t0 = time.perf_counter()
                try:
                    ok, err = fn(client)
                except Exception as e:
                    ok, err = False, f"{type(e).__name__}: {e}"
                lat = (time.perf_counter() - t0) * 1000
                cur.execute("INSERT INTO results VALUES(?,?,?,?,?)",
                            (ts, name, int(ok), round(lat, 1), err if not ok else ""))
                msg = update_alert(cur, name, ok, err)
                if msg:
                    print(f"  {msg}", flush=True)
            con.commit()
            print(f"round {r+1}/{rounds} 完成："
                  + " ".join(f"{k}={'✅' if v else '❌'}" for k, v in
                             cur.execute("SELECT probe, ok FROM results WHERE ts=?", (ts,)).fetchall()),
                  flush=True)
            if r < rounds - 1:
                time.sleep(interval)
    con.close()


def stats() -> dict:
    con = db()
    cur = con.cursor()
    out = {}
    probes = [r[0] for r in cur.execute("SELECT DISTINCT probe FROM results").fetchall()]
    for probe in probes:
        total, ok = cur.execute(
            "SELECT COUNT(*), SUM(ok) FROM results WHERE probe=?", (probe,)).fetchone()
        avg_lat = cur.execute(
            "SELECT AVG(latency_ms) FROM results WHERE probe=? AND ok=1", (probe,)).fetchone()[0]
        alerts = cur.execute(
            "SELECT active, opened_at, closed_at FROM alerts WHERE probe=?", (probe,)).fetchone()
        out[probe] = {"runs": total, "success_rate": round(ok * 100 / total, 1) if total else 0,
                      "avg_latency_ms": round(avg_lat or 0, 1),
                      "alert_active": bool(alerts[0]) if alerts else False,
                      "opened_at": alerts[1] if alerts else None,
                      "closed_at": alerts[2] if alerts else None}
    con.close()
    return out


def render_stats(s: dict) -> str:
    lines = ["# 🛰️ 合成探针报告", ""]
    for probe, st in s.items():
        lines.append(
            f"- **{probe}**：{st['runs']} 轮，成功率 {st['success_rate']}%，"
            f"平均延迟 {st['avg_latency_ms']}ms，"
            f"告警{'⚠️ 活跃（开启于 '+st['opened_at']+'' if st['alert_active'] else '已消除（'+st['closed_at']+'）' if st['closed_at'] else '从未触发'}")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="合成监控探针")
    ap.add_argument("cmd", choices=["run", "report"])
    ap.add_argument("--rounds", type=int, default=10)
    ap.add_argument("--interval", type=float, default=1.0)
    args = ap.parse_args()
    if args.cmd == "run":
        run(args.rounds, args.interval)
        return 0
    s = stats()
    print(json.dumps(s, ensure_ascii=False, indent=2))
    print(render_stats(s))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
