#!/usr/bin/env python3
"""声明式 mock server：规则表是数据，匹配引擎只有一套。

三块积木：
- 加载：启动时读 stubs/*.json，每条 stub = match(约束) + response(应答)
- 匹配：method+path 命中的候选里，约束全部满足者按「特异度分」取最高；
  平分取先定义——同一套语义，规则文件怎么写都不含糊
- 诊断：没有任何 stub 全约束满足时，404 带逐条失败原因，绝不静默兜底

每个应答自带 X-Mocked-By（哪条规则答的）与 X-Match-Score（特异度分），
客户端不用翻服务端日志就能断言「是谁在应答」。

本实验刻意保持最小：path 只支持精确匹配，body 条件只支持
`$.字段 运算符 字面量`。模板化、正则 path、延迟注入留给后续实验。
"""
import json
import sys
import threading
from glob import glob
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

LOCK = threading.Lock()
STATS = {"hits": 0, "misses": 0, "by_stub": {}}
MISSING = object()  # dot-path 未命中的哨兵，区别于合法值 None

# 特异度评分：path/method 命中是入场券（0 分），每条 header 约束 +10，
# 每条 body 条件 +20——约束越细的规则越懂这个请求，理应它来应答。
HEADER_SCORE = 10
BODY_SCORE = 20


def load_stubs(stub_dir):
    """stubs/*.json 每个文件是一组规则；加载顺序即「先定义」的先后。"""
    stubs = []
    files = sorted(glob(str(Path(stub_dir) / "*.json")))
    if not files:
        sys.exit(f"stub 目录 {stub_dir} 下没有 .json 规则文件")
    for f in files:
        for stub in json.loads(Path(f).read_text(encoding="utf-8")):
            stub["_source"] = Path(f).name
            stubs.append(stub)
    return stubs


def resolve_dotpath(obj, path):
    """取 `$.customer.tier` 这类点路径；取不到返回 MISSING（不是 None）。"""
    cur = obj
    for part in path.lstrip("$.").split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return MISSING
    return cur


def eval_body_condition(cond, body):
    """求值一条 body 条件，返回 (是否满足, 人话原因)。

    body 不是 JSON 或字段缺失都算不满足——原因要能直接贴进诊断报告。
    """
    path, op, value = cond["path"], cond["op"], cond["value"]
    if body is MISSING:
        return False, f"body 条件 {path} {op} {value!r} 不满足（body 不是合法 JSON）"
    actual = resolve_dotpath(body, path)
    if actual is MISSING:
        return False, f"body 条件 {path} {op} {value!r} 不满足（字段不存在）"
    ops = {
        "==": lambda a, b: a == b, "!=": lambda a, b: a != b,
        ">": lambda a, b: a > b, "<": lambda a, b: a < b,
        ">=": lambda a, b: a >= b, "<=": lambda a, b: a <= b,
    }
    if op not in ops:
        return False, f"body 条件 {path} 用了不支持的运算符 {op}"
    try:
        ok = ops[op](actual, value)
    except TypeError:
        return False, f"body 条件 {path} {op} {value!r} 不满足（{actual!r} 与 {value!r} 类型不可比）"
    if not ok:
        return False, f"body 条件 {path} {op} {value!r} 不满足（实际 {actual!r}）"
    return True, ""


def match_request(stubs, method, path, headers, body):
    """返回 (命中的 stub, 应答分) 或 (None, 逐条失败原因)。"""
    reasons, best, best_score = [], None, -1
    for stub in stubs:
        m = stub["match"]
        if m["method"] != method or m["path"] != path:
            continue  # path 层就不沾边的不进候选，也不进诊断（候选=能扯上关系的）
        failed = False
        for name, want in m.get("headers", {}).items():
            if want == "*":  # 约定：值写 "*" = 只要求该 header 存在
                if name not in headers:
                    reasons.append({"id": stub["id"], "reason": f"缺少 header {name}"})
                    failed = True
            elif headers.get(name) != want:
                reasons.append({
                    "id": stub["id"],
                    "reason": f"header {name} 期望 {want!r}，实际 {headers.get(name)!r}",
                })
                failed = True
        for cond in m.get("body", []):
            ok, why = eval_body_condition(cond, body)
            if not ok:
                reasons.append({"id": stub["id"], "reason": why})
                failed = True
        if failed:
            continue
        score = HEADER_SCORE * len(m.get("headers", {})) + BODY_SCORE * len(m.get("body", []))
        if score > best_score:  # 平分不覆盖：后来的规则不改写先定义的应答
            best, best_score = stub, score
    return (best, best_score) if best is not None else (None, reasons)


class MockHandler(BaseHTTPRequestHandler):
    server_version = "DeclarativeMock/1.0"
    stubs = []  # 服务进程内只读，ThreadingHTTPServer 多线程共享无竞争

    def log_message(self, fmt, *args):  # 默认逐请求打日志会淹没演示输出
        pass

    def _send(self, status, payload, extra=None):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def _handle(self, method):
        if method == "GET" and self.path == "/__health__":
            return self._send(200, {"state": "serving", "stubs": len(self.stubs)})
        if method == "GET" and self.path == "/__stats__":
            with LOCK:
                return self._send(200, dict(STATS, loaded=len(self.stubs)))
        if method == "GET" and self.path == "/__stubs__":
            return self._send(200, [
                {"id": s["id"], "source": s["_source"],
                 "score": HEADER_SCORE * len(s["match"].get("headers", {}))
                          + BODY_SCORE * len(s["match"].get("body", [])),
                 "description": s.get("description", "")}
                for s in self.stubs])

        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            body = json.loads(raw) if raw else MISSING
        except json.JSONDecodeError:
            body = MISSING
        headers = {k: v for k, v in self.headers.items()}

        stub, score_or_reasons = match_request(self.stubs, method, self.path, headers, body)
        if stub is None:
            with LOCK:
                STATS["misses"] += 1
            return self._send(404, {
                "error": "no_stub_matched",
                "request": {"method": method, "path": self.path},
                "candidates": score_or_reasons,  # path 命中但约束没过的规则，逐条说为什么
                "hint": "补一条 stub 或修请求；未命中必须响亮，服务端绝不猜一个默认应答",
            })

        with LOCK:
            STATS["hits"] += 1
            STATS["by_stub"][stub["id"]] = STATS["by_stub"].get(stub["id"], 0) + 1
        resp = stub["response"]
        extra = {"X-Mocked-By": stub["id"], "X-Match-Score": str(score_or_reasons)}
        self._send(resp.get("status", 200), resp.get("body", {}), extra)

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")

    def do_DELETE(self):
        self._handle("DELETE")


def main():
    port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 9100
    stub_dir = sys.argv[sys.argv.index("--stubs") + 1] if "--stubs" in sys.argv else "stubs"
    MockHandler.stubs = load_stubs(stub_dir)
    print(f"声明式 mock 已加载 {len(MockHandler.stubs)} 条规则，监听 :{port}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), MockHandler).serve_forever()


if __name__ == "__main__":
    main()
