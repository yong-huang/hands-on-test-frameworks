"""pytest-ministore-report —— 教学用自定义 pytest 插件（lab 10 产出物）。

三个能力（全部只在 --ministore 开启时生效，绝不打扰其他项目）：
1. marker 校验：@pytest.mark.ministore_tier(tier=...) 的 tier 必须合法
2. 自动给慢用例打 slow 标并记账
3. 失败用例自动落一份上下文 JSON，供事后分析
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

VALID_TIERS = {"smoke", "core", "slow"}


# ---------------------------------------------------------------------------
# 配置项：pytest --ministore --ministore-slow-threshold 0.1
# ---------------------------------------------------------------------------
def pytest_addoption(parser):
    group = parser.getgroup("ministore")
    group.addoption("--ministore", action="store_true", help="启用 ministore 报告插件")
    group.addoption(
        "--ministore-slow-threshold",
        type=float,
        default=0.1,
        help="超过该秒数的用例自动记为 slow（默认 0.1）",
    )


# ---------------------------------------------------------------------------
# marker 注册与校验：注册要趁早（pytest_configure），校验在收集期
# ---------------------------------------------------------------------------
def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "ministore_tier(tier): 用例分层标记，tier ∈ smoke|core|slow",
    )
    if config.getoption("--ministore"):
        config._ministore = {"slow": [], "failed": []}


def pytest_collection_modifyitems(config, items):
    """收集期校验：tier 非法直接 UsageError——配置错误要在最早的时刻炸出来"""
    if not config.getoption("--ministore"):
        return
    for item in items:
        marker = item.get_closest_marker("ministore_tier")
        if marker and marker.kwargs.get("tier") not in VALID_TIERS:
            raise pytest.UsageError(
                f"[ministore] {item.nodeid} 的 tier 必须是 {'/'.join(sorted(VALID_TIERS))}，"
                f"收到的是 {marker.kwargs.get('tier')!r}"
            )


import pytest


# ---------------------------------------------------------------------------
# 核心钩子：runtest_makereport —— 每个阶段的 setup/call/teardown 都会产生一份报告
# ---------------------------------------------------------------------------
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """hookwrapper 拿到真正的 test report，从而知道失败与否与耗时。

    这里是"失败自动留痕"类插件的标准插桩点：call.when == 'call' 表示
    用例函数本体执行完毕。
    """
    outcome = yield
    rep = outcome.get_result()
    if not item.config.getoption("--ministore"):
        return
    store = item.config._ministore

    if rep.when == "call":
        if rep.failed:
            ctx = {
                "nodeid": item.nodeid,
                "when": rep.when,
                "duration_s": round(rep.duration, 4),
                "exception": str(rep.longreprtext)[:2000],
                "keywords": sorted(k for k in item.keywords if not k.startswith("_")),
            }
            ctx_dir = Path(item.config.rootpath) / "contexts"
            ctx_dir.mkdir(exist_ok=True)
            safe = item.nodeid.replace("::", "__").replace("/", "_").replace("[", "_").replace("]", "")
            (ctx_dir / f"{safe}.json").write_text(
                json.dumps(ctx, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            store["failed"].append(item.nodeid)

        # 慢用例自动打标 + 记账（阈值为 0 的边界由比较符自然处理）
        threshold = item.config.getoption("--ministore-slow-threshold")
        if rep.duration > threshold:
            item.add_marker("slow")
            store["slow"].append({"nodeid": item.nodeid, "duration_s": round(rep.duration, 4)})


def pytest_sessionfinish(session, exitstatus):
    """会话收尾：汇总落一份 ministore-report.json"""
    if not getattr(session.config, "_ministore", None):
        return
    store = session.config._ministore
    report = {
        "plugin": "pytest-ministore-report",
        "exitstatus": int(exitstatus),
        "slow_threshold_s": session.config.getoption("--ministore-slow-threshold"),
        "slow": store["slow"],
        "failed": store["failed"],
    }
    out = Path(session.config.rootpath) / "ministore-report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """终端摘要：摘要类输出走官方钩子，不要碰私有属性"""
    if not getattr(config, "_ministore", None):
        return
    store = config._ministore
    terminalreporter.section("ministore report", sep="=")
    terminalreporter.write_line(
        f"slow={len(store['slow'])}  failed={len(store['failed'])}  -> ministore-report.json"
    )
