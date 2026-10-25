#!/usr/bin/env python3
"""pact-as-stub：把 pact JSON 当应答数据源的最小 stub 服务器。

三块积木：
- 匹配：method+path 精确；query 按契约的 matchingRules（match:type = 类型一致
  即命中，值可以不同）
- 生成：应答体按契约的 generators 补随机值（RandomInt/RandomDecimal），契约里
  的 null 占位在应答时才变成真值
- 拒绝：契约之外的请求回 500 + interaction_not_found——pact mock 服务的同款
  语义，绝不静默兜底

这版刻意自研而不是用现成组件：pact-python 的 consumer mock 是随测试用例起的，
没有「长期伺服一份 pact 文件」的形态——而把 pact 文件伺服起来，恰恰证明
契约文件本身（不是任何工具）就是一份完整的应答数据源。
"""
import argparse
import json
import random
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

INTERACTIONS = []  # [(description, request, response), ...]


def load_pacts(pact_dir):
    for f in sorted(Path(pact_dir).glob("*.json")):
        pact = json.loads(Path(f).read_text(encoding="utf-8"))
        for it in pact.get("interactions", []):
            INTERACTIONS.append((it.get("description", "?"), it["request"], it["response"]))


def type_token(value):
    """类型令牌：pact match:type 的比较单位（数字串与数字同属 number）。"""
    try:
        float(value)
        return "number"
    except (TypeError, ValueError):
        return "string"


def query_matches(declared, rules, actual_qs):
    for name, values in (declared or {}).items():
        if name not in actual_qs:
            return False
        want = values[0] if isinstance(values, list) else values
        got = actual_qs[name][0]
        mr = ((rules or {}).get("query", {}).get(name, {})
              .get("matchers", [{}]))[0]
        if mr.get("match") == "type":
            if type_token(got) != type_token(want):
                return False
        elif got != want:
            return False
    return True


def find_interaction(method, path, query):
    for desc, req, resp in INTERACTIONS:
        if req["method"] != method or req["path"] != path:
            continue
        rules = req.get("matchingRules")
        if query_matches(req.get("query"), rules, query):
            return desc, resp
    return None, None


def apply_generators(value, gen_map, prefix="$"):
    """按 generators 的 JSON-path 键（支持 [*] 通配）把 null 占位补成随机值。"""
    for path, spec in (gen_map or {}).items():
        if not path.startswith(prefix):
            continue
        parts = [p for p in path[len(prefix):].split(".") if p]
        _apply(value, parts, spec)
    return value


def _apply(node, parts, spec):
    if not parts:
        return
    part = parts[0]
    if part.endswith("[*]"):
        key = part[:-3]
        for item in (node.get(key) or []):
            _apply(item, parts[1:], spec)
        return
    if len(parts) == 1:
        if part in node and node[part] is None:
            node[part] = _generate(spec)
        return
    _apply(node.setdefault(part, {}), parts[1:], spec)


def _generate(spec):
    kind = spec.get("type")
    if kind == "RandomInt":
        return random.randint(spec.get("min", 0), spec.get("max", 100))
    if kind == "RandomDecimal":
        digits = spec.get("digits", 6)
        return round(random.uniform(0, 10 ** (digits - 2)), 2)
    if kind == "RandomString":
        return "".join(random.choices("abcdef0123456789", k=8))
    return None


class StubHandler(BaseHTTPRequestHandler):
    server_version = "PactStub/1.0"

    def log_message(self, fmt, *args):
        pass

    def _send(self, status, payload, content_type="application/json"):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")

    def _handle(self, method):
        parts = urlsplit(self.path)
        query = parse_qs(parts.query)
        desc, resp = find_interaction(method, parts.path, query)
        if resp is None:
            return self._send(500, {
                "error": "interaction_not_found",
                "detail": f"没有契约交互匹配 {method} {parts.path}（pact 文件之外不予应答）",
                "expected": [d for d, _, _ in INTERACTIONS],
            })
        body = resp.get("body", {})
        content = apply_generators(json.loads(json.dumps(body.get("content", {}))),
                                   (resp.get("generators") or {}).get("body"))
        self._send(resp.get("status", 200), content,
                   body.get("contentType", "application/json"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9701)
    ap.add_argument("--pacts", default="pacts")
    args = ap.parse_args()
    load_pacts(args.pacts)
    print(f"pact-stub 已加载 {len(INTERACTIONS)} 条契约交互，监听 :{args.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port), StubHandler).serve_forever()


if __name__ == "__main__":
    main()
