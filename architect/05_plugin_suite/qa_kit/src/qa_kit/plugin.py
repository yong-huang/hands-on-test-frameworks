"""qa_kit — 公司级 pytest 插件套件。

设计原则：**默认零行为，配置了才生效**。插件通过 pytest11 entry point 全局加载，
所以绝不能在无配置时改变任何套件的行为——这是公司级基建与个人脚本的分水岭
（别的团队装了它，他们的套件必须原样跑）。

三个能力（对应架构师面试题「你们统一沉淀了哪些测试基建」）：
  1. 失败留现场：失败用例自动落 evidence/（traceback + 元数据），排查不用凭记忆复现；
  2. 慢用例打标：超阈值用例进排行报告，慢是漂移来的，要让它可见；
  3. 分层标记：@pytest.mark.smoke/full 分层分发，冒烟层数量与覆盖说话。
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest


def pytest_addoption(parser):
    group = parser.getgroup("qa_kit")
    group.addoption("--qa-evidence-dir", dest="qa_evidence_dir", default=None,
                    help="失败留现场目录；不配置则功能关闭")
    group.addoption("--qa-slow-threshold", dest="qa_slow_threshold", type=float, default=1.0,
                    help="慢用例阈值秒数（默认 1.0）")
    group.addoption("--qa-slow-report", dest="qa_slow_report", default=None,
                    help="慢用例排行 JSON 输出路径；不配置则只打印")


def pytest_configure(config):
    config.addinivalue_line("markers", "smoke: 冒烟层——PR 快反馈必跑")
    config.addinivalue_line("markers", "full: 全量层——夜间/合并跑")
    cfg = config.getpath("inifile") if hasattr(config, "getpath") else None
    config._qa_slow_records = []          # (nodeid, dur)
    config._qa_levels = {"smoke": 0, "full": 0, "unmarked": 0}


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """hookwrapper：拿到每个阶段的测试报告，失败时落现场。

    必须声明 hookwrapper=True：否则 pytest 把本函数当普通 hook 实现，
    函数里的 yield 会把 generator 对象漏给下游插件链（INTERNALERROR）。"""
    outcome = yield
    rep = outcome.get_result()
    if rep.when != "call" or not rep.failed:
        return
    ev_dir = item.config.getoption("qa_evidence_dir")
    if not ev_dir:
        return
    ev = Path(ev_dir)
    ev.mkdir(parents=True, exist_ok=True)
    safe = item.nodeid.replace("::", "__").replace("/", "_")
    lines = [
        f"nodeid: {item.nodeid}",
        f"when: {rep.when}",
        f"outcome: {rep.outcome}",
        f"duration: {getattr(rep, 'duration', 0):.3f}s",
        f"timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"markers: {[m.name for m in item.iter_markers()]}",
        "---- traceback ----",
        str(rep.longrepr),
    ]
    (ev / f"{safe}.txt").write_text("\n".join(lines), encoding="utf-8")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    """记录每条用例的协议级耗时（含 fixture setup，比 call duration 更接近真实成本）。"""
    t0 = time.perf_counter()
    yield
    dur = time.perf_counter() - t0
    item.config._qa_slow_records.append((item.nodeid, dur))
    if item.get_closest_marker("smoke"):
        item.config._qa_levels["smoke"] += 1
    elif item.get_closest_marker("full"):
        item.config._qa_levels["full"] += 1
    else:
        item.config._qa_levels["unmarked"] += 1


def pytest_sessionfinish(session, exitstatus):
    cfg = session.config
    records = sorted(cfg._qa_slow_records, key=lambda x: -x[1])
    threshold = cfg.getoption("qa_slow_threshold")
    slow = [(nid, round(d, 3)) for nid, d in records if d >= threshold]

    print(f"\n=====> [qa_kit] 分层统计：smoke={cfg._qa_levels['smoke']} "
          f"full={cfg._qa_levels['full']} unmarked={cfg._qa_levels['unmarked']}")
    if slow:
        print(f"=====> [qa_kit] 慢用例排行（≥{threshold}s，共 {len(slow)} 条）：")
        for nid, d in slow[:5]:
            print(f"        {d:6.3f}s  {nid}")
    else:
        print(f"=====> [qa_kit] 无慢用例（阈值 {threshold}s）")

    out = cfg.getoption("qa_slow_report")
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(json.dumps({
            "threshold_s": threshold, "total": len(records),
            "slow": slow, "levels": cfg._qa_levels,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"=====> [qa_kit] 慢用例报告已写入 {out}")
