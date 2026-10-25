#!/usr/bin/env python3
"""三个「真下游」（确定性应答）：支付 :9801 / 风控 :9802 / 短信 :9803。

它们扮演现实——BFF 的聚合逻辑以它们的应答为准。虚拟化模式下它们被全部
杀掉，由 01 的声明式替身顶上。
"""
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROLE = sys.argv[1] if len(sys.argv) > 1 else "pay"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 9801

RESPONSES = {
    "pay": (200, {"txn": "TXN-REAL-001", "status": "settled"}),
    "risk": (200, {"decision": "approve", "score": 87}),
    "sms": (200, {"sent": True, "message_id": "MSG-REAL-001"}),
}


class Handler(BaseHTTPRequestHandler):
    server_version = f"Real_{ROLE}/1.0"

    def log_message(self, fmt, *args):
        pass

    def _handle(self, method):
        if method == "POST" and self.path in ("/pay", "/risk", "/sms"):
            length = int(self.headers.get("Content-Length") or 0)
            if length:
                self.rfile.read(length)
            status, payload = RESPONSES[ROLE]
            return self._send(status, payload)
        self._send(404, {"error": "not found"})

    def _send(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    do_GET = lambda self: self._handle("GET")
    do_POST = lambda self: self._handle("POST")


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
