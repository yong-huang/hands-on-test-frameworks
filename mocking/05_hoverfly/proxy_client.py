#!/usr/bin/env python3
"""结账客户端：经（或绕过）Hoverfly 代理访问支付网关。

经代理模式用 http.client 直连代理、请求行写绝对 URL——这是 HTTP 代理的
教科书语义。不用 urllib 的 ProxyHandler：macOS 上它会查系统代理排除表，
对 127.0.0.1 一律旁路（实测踩过：请求根本没进代理，journal 空）。

三种用途由脚本编排：
- 录制期/回放期：正常跑，输出只含稳定字段（状态码 + 解析后的字段），
  保证「逐字节一致」diff 有意义；
- 注入期：--expect-500 模式，收到 500 时打印注入生效并以退出码 1 报红。
"""
import argparse
import json
import sys
from http.client import HTTPConnection
from urllib import error, request
from urllib.parse import urlsplit

UPSTREAM = "http://127.0.0.1:9500"


def call_via_proxy(proxy, method, url, body=None):
    """把请求发给代理，请求行用绝对 URL（代理转发给真实目标）。"""
    parts = urlsplit(proxy)
    conn = HTTPConnection(parts.hostname, parts.port or 8080, timeout=10)
    conn.request(method, url, body=body,
                 headers={"Content-Type": "application/json"})
    resp = conn.getresponse()
    data = resp.read()
    conn.close()
    return resp.status, data


def call_direct(method, url, body=None):
    r = request.Request(url, data=body, method=method,
                        headers={"Content-Type": "application/json"})
    try:
        with request.build_opener(request.ProxyHandler({})).open(r, timeout=10) as resp:
            return resp.status, resp.read()
    except error.HTTPError as e:
        return e.code, e.read()


def flow(proxy):
    """结账两步：支付创建 → 凭 txn 查状态。输出只含稳定字段。"""
    send = (lambda m, u, b=None: call_via_proxy(proxy, m, u, b)) if proxy else call_direct
    body = json.dumps({"order": "ORDER-FIXED-001", "amount": 4200}).encode()
    status, raw = send("POST", UPSTREAM + "/pay", body)
    payload = json.loads(raw or b"null")
    print(f"POST /pay → {status} txn={payload.get('txn')} gw_status={payload.get('status')}")
    if status != 200:
        return 1

    txn = payload["txn"]
    status, raw = send("GET", UPSTREAM + f"/pay/status?txn={txn}")
    state = json.loads(raw or b"null")
    print(f"GET /pay/status → {status} state={state.get('state')}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proxy", help="经此 HTTP 代理发请求（如 http://127.0.0.1:9501）")
    ap.add_argument("--expect-500", action="store_true", help="收到 500 视为注入生效，退出码 1")
    args = ap.parse_args()
    rc = flow(args.proxy)
    if args.expect_500:
        if rc == 1:
            print(">>> 注入生效：支付被 simulation 里的 500 拦下（业务按失败分支处理）")
        sys.exit(rc)
    sys.exit(rc)


if __name__ == "__main__":
    main()
