"""gates/_server.py —— 起停 mini API 的公共帮手（下划线开头，不是关卡）。

每个需要 HTTP 的关卡（4/5）用独立端口起自己的服务实例，跑完即停，
互不串台；启动前顺手清掉端口上的残留监听（同 architect/01 的清理手法）。
"""
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

DEFECT_DIR = Path(__file__).resolve().parents[1] / "defect"


def start(impl: str, port: int):
    """起 uvicorn（被测实现由 PRICING_IMPL 环境变量注入），轮询健康检查就绪。"""
    # 清残留：上一个实验轮次若留下孤儿监听，先摘掉再起，避免打到旧实现上
    subprocess.run(["lsof", "-ti", f":{port}"], capture_output=True)
    subprocess.run("lsof -ti :%d | xargs kill 2>/dev/null" % port,
                   shell=True, capture_output=True)
    env = dict(os.environ, PRICING_IMPL=impl, PYTHONUNBUFFERED="1")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api_app:app",
         "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
        cwd=DEFECT_DIR, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}"
    for _ in range(80):  # 轮询而非裸 sleep，最多约 8s
        try:
            with urllib.request.urlopen(f"{base}/api/health", timeout=1) as r:
                if r.status == 200:
                    return proc, base
        except Exception:
            time.sleep(0.1)
    proc.kill()
    raise RuntimeError(f"mini API 启动失败（port {port}）")


def stop(proc):
    """停服并回收进程，两种信号兜底，不留孤儿。"""
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
