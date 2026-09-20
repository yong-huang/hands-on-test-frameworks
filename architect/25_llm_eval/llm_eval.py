#!/usr/bin/env python3
"""llm_eval.py — LLM 用例生成与质量评测：AI 生成的测试敢不敢用，先造一台量尺。

架构师视角的一句话：**LLM 生成的测试不能直接进主干，但也不能一棍打死——需要一台
四维量尺**：可执行性（不改就能跑）、断言有效性（期望值与真实行为一致）、边界覆盖
（规格里的边界维度盖了几个）、重复率（换皮用例是噪音）。量尺合格才允许进「人工
审核池」，这是 AI 时代测试架构的务实姿态。

双模式：
  mock（默认）：确定性模板生成——离线可跑，量尺本身的回归靠它；
  --llm：OpenAI 兼容接口（LLM_BASE_URL/LLM_API_KEY/LLM_MODEL 环境变量）真实生成。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path

import httpx
import yaml

BASE = Path(__file__).parent
SUT = "http://127.0.0.1:8899"


# ---------------------------------------------------------------- 生成：mock
def generate_mock(spec: dict) -> list[dict]:
    """确定性边界模板生成：规格里每个 boundary 维度至少一条用例。"""
    cases = [
        {"name": "正常下单", "method": "POST", "path": "/api/orders",
         "payload": {"customer": "评测用户", "item": "商品A", "qty": 1, "price": 9.9},
         "expect_status": 201, "boundary": ["正常值"]},
        {"name": "qty 为零", "method": "POST", "path": "/api/orders",
         "payload": {"customer": "评测用户", "item": "商品A", "qty": 0, "price": 9.9},
         "expect_status": 422, "boundary": ["零"]},
        {"name": "qty 为负", "method": "POST", "path": "/api/orders",
         "payload": {"customer": "评测用户", "item": "商品A", "qty": -1, "price": 9.9},
         "expect_status": 422, "boundary": ["负数"]},
        {"name": "price 为零（规格未禁，真实 201）", "method": "POST", "path": "/api/orders",
         "payload": {"customer": "评测用户", "item": "商品A", "qty": 1, "price": 0},
         "expect_status": 201, "boundary": ["零"]},
        {"name": "customer 空串", "method": "POST", "path": "/api/orders",
         "payload": {"customer": "", "item": "商品A", "qty": 1, "price": 9.9},
         "expect_status": 422, "boundary": ["空串"]},
        {"name": "customer 缺失", "method": "POST", "path": "/api/orders",
         "payload": {"item": "商品A", "qty": 1, "price": 9.9},
         "expect_status": 422, "boundary": ["缺失"]},
        {"name": "item 缺失", "method": "POST", "path": "/api/orders",
         "payload": {"customer": "评测用户", "qty": 1, "price": 9.9},
         "expect_status": 422, "boundary": ["缺失"]},
        {"name": "查询不存在订单", "method": "GET", "path": "/api/orders/999999",
         "expect_status": 404, "boundary": ["缺失"]},
        {"name": "删除不存在订单", "method": "DELETE", "path": "/api/orders/999999",
         "expect_status": 404, "boundary": ["缺失"]},
        {"name": "下单后查询", "method": "POST", "path": "/api/orders",
         "payload": {"customer": "评测用户", "item": "商品B", "qty": 2, "price": 5.0},
         "expect_status": 201, "boundary": ["正常值"], "then": "GET"},
    ]
    return cases


# ---------------------------------------------------------------- 生成：LLM
LLM_PROMPT = """你是测试工程师。针对下面的 API 规格，生成 10 条边界测试用例，输出 JSON 数组，
每条格式：{{"name","method","path","payload","expect_status","boundary":["..."]}}。
注意 price=0 规格未禁止，应期望 201。规格：
{spec}
只输出 JSON。"""


def generate_llm(spec: dict) -> list[dict]:
    base = os.environ.get("LLM_BASE_URL")
    model = os.environ.get("LLM_MODEL")
    key = os.environ.get("LLM_API_KEY", "EMPTY")
    if not (base and model):
        raise SystemExit("真实模式需环境变量 LLM_BASE_URL/LLM_MODEL（可选 LLM_API_KEY）；"
                         "未配置请用 mock 模式")
    with httpx.Client(timeout=120) as c:
        r = c.post(f"{base.rstrip('/')}/chat/completions", headers={"Authorization": f"Bearer {key}"},
                   json={"model": model, "temperature": 0.3,
                         "messages": [{"role": "user", "content": LLM_PROMPT.format(spec=json.dumps(spec, ensure_ascii=False))}]})
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"]
    m = re.search(r"\[.*\]", text, re.S)
    if not m:
        raise SystemExit("LLM 返回中未找到 JSON 数组")
    return json.loads(m.group(0))


# ---------------------------------------------------------------- 评测四维
def evaluate(cases: list[dict]) -> dict:
    executed, matched = 0, 0
    boundaries_seen: set[str] = set()
    sigs: set[str] = []
    dup = 0
    details = []
    with httpx.Client(timeout=5, trust_env=False) as c:
        for case in cases:
            try:
                r = c.request(case["method"], SUT + case["path"],
                              json=case.get("payload"), timeout=5)
                if case["method"] == "POST" and r.status_code == 201:
                    c.delete(f"{SUT}/api/orders/{r.json()['id']}")
                ok_exec = True
                status_match = r.status_code == case.get("expect_status")
            except Exception as e:
                ok_exec, status_match = False, False
                case["error"] = str(e)[:80]
            executed += ok_exec
            matched += status_match
            boundaries_seen |= set(case.get("boundary", []))
            sig = f"{case['method']}:{case['path']}:{json.dumps(case.get('payload', {}), sort_keys=True)}"
            if sig in sigs:
                dup += 1
            sigs.append(sig)
            details.append({"name": case.get("name"), "ok_exec": ok_exec,
                            "status_match": status_match,
                            "actual": getattr(r, "status_code", "EXC")})
    n = max(len(cases), 1)
    spec_boundaries = {"空串", "缺失", "零", "负数", "正常值"}
    return {
        "total": len(cases),
        "executability_pct": round(executed * 100 / n),
        "assert_validity_pct": round(matched * 100 / n),
        "boundary_coverage_pct": round(len(boundaries_seen & spec_boundaries) * 100 / len(spec_boundaries)),
        "duplication_pct": round(dup * 100 / n),
        "details": details,
    }


def render(scores: dict, mode: str) -> str:
    verdict = ("✅ 可进入人工审核池" if scores["executability_pct"] >= 80 and scores["duplication_pct"] <= 20
               else "❌ 不建议直接采用")
    return f"""# 🤖 LLM 用例生成评测报告（模式：{mode}）
