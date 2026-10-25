#!/usr/bin/env python3
"""真服务：固定应答的订单 API（漂移巡检的「现实」一侧）。

应答刻意全确定性（无随机、无时间）——巡检比的是结构，固定值让 diff 输出
稳定可读。GET 带 created_at 与 amount(number)，是后续契约漂移注入的靶子。
"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ORDER = {"order_id": "ORD-001", "customer": "alice", "amount": 123.5,
         "state": "created", "created_at": "2026-10-24 12:00:00"}


class Handler(BaseHTTPRequestHandler):
    server_version = "RealOrders/1.0"

    def log_message(self, fmt, *args):
        pass

    def _send(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.startswith("/orders/"):
            return self._send(200, dict(ORDER, order_id=self.path.rsplit("/", 1)[-1]))
        self._send(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length:
            self.rfile.read(length)
        self._send(201, {"order_id": "ORD-NEW-001", "state": "created",
                         "review": False, "created_at": "2026-10-24 12:00:00"})


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9900)
    args = ap.parse_args()
    print(f"真服务已就绪，监听 :{args.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
