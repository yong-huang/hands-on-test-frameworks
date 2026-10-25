"""项目 16 验收：跑 hunt 闭环，断言 检出≥2 / 零误报 / 隔离后零失败。"""
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
PY = HERE.parent.parent / ".venv" / "bin" / "python"


def test_flaky_governance_loop():
    r = subprocess.run([str(PY), str(HERE / "hunt.py")], capture_output=True, text=True, timeout=900)
    print(r.stdout[-600:])
    flaky = json.loads((HERE / "reports" / "flaky.json").read_text(encoding="utf-8"))
    assert len(flaky["detected"]) >= 2, f"两个植入 flaky 应全部检出：{flaky['detected']}"
    assert flaky["stable_zero_false_positive"], "稳定对照出现误报"
    assert flaky["confirm_failures"] == 0, "隔离后确认轮仍有失败"
    assert any("random_flake" in d for d in flaky["detected"])
    assert any("order_dependent" in d for d in flaky["detected"])
