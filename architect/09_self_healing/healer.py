#!/usr/bin/env python3
"""healer.py — 自愈 UI 定位器：定位策略链 + 历史档案 + 自愈报告。

架构师视角的一句话：**UI 自动化的脆不在测试在耦合**——用例绑死 id/class，前端一改版
全红。自愈的本质是把「定位」从单点选择器升级为带记忆的策略链：
  css(原定位) → role(ARIA 语义) → placeholder → 文本 → 档案(上次自愈结果)。
命中即记录进档案，下次直接走档案——组件改版第一轮自愈，第二轮免愈。
**语义也没了就如实报红**：自愈是容错，不是包容任意改版（误 healing 比 fail 更危险）。
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from playwright.sync_api import Page, TimeoutError as PWTimeout

ARCHIVE = Path(__file__).parent / "reports" / "locator_archive.json"
REPORT = Path(__file__).parent / "reports" / "healing_report.json"


@dataclass
class HealAttempt:
    page: str
    key: str                      # 业务语义键：客户名输入框/提交按钮…
    strategy: str = ""
    healed: bool = False
    tried: list[str] = field(default_factory=list)


def load_archive() -> dict:
    if ARCHIVE.exists():
        return json.loads(ARCHIVE.read_text(encoding="utf-8"))
    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    return {}


def save_archive(arch: dict) -> None:
    ARCHIVE.write_text(json.dumps(arch, ensure_ascii=False, indent=2), encoding="utf-8")


def _resolve(page: Page, strategy: str, arg):
    """按策略生成定位器并要求可见（可见才算命中，防假阳性）。"""
    if strategy == "css":
        loc = page.locator(arg)
    elif strategy == "placeholder":
        loc = page.get_by_placeholder(arg)
    elif strategy == "role":
        loc = page.get_by_role(arg[0], name=arg[1])
    elif strategy == "label":
        loc = page.get_by_text(arg, exact=False)
    elif strategy == "archive":
        return None                                   # 调用方已查过档案
    else:
        raise ValueError(strategy)
    loc = loc.first
    loc.wait_for(state="visible", timeout=1200)
    return loc


def find(page: Page, page_name: str, key: str,
         strategies: list[tuple], report: list[HealAttempt]):
    """策略链定位：档案 → 各策略；命中即返回定位器并记录自愈事件。"""
    att = HealAttempt(page=page_name, key=key)
    report.append(att)
    arch = load_archive()

    cached = arch.get(page_name, {}).get(key)
    if cached:
        att.tried.append(f"archive:{cached}")
        try:
            loc = _resolve(page, "css", cached)
            if loc is not None:
                att.strategy, att.healed = "archive", True
                return loc
        except PWTimeout:
            pass

    for strategy, arg in strategies:
        att.tried.append(f"{strategy}:{arg if not isinstance(arg, tuple) else arg[1]}")
        try:
            loc = _resolve(page, strategy, arg)
        except PWTimeout:
            continue
        if loc is not None:
            att.strategy = strategy
            att.healed = strategy != strategies[0][0]   # 首选策略命中不算自愈
            if strategy != strategies[0][0]:
                arch.setdefault(page_name, {})[key] = _css_of(loc, page)
                save_archive(arch)                       # 记住自愈结果，下次免愈
            return loc
    raise AssertionError(f"定位彻底失败：{page_name} 的「{key}」试尽策略链 {att.tried}")


def _css_of(loc, page: Page) -> str:
    """从命中元素反推一个稳定 css（用 name/placeholder 属性拼）。"""
    for attr in ("name", "id", "placeholder"):
        v = loc.get_attribute(attr)
        if v:
            return f"[{attr}=\"{v}\"]"
    return "body"


def write_report(report: list[HealAttempt]) -> dict:
    healed = sum(1 for a in report if a.healed)
    located = sum(1 for a in report if a.healed or a.strategy)
    failed = sum(1 for a in report if not a.strategy)
    summary = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "attempts": len(report),
        "first_try": located - healed,
        "healed": healed,
        "failed": failed,
        "heal_rate_of_mutants": None,
        "events": [a.__dict__ for a in report],
    }
    mutants = [a for a in report if a.page.startswith("v")]
    if mutants:
        summary["heal_rate_of_mutants"] = round(
            sum(1 for a in mutants if a.healed or a.strategy) / len(mutants), 2)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


CUSTOMER = [("css", "#customer"), ("role", ("textbox", "客户名")),
            ("placeholder", "客户名"), ("label", "客户名")]
ITEM = [("css", "#item"), ("role", ("textbox", "商品")),
        ("placeholder", "商品"), ("label", "商品")]
SUBMIT = [("css", "#submitBtn"), ("role", ("button", "提交订单")),
          ("label", "提交订单")]
