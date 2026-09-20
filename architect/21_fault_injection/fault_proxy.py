#!/usr/bin/env python3
"""fault_proxy.py — 故障注入代理：正常转发 + 三种故障模式（延迟/拒绝/503）。

故障模式由 reports/fault.json 热控制（chaos 脚本改文件即生效，无需重启代理）：
  {"mode": "normal"}                    正常转发
  {"mode": "latency", "ms": 500}        转发前 sleep
  {"mode": "error503"}                  直接回 503（模拟依赖过载）
  {"mode": "refuse"}                    直接断开连接（模拟依赖宕机）
"""
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import httpx

UPSTREAM = "http://127.0.0.1:8899"
FAULT = Path(__file__).parent / "reports" / "fault.json"


def fault_mode() -> dict:
    if FAULT.exists():
        return json.loads(FAULT.read_text(encoding="utf-8"))
    return {"mode": "normal"}


class Handler(BaseHTTPRequestHandler):
    def _relay(self, method):
        f = fault_mode()
        if f["mode"] == "refuse":
            self.close_connection = True
            self.wfile.close()
            return
        if f["mode"] == "latency":
            time.sleep(f.get("ms", 500) / 1000)
        if f["mode"] == "error503":
            body = b'{"error":"upstream overloaded (injected)"}'
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        length = int(self.headers.get("Content-Length") or 0)
        payload = self.rfile.read(length) if length else None
        with httpx.Client(timeout=10, trust_env=False) as c:
            r = c.request(method, UPSTREAM + self.path, content=payload,
                          headers={"Content-Type": self.headers.get("Content-Type", "application/json")})
        self.send_response(r.status_code)
        self.send_header("Content-Type", r.headers.get("Content-Type", "application/json"))
        self.send_header("Content-Length", str(len(r.content)))
        self.end_headers()
        self.wfile.write(r.content)

    def do_GET(self):
        self._relay("GET")

    def do_POST(self):
        self._relay("POST")

    def do_DELETE(self):
        self._relay("DELETE")

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print("故障代理 :8904 → 上游 :8899（模式由 reports/fault.json 热控制）")
    ThreadingHTTPServer(("127.0.0.1", 8904), Handler).serve_forever()
