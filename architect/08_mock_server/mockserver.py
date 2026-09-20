#!/usr/bin/env python3
"""mockserver.py — 录制回放式挡板服务（record / replay / upstream 三模式）。

架构师视角的一句话：**外部依赖（第三方支付/风控/短信）不稳定、要收费、没有测试环境时，
服务虚拟化让它们在磁带里复活**——录一次真响应，之后离线确定性回放。

三模式：
  upstream  假「第三方支付网关」，录制阶段的真实依赖替身；
  record    代理：客户端 → 挡板 → 上游，响应原样转发并写进磁带（cassette.json）；
  replay    断网模式：只查磁带回放；未命中=599（如实暴露）；标记超时的条目延迟后回 504。
统计：每次请求后把命中/未命中写 reports/mock_stats.json——挡板好不好用要看命中率。
"""
from __future__ import annotations

import argparse
import json
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import request as urlreq

CASSETTE = Path(__file__).parent / "reports" / "cassette.json"
STATS = Path(__file__).parent / "reports" / "mock_stats.json"
TIMEOUT_SLEEP_S = 2.0


def load_tape() -> dict:
    if CASSETTE.exists():
        return json.loads(CASSETTE.read_text(encoding="utf-8"))
    CASSETTE.parent.mkdir(parents=True, exist_ok=True)
    return {}


def save_tape(tape: dict) -> None:
    CASSETTE.write_text(json.dumps(tape, ensure_ascii=False, indent=2), encoding="utf-8")


def bump_stats(**delta) -> None:
    st = {"hits": 0, "misses": 0, "recorded": 0}
    if STATS.exists():
        st = json.loads(STATS.read_text(encoding="utf-8"))
    st.update(delta | {k: st.get(k, 0) + v for k, v in delta.items() if isinstance(v, int)})
    STATS.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")


class MockHandler(BaseHTTPRequestHandler):
    upstream: str = ""
    mode: str = "replay"

    def _reply(self, status: int, headers: dict, body: bytes):
        self.send_response(status)
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        self._handle()

    def do_GET(self):
        self._handle()

    def _handle(self):
        key = f"{self.command} {self.path}"
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        tape = load_tape()

        if self.mode == "upstream":                       # 假第三方网关的固定行为
            if self.path == "/" :
                self._reply(200, {"Content-Type": "text/plain"}, b"fake-gateway ok")
                return
            if self.command == "POST" and self.path == "/pay":
                self._reply(200, {"Content-Type": "application/json"},
                            json.dumps({"txn": f"TXN-{uuid.uuid4().hex[:8]}",
                                        "status": "ok"}).encode())
                return
            if self.command == "GET" and self.path.startswith("/pay/status"):
                txn = self.path.split("txn=")[-1]
                self._reply(200, {"Content-Type": "application/json"},
                            json.dumps({"txn": txn, "state": "settled"}).encode())
                return
            self._reply(404, {"Content-Type": "application/json"},
                        json.dumps({"error": "fake-gateway: no route"}).encode())
            return

        if self.mode == "record":
            req = urlreq.Request(self.upstream + self.path, data=body if body else None,
                                 method=self.command,
                                 headers={"Content-Type": "application/json"})
            try:
                with urlreq.urlopen(req, timeout=5) as r:
                    payload, status = r.read(), r.status
            except Exception as e:                       # 上游挂了要如实喊出来
                self._reply(502, {"Content-Type": "application/json"},
                            json.dumps({"error": f"upstream unreachable: {e}"}).encode())
                return
            tape[key] = {"status": status,
                         "headers": {"Content-Type": "application/json"},
                         "body": payload.decode("utf-8", errors="replace"),
                         "recorded_at": time.strftime("%Y-%m-%d %H:%M:%S")}
            save_tape(tape)
            bump_stats(recorded=1)
            self._reply(status, {"Content-Type": "application/json"}, payload)
            return

        # replay 模式
        entry = tape.get(key)
        if entry is None:
            bump_stats(misses=1)
            self._reply(599, {"Content-Type": "application/json"},
                        json.dumps({"error": f"磁带未命中: {key}"}).encode())
            return
        if entry.get("timeout"):                          # 手工编辑过的超时磁带
            time.sleep(TIMEOUT_SLEEP_S)
            bump_stats(hits=1)
            self._reply(504, {"Content-Type": "application/json"},
                        json.dumps({"error": "gateway timeout (taped)"}).encode())
            return
        bump_stats(hits=1)
        self._reply(entry["status"], entry["headers"], entry["body"].encode())

    def log_message(self, *a):     # 静默默认日志，输出留给演示脚本
        pass


def serve(mode: str, port: int, upstream: str) -> None:
    MockHandler.mode = mode
    MockHandler.upstream = upstream
    tag = {"record": f"录制模式（上游 {upstream}）", "replay": "回放模式（断网，只查磁带）",
           "upstream": "假第三方网关"}[mode]
    print(f"挡板 [{mode}] {tag} → http://127.0.0.1:{port}")
    ThreadingHTTPServer(("127.0.0.1", port), MockHandler).serve_forever()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="录制回放式挡板服务")
    ap.add_argument("mode", choices=["record", "replay", "upstream"])
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--upstream", default="http://127.0.0.1:8900")
    args = ap.parse_args()
    serve(args.mode, args.port, args.upstream)
