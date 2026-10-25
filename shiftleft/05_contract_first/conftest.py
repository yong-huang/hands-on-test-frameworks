"""pytest 会话钩子：起停被测实现（uvicorn 子进程）+ 统计实际执行的案例数。

APP_IMPL 环境变量选实现：good（默认）/ bad。CONTRACT 环境变量选契约文件。
案例计数从测试模块回写到这里的 RUN_STATS，跑完打印——「≥50 examples」是
实测数字，不是推断值。
"""
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
PY = str(ROOT.parent.parent / ".venv/bin/python")
PORT = 8933
BASE_URL = f"http://127.0.0.1:{PORT}"

RUN_STATS = {"cases": 0}


@pytest.fixture(scope="session")
def base_url(request):
    impl = os.environ.get("APP_IMPL", "good")
    env = dict(os.environ, APP_IMPL=impl, PYTHONUNBUFFERED="1")
    # 端口残留防护：先摘掉孤儿监听再起
    subprocess.run(f"lsof -ti :{PORT} | xargs kill 2>/dev/null", shell=True, capture_output=True)
    proc = subprocess.Popen(
        [PY, "-m", "uvicorn", f"app_{impl}:app", "--host", "127.0.0.1",
         "--port", str(PORT), "--log-level", "warning"],
        cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(80):
        try:
            with urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=1) as r:
                if r.status == 200:
                    break
        except Exception:
            time.sleep(0.1)
    else:
        proc.kill()
        raise RuntimeError(f"被测实现 app_{impl} 启动失败")
    yield BASE_URL
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def pytest_terminal_summary(terminalreporter):
    n = RUN_STATS["cases"]
    terminalreporter.section("schemathesis 执行规模")
    terminalreporter.write_line(f"实际执行生成案例：{n} 条")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    outcome = yield
    # schemathesis 每个操作生成一个 pytest 项；执行完从其 hypothesis 统计里拿不到
    # 细粒度计数，改为在测试体内累加（见 test_contract.py），此处无需处理
    _ = outcome, item
