#!/usr/bin/env python3
"""shop server — selenium 系列共享被测靶场（静态页 + 最小 REST API）。

用法: .venv/bin/python server.py --port 8946
陷阱清单见 SECRET_DEFS.md（先自己找，别偷看）。
"""
import argparse
import json
import os
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
LOCK = threading.Lock()
ORDERS = {}  # order_id -> {id, customer, product, qty, amount, status}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, code, payload=None, bytes_body=None, ctype="application/json; charset=utf-8"):
        if bytes_body is None:
            bytes_body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(bytes_body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(bytes_body)

    def do_GET(self):
        path, _, query = self.path.partition("?")
        if path == "/api/health":
            return self._send(200, {"status": "ok"})
        if path == "/api/products":
            page = int([q for q in query.split("&") if q.startswith("page=")][0].split("=")[1]) \
                if "page=" in query else 1
            time.sleep(1.2)  # 陷阱③前置：接口慢，逼出等待与懒加载问题
            size = 10
            names = [f"商品 {((page - 1) * size) + i:02d}" for i in range(1, size + 1)]
            items = [{"name": n, "price": 9.99 + i * 0.5} for i, n in enumerate(names)]
            return self._send(200, {"page": page, "pages": 3, "items": items})
        if path.startswith("/api/orders/"):
            oid = path.rsplit("/", 1)[1]
            with LOCK:
                order = ORDERS.get(oid)
            return self._send(200, order) if order else self._send(404, {"error": "order not found"})
        return self._static(path)

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._send(400, {"error": "invalid json"})
        path = self.path.rstrip("/")
        if path == "/api/feedback":  # 表单回读：原样回显，供「服务端回读 vs 输入」断言
            return self._send(200, {"received": body})
        if path == "/api/orders":
            if not body.get("customer") or not body.get("product"):
                return self._send(422, {"error": "customer/product required"})
            oid = "ORD-" + uuid.uuid4().hex[:8]
            qty = int(body.get("qty", 1))
            with LOCK:
                ORDERS[oid] = {"id": oid, "customer": body["customer"], "product": body["product"],
                               "qty": qty, "amount": round(9.99 * qty + 5.99, 2), "status": "created"}
            return self._send(201, ORDERS[oid])
        m_pay, oid = path.startswith("/api/orders/"), None
        if m_pay:
            parts = path.split("/")
            oid, action = parts[3], (parts[4] if len(parts) > 4 else "")
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
        ctype = {"html": "text/html; charset=utf-8", "js": "text/javascript; charset=utf-8",
                 "css": "text/css; charset=utf-8"}.get(full.rsplit(".", 1)[-1], "application/octet-stream")
        with open(full, "rb") as f:
            return self._send(200, bytes_body=f.read(), ctype=ctype)

    def log_message(self, *a):  # 静默访问日志，避免污染 .server.log
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8946)
    ap.add_argument("--bind", default="0.0.0.0", help="Grid 容器里的浏览器要经 host.docker.internal 访问，须绑 0.0.0.0")
    args = ap.parse_args()
    srv = ThreadingHTTPServer((args.bind, args.port), Handler)
    print(f"shop serving on http://{args.bind}:{args.port}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
