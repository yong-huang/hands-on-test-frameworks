#!/usr/bin/env python3
"""drift.py — 多环境配置矩阵：schema 校验 + 漂移检测。

架构师视角的一句话：**「测试环境和生产不一致导致漏测」的前提，是有人能系统性地
发现不一致**——本工具两件事：
  1. 校验：每个环境配置对 schema 的必填/类型/枚举合规（缺字段报字段名）；
  2. 漂移：三环境逐字段对比，差异分两类——
     expected_diff（本来就应不同：db 地址/日志级别）与
     invariant（必须一致：重试次数/超时/功能开关默认值）——后者出现差异即疑似漂移。
原则：**先声明哪些差异合法，剩下的差异才配叫漂移**。
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import yaml


def load_envs(env_dir: Path) -> dict[str, dict]:
    envs = {}
    for f in sorted(env_dir.glob("*.yaml")):
        envs[f.stem] = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
    return envs


def flat(d: dict, prefix: str = "") -> dict:
    out = {}
    for k, v in (d or {}).items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(flat(v, key + "."))
        else:
            out[key] = v
    return out


def validate(flat_cfg: dict, schema: dict) -> list[str]:
    errs = []
    for field, rule in schema["required"].items():
        if field not in flat_cfg:
            errs.append(f"缺少必填字段 {field}")
            continue
        v = flat_cfg[field]
        t = rule.get("type")
        type_ok = {int: lambda x: isinstance(x, int) and not isinstance(x, bool),
                   str: lambda x: isinstance(x, str),
                   bool: lambda x: isinstance(x, bool)}.get(t, lambda x: True)(v)
        if not type_ok:
            errs.append(f"字段 {field} 类型错误：期望 {t}，实际 {v!r}")
            continue
        if "enum" in rule and v not in rule["enum"]:
            errs.append(f"字段 {field} 非法值 {v!r}（合法：{rule['enum']}）")
        if "pattern" in rule and not __import__("re").match(rule["pattern"], str(v)):
            errs.append(f"字段 {field} 不匹配 {rule['pattern']}：{v!r}")
        if "min" in rule and v < rule["min"] or "max" in rule and v > rule.get("max", v):
            errs.append(f"字段 {field} 越界：{v!r}（{rule.get('min','-')}~{rule.get('max','-')}）")
    return errs


def drift_matrix(envs_flat: dict[str, dict], schema: dict) -> list[dict]:
    fields = sorted({k for cfg in envs_flat.values() for k in cfg})
    rows = []
    for field in fields:
        values = {e: cfg.get(field, "<缺失>") for e, cfg in envs_flat.items()}
        differs = len(set(map(repr, values.values()))) > 1
        kind = "一致"
        if differs:
            kind = ("预期差异" if field in schema["expected_diff"]
                    else "⚠️ 疑似漂移" if field in schema["invariant"] else "未声明字段")
        rows.append({"field": field, "values": values, "kind": kind})
    return rows


def render(envs: list[str], errs: dict[str, list[str]], rows: list[dict]) -> str:
    lines = ["# 🧭 多环境配置矩阵与漂移报告",
             f"> {time.strftime('%Y-%m-%d %H:%M:%S')} · 环境 {len(envs)} 个 · "
             f"字段 {len(rows)} 个", ""]
    if any(errs.values()):
        lines.append("## ❌ Schema 校验失败")
        for env, es in errs.items():
            for e in es:
                lines.append(f"- [{env}] {e}")
        lines.append("")
    drift = [r for r in rows if r["kind"] != "一致"]
    lines += ["## 逐字段矩阵（差异分类）", "",
              "| 字段 | " + " | ".join(envs) + " | 分类 |", "|:---|" + ":---:|" * (len(envs) + 1)]
    for r in rows:
        vals = [str(r["values"].get(e, "<缺失>"))[:34] for e in envs]
        lines.append(f"| {r['field']} | " + " | ".join(vals) + f" | {r['kind']} |")
    n_drift = sum(1 for r in drift if "漂移" in r["kind"])
    lines += ["", f"> 共 {len(drift)} 处差异：预期差异 "
              f"{len(drift) - n_drift} 处（schema 声明合法），疑似漂移 {n_drift} 处"
              "（invariant 字段必须三环境一致）", ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="多环境配置矩阵与漂移检测")
    base = Path(__file__).parent
    ap.add_argument("--env-dir", default=str(base / "configs/environments"))
    ap.add_argument("--schema", default=str(base / "configs/schema.yaml"))
    ap.add_argument("--strict", action="store_true", help="疑似漂移也判失败")
    ap.add_argument("--out", default=str(base / "reports"))
    args = ap.parse_args()

    schema = yaml.safe_load(Path(args.schema).read_text(encoding="utf-8"))
    envs = load_envs(Path(args.env_dir))
    envs_flat = {e: flat(c) for e, c in envs.items()}
    errs = {e: validate(cfg, schema) for e, cfg in envs_flat.items()}
    rows = drift_matrix(envs_flat, schema)

    n_drift = sum(1 for r in rows if "漂移" in r["kind"])
    has_err = any(errs.values())
    ok = not has_err and not (args.strict and n_drift)
    md = render(list(envs), errs, rows)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "drift.md").write_text(md, encoding="utf-8")
    (out / "drift.json").write_text(json.dumps(
        {"errors": errs, "rows": rows, "drift_count": n_drift},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(md)
    print(f">>> 报告已写入 {out/'drift.md'}；裁决 {'✅' if ok else '❌'}（exit {0 if ok else 1}）")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
