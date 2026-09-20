#!/usr/bin/env python3
"""dsl.py — YAML DSL 接口用例引擎（httprunner 思想 mini 版）。

架构师视角的一句话：**DSL 的价值不在省行数，在把「写用例」的门槛从会编程降到会业务**——
但门槛降多少、可读性亏多少，要拿数据说话（本实验与 pytest 版同场景对比）。

支持能力（刻意保持最小集，够用即可）：
  - 变量：${var} 替换 + 内置 ${__uuid}；
  - 提取：extract 把响应写回变量（迷你 jsonpath：$.a.b[0]，响应信封 $.status_code/$.headers/$.json/$.text）；
  - 断言：eq / contains / len_le / exists；
  - 报错定位：断言失败指向 YAML 文件名 + 用例所在行号（平台用户不读 traceback）。

用法：
  python dsl.py [--cases configs/cases.yaml]     # 跑 DSL 用例，退出码 0/1
"""
from __future__ import annotations

import argparse
import re
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import httpx
import yaml

VAR_RE = re.compile(r"\$\{(\w+)\}")


# ---------------------------------------------------------------- 迷你 jsonpath
def resolve(path: str, ctx: dict):
    """$.a.b[0] → 逐段下钻；根键固定 status_code/headers/json/text，缺失抛 KeyError。"""
    assert path.startswith("$."), f"路径必须以 $. 开头：{path}"
    node = ctx
    for seg in path[2:].replace("]", "").replace("[", ".").split("."):
        if seg == "":
            continue
        node = node[int(seg)] if isinstance(node, list) else node[seg]
    return node


# ---------------------------------------------------------------- 变量与行号
def substitute(value, variables: dict):
    if isinstance(value, str):
        m = VAR_RE.fullmatch(value)
        if m:                       # 整串就是变量：保留原始类型（int 比较才不出 3=="3"）
            name = m.group(1)
            return variables[name] if name in variables else str(uuid.uuid4())[:8]

        def repl(mm):               # 混在长字符串里：str 化拼接
            name = mm.group(1)
            return str(variables[name]) if name in variables else str(uuid.uuid4())[:8]
        return VAR_RE.sub(repl, value)
    if isinstance(value, dict):
        return {k: substitute(v, variables) for k, v in value.items()}
    if isinstance(value, list):
        return [substitute(v, variables) for v in value]
    return value


def find_line(raw: str, case_name: str) -> int:
    """在 YAML 原文里找用例 name 所在行——报错定位的行号来源。"""
    for i, line in enumerate(raw.splitlines(), 1):
        if line.strip() == f"- name: {case_name}":
            return i
    return 0


# ---------------------------------------------------------------- 断言
@dataclass
class DslError(Exception):
    case: str
    line: int
    reason: str
    def __str__(self):
        return f"{self.case}（{self.path_line()}）{self.reason}"

    def path_line(self) -> str:
        return f"configs/cases.yaml:{self.line}" if self.line else "configs/cases.yaml"


def run_validate(v: dict, ctx: dict) -> str | None:
    (op, args), = v.items()
    if op == "eq":
        actual = resolve(args[0], ctx)
        return None if actual == args[1] else f"断言 eq 失败：{args[0]} 实际={actual!r} 期望={args[1]!r}"
    if op == "contains":
        actual = str(resolve(args[0], ctx))
        return None if args[1] in actual else f"断言 contains 失败：{args[0]} 实际={actual!r} 应含 {args[1]!r}"
    if op == "len_le":
        actual = resolve(args[0], ctx)
        return None if len(actual) <= args[1] else f"断言 len_le 失败：{args[0]} 长度={len(actual)} 上限={args[1]}"
    if op == "exists":
        try:
            resolve(args[0], ctx)
            return None
        except (KeyError, IndexError, TypeError):
            return f"断言 exists 失败：{args[0]} 不存在"
    return f"未知断言类型 {op}"


# ---------------------------------------------------------------- 执行器
@dataclass
class CaseResult:
    name: str
    line: int
    ok: bool
    detail: str = ""
    ms: int = 0

    def path_line(self) -> str:
        return f"configs/cases.yaml:{self.line}" if self.line else "configs/cases.yaml"


def run_case(case: dict, line: int, base_url: str, variables: dict, client: httpx.Client) -> CaseResult:
    """variables 是会话级共享字典：本用例 extract 出的变量，后续用例直接可用。"""
    ctx: dict = {}
    req = substitute(case["request"], variables)
    t0 = time.perf_counter()
    r = client.request(req["method"], req["url"],
                       json=req.get("json"), timeout=10)
    ms = int((time.perf_counter() - t0) * 1000)
    ctx.update({"status_code": r.status_code,
                "headers": {k.lower(): v for k, v in r.headers.items()},
                "json": _safe_json(r), "text": r.text})

    for var, path in (case.get("extract") or {}).items():
        variables[var] = resolve(substitute(path, variables), ctx)

    for v in case.get("validate") or []:
        v = substitute(v, variables)
        reason = run_validate(v, ctx)
        if reason:
            return CaseResult(case["name"], line, False, reason, ms)
    return CaseResult(case["name"], line, True, "", ms)


def _safe_json(r: httpx.Response):
    try:
        return r.json()
    except Exception:
        return {}


def main() -> int:
    ap = argparse.ArgumentParser(description="YAML DSL 接口用例引擎")
    base = Path(__file__).parent
    ap.add_argument("--cases", default=str(base / "configs/cases.yaml"))
    args = ap.parse_args()

    raw = Path(args.cases).read_text(encoding="utf-8")
    doc = yaml.safe_load(raw)
    cfg = doc.get("config", {})
    variables = {k: substitute(v, {}) for k, v in (doc.get("variables") or {}).items()}

    results: list[CaseResult] = []
    with httpx.Client(base_url=cfg.get("base_url", "http://127.0.0.1:8899")) as client:
        for case in doc["testcases"]:
            line = find_line(raw, case["name"])
            try:
                results.append(run_case(case, line, cfg.get("base_url", ""), variables, client))
            except Exception as e:                      # 请求层异常也归到 YAML 行号
                results.append(CaseResult(case["name"], line, False,
                                          f"请求异常：{type(e).__name__}: {e}"))

    print(f"# {cfg.get('name', 'DSL 用例')} — {len(results)} 条")
    for r in results:
        mark = "✅" if r.ok else "❌"
        print(f"{mark} [{r.ms:>4}ms] {r.name}" + ("" if r.ok else f" → {r.detail}（定位 {r.path_line()}）"))
    failed = [r for r in results if not r.ok]
    print(f"\n{len(results)-len(failed)} passed, {len(failed)} failed")
    if failed:
        print(f"\n首个失败定位：{failed[0].path_line()}（用例「{failed[0].name}」）——改 YAML 即可，无需读 traceback")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
