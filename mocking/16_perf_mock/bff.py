#!/usr/bin/env python3
"""订单聚合 BFF：依赖 支付/风控/短信 三个下游，带逐依赖降级分支。

下游地址从环境变量读取（同一份代码两种模式）：
  DOWNSTREAM_MODE=real → 9801/9802/9803 三个真服务
  DOWNSTREAM_MODE=mock → 单个声明式替身 :9810（/pay /risk /sms 同端口不同路径）

降级章程（07 矩阵的分支在这里落地）：
  支付失败 → payment=PENDING_RETRY（业务不崩，落补偿）
  风控失败 → risk=DEFAULT_PASS（默认放行 + 标记）
  短信失败 → sms=skipped（尽力而为，可补发）
"""
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx

MODE = os.environ.get("DOWNSTREAM_MODE", "mock")
BASES = {
    "pay": os.environ.get("PAY_BASE", "http://127.0.0.1:9810"),
    "risk": os.environ.get("RISK_BASE", "http://127.0.0.1:9810"),
    "sms": os.environ.get("SMS_BASE", "http://127.0.0.1:9810"),
}
if MODE == "real":
    BASES = {"pay": "http://127.0.0.1:9801", "risk": "http://127.0.0.1:9802",
             "sms": "http://127.0.0.1:9803"}

TIMEOUT_S = 1.0

# 压测加固：共享连接池（避免每请求新建连接）+ 更深的监听队列
_shared = httpx.Client(timeout=TIMEOUT_S, trust_env=False,
                       limits=httpx.Limits(max_connections=300))


class Server(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 256


def call(name, path, payload):
    try:
        r = _shared.post(BASES[name] + path, json=payload)
        return r.status_code, (r.json() if r.content else {})
    except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError):
        return None, {}


def checkout(order):
    """聚合三下游：每个都有独立的降级分支，任何下游死都不崩。"""
    result = {"order_id": order.get("order_id", "ORD-AGG-001"),
              "payment": None, "risk": None, "sms": None, "degraded": []}

    code, body = call("pay", "/pay", order)
    if code == 200:
        result["payment"] = body.get("txn", "unknown")
    else:
        result["payment"] = "PENDING_RETRY"
        result["degraded"].append("pay")

    code, body = call("risk", "/risk", order)
    if code == 200:
        result["risk"] = body.get("decision", "unknown")
    else:
        result["risk"] = "DEFAULT_PASS"
        result["degraded"].append("risk")

    code, body = call("sms", "/sms", order)
    if code == 200 and body.get("sent"):
        result["sms"] = body.get("message_id", "sent")
    else:
        result["sms"] = "skipped"
        result["degraded"].append("sms")

    return result


class Handler(BaseHTTPRequestHandler):
    server_version = "OrderBFF/1.0"

    def log_message(self, fmt, *args):
        pass

    def do_POST(self):
        if self.path != "/checkout":
            return self._send(404, {"error": "use POST /checkout"})
        length = int(self.headers.get("Content-Length") or 0)
        order = json.loads(self.rfile.read(length) or b"{}") if length else {}
        self._send(200, checkout(order))

    def _send(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    print(f"OrderBFF 就绪（模式 {MODE}，下游 {BASES}）", flush=True)
    Server(("127.0.0.1", 9804), Handler).serve_forever()