> {time.strftime('%Y-%m-%d %H:%M:%S')} · 生成 {scores['total']} 条 · 判定：{verdict}

| 维度 | 得分 | 说明 |
|:---|:---:|:---|
| 可执行性 | {scores['executability_pct']}% | 不改代码即可发出的比例 |
| 断言有效性 | {scores['assert_validity_pct']}% | 期望状态码与真实行为一致的比例 |
| 边界覆盖 | {scores['boundary_coverage_pct']}% | 规格边界维度（空串/缺失/零/负数/正常）的覆盖 |
| 重复率 | {scores['duplication_pct']}% | 同方法+路径+payload 签名的重复（验收 ≤20%） |

判定规则：可执行性 ≥80% 且重复率 ≤20% → 进人工审核池；否则打回重新生成。
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="LLM 用例生成与质量评测")
    ap.add_argument("--llm", action="store_true", help="真实 LLM 生成（默认 mock）")
    ap.add_argument("--out", default=str(BASE / "reports"))
    args = ap.parse_args()

    spec = yaml.safe_load((BASE / "configs/api_spec.yaml").read_text(encoding="utf-8"))
    mode = "llm" if args.llm else "mock"
    cases = generate_llm(spec) if args.llm else generate_mock(spec)

    scores = evaluate(cases)
    md = render(scores, mode)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "llm_eval.md").write_text(md, encoding="utf-8")
    (out / "llm_eval.json").write_text(json.dumps(scores, ensure_ascii=False, indent=2),
                                       encoding="utf-8")
    print(md)
    print(f">>> 报告已写入 {out/'llm_eval.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
