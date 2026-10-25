"""test_perf_budget.py —— pytest 包装：让预算检查可进 CI（pytest 退出码即门禁）。

引擎在 perf_budget.py（standalone 可跑）；本文件通过 subprocess 调用并
断言退出码，保持「引擎与测试分离」——CI 可以只用引擎，pytest 只管红绿。
"""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = str(ROOT.parent.parent / ".venv/bin/python")


def test_perf_budget_all_pass():
    """正常 SUT 下预算全达标（不含 slow-config 延迟端点）。"""
    r = subprocess.run([PY, str(ROOT / "perf_budget.py")],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"预算检查失败：\n{r.stdout[-500:]}"
