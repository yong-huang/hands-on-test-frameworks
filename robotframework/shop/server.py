#!/usr/bin/env python3
"""Robot 专属靶场：Web 下单表单 + 4 个 REST 接口（创建/查询/支付/取消）。

用法: .venv/bin/python server.py --port 8952
"""
import argparse
import json
import os
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
LOCK = threading.Lock()
ORDERS = {}  # id -> {id, customer, product, amount, status}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, code, payload=None):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/health":
            return self._send(200, {"status": "ok"})
        if self.path.startswith("/api/orders/"):
            oid = self.path.rsplit("/", 1)[1]
            with LOCK:
                order = ORDERS.get(oid)
            return self._send(200, order) if order else self._send(404, {"error": "order not found"})
        return self._static(self.path)

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._send(400, {"error": "invalid json"})
        path = self.path.rstrip("/")
        if path == "/api/orders":
            if not body.get("customer") or not body.get("product"):
                return self._send(422, {"error": "customer/product required"})
            oid = "ROB-" + uuid.uuid4().hex[:8]
            with LOCK:
                ORDERS[oid] = {"id": oid, "customer": body["customer"], "product": body["product"],
                               "amount": round(19.9 * int(body.get("qty", 1)), 2), "status": "created"}
            return self._send(201, ORDERS[oid])
        parts = path.split("/")
        if len(parts) >= 4 and parts[1] == "orders" and parts[2] != "":
            oid, action = parts[2], (parts[3] if len(parts) > 3 else "")
            with LOCK:
                order = ORDERS.get(oid)
            if not order:
                return self._send(404, {"error": "order not found"})
            if action == "pay":
                if order["status"] != "created":
                    return self._send(409, {"error": f"cannot pay from {order['status']}"})
                order["status"] = "paid"
                return self._send(200, order)
            if action == "cancel":
                if order["status"] == "paid":
                    return self._send(409, {"error": "paid order cannot be cancelled"})
                order["status"] = "cancelled"
                return self._send(200, order)
        return self._send(404, {"error": "not found"})

    def _static(self, path):
        name = "index.html" if path in ("/", "") else path.lstrip("/")
        full = os.path.normpath(os.path.join(HERE, name))
        if not full.startswith(HERE) or not os.path.isfile(full):
            return self._send(404, {"error": "not found"})
        with open(full, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8952)
    args = ap.parse_args()
    srv = ThreadingHTTPServer(("0.0.0.0", args.port), Handler)
    print(f"robot shop serving on http://0.0.0.0:{args.port}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
