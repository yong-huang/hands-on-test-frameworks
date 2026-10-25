#!/usr/bin/env python3
"""压测用的下游替身：可配置延迟 + 命中计数（零泄漏断言的数据源）。

- POST /pay|/risk|/sms → 按 --delay-ms 睡眠后返回固定 JSON
- GET /stats → {"hits": N, "delay_ms": X}（k6 压完后核对泄漏）
- 线程安全计数（压测并发下也准）
"""
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DELAY_MS = int(sys.argv[sys.argv.index("--delay-ms") + 1]) if "--delay-ms" in sys.argv else 50
PORT = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 9810

LOCK = threading.Lock()
HITS = {"n": 0}

RESPONSES = {
    "/pay": {"txn": "TXN-PERF", "status": "settled"},
    "/risk": {"decision": "approve", "score": 90},
    "/sms": {"sent": True, "message_id": "MSG-PERF"},
}


class Handler(BaseHTTPRequestHandler):
    server_version = "PerfMock/1.0"

    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        if self.path == "/stats":
            with LOCK:
                return self._send(200, {"hits": HITS["n"], "delay_ms": DELAY_MS})
        self._send(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length:
            self.rfile.read(length)
        payload = RESPONSES.get(self.path.split("?")[0])
        if payload is None:
            return self._send(404, {"error": "not found"})
        if DELAY_MS:
            time.sleep(DELAY_MS / 1000)
        with LOCK:
            HITS["n"] += 1
        self._send(200, payload)

    def _send(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    print(f"压测替身就绪：延迟 {DELAY_MS}ms，监听 :{PORT}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
