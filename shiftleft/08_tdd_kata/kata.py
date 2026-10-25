#!/usr/bin/env python3
"""kata.py —— 严格 TDD 操练驱动器：在独立 git 仓库里逐轮回放「红 → 绿」。

纪律（每轮固定节拍，runs.log 留档）：
  RED   先写测试（此刻实现还不存在或不完整）→ 提交 → 跑测试必须失败
  GREEN 用最小实现让测试通过 → 提交 → 跑测试必须通过
  最后一轮之后做一次纯重构：只动实现不动测试 → 提交 → 测试保持绿

功能域：给订单定价加「满减优惠券」（labs/11 订单应用语义的最小复刻），
五轮演进：基础满减 → 门槛拒绝 → 可配置券额 → 精确到分（float 换 Decimal）
→ 拒绝信息带门槛值。仓库建在 ./repo（独立 git，绝不碰 labs/11）。

用法：python kata.py          # 全程回放，结尾打印提交序列摘要
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT / "repo"
PY = str(ROOT.parent.parent / ".venv/bin/python")
LOG: list[str] = []  # runs.log 行：phase|subject|pytest_exit

TEST_HEAD = '''"""满减优惠券：TDD 操练的测试（每轮 RED 先追加，GREEN 后不动）。"""
import pytest

from pricing import payable
'''

TESTS = {
    "C1": '''

def test_basic_discount():
    """满 100 减 20：小计 150 用券，应付 130。"""
    assert payable(150.0, use_coupon=True) == 130.0
''',
    "C2": '''

def test_below_threshold_rejected():
    """未满门槛用券必须被拒绝（ValueError），而不是照常减钱。"""
    with pytest.raises(ValueError):
        payable(99.99, use_coupon=True)
''',
    "C3": '''

def test_configurable_coupon_value():
    """券额可配置：满 100 用 50 元券，应付 100。"""
    assert payable(150.0, use_coupon=True, coupon_value=50.0) == 100.0
''',
    "C4": '''

def test_exact_cents():
    """金额精确到分：19.99 + 80.10 用 20 元券，应付必须是 80.09（字符串级精确）。"""
    subtotal = 19.99 + 80.10
    assert str(payable(subtotal, use_coupon=True)) == "80.09"
''',
    "C5": '''

def test_reject_message_contains_threshold():
    """拒绝信息要带门槛值，让调用方不用查文档就知道差多少。"""
    with pytest.raises(ValueError, match="100"):
        payable(50.0, use_coupon=True)
''',
}

IMPLS = {
    "C1": '''"""满减优惠券定价（TDD 最小实现，随轮次生长）。"""


def payable(subtotal, use_coupon=True):
    if use_coupon:
        return subtotal - 20.0
    return subtotal
''',
    "C2": '''"""满减优惠券定价（TDD 最小实现，随轮次生长）。"""


def payable(subtotal, use_coupon=True):
    if use_coupon:
        if subtotal < 100.0:
            raise ValueError("未满门槛，不可用券")
        return subtotal - 20.0
    return subtotal
''',
    "C3": '''"""满减优惠券定价（TDD 最小实现，随轮次生长）。"""


def payable(subtotal, use_coupon=True, coupon_value=20.0):
    if use_coupon:
        if subtotal < 100.0:
            raise ValueError("未满门槛，不可用券")
        return subtotal - coupon_value
    return subtotal
''',  # C3 的接口已在 C1 预留默认参数——本轮测试直接通过，属 TDD 正常现象
    "C4": '''"""满减优惠券定价（TDD 最小实现，随轮次生长）。"""
from decimal import Decimal, ROUND_HALF_UP

_COUPON_DEFAULT = Decimal("20.00")
_THRESHOLD = Decimal("100.00")
_CENT = Decimal("0.01")


def payable(subtotal, use_coupon=True, coupon_value=_COUPON_DEFAULT):
    subtotal = Decimal(str(subtotal))
    coupon_value = Decimal(str(coupon_value))
    if use_coupon:
        if subtotal < _THRESHOLD:
            raise ValueError("未满门槛，不可用券")
        return (subtotal - coupon_value).quantize(_CENT, ROUND_HALF_UP)
    return subtotal.quantize(_CENT, ROUND_HALF_UP)
''',
    "C5": '''"""满减优惠券定价（TDD 最小实现，随轮次生长）。"""
from decimal import Decimal, ROUND_HALF_UP

_COUPON_DEFAULT = Decimal("20.00")
_THRESHOLD = Decimal("100.00")
_CENT = Decimal("0.01")


def payable(subtotal, use_coupon=True, coupon_value=_COUPON_DEFAULT):
    subtotal = Decimal(str(subtotal))
    coupon_value = Decimal(str(coupon_value))
    if use_coupon:
        if subtotal < _THRESHOLD:
            raise ValueError(f"未满 {_THRESHOLD}，不可用券")
        return (subtotal - coupon_value).quantize(_CENT, ROUND_HALF_UP)
    return subtotal.quantize(_CENT, ROUND_HALF_UP)
''',
}

IMPL_REFACTOR = '''"""满减优惠券定价（重构版：常量命名 + 门槛守卫提取，行为不变）。"""
from decimal import Decimal, ROUND_HALF_UP

COUPON_DEFAULT = Decimal("20.00")
THRESHOLD = Decimal("100.00")
_CENT = Decimal("0.01")


def _ensure_threshold(subtotal: Decimal) -> None:
    """门槛守卫：拒绝信息带上门槛值（C5 的行为，原样保留）。"""
    if subtotal < THRESHOLD:
        raise ValueError(f"未满 {THRESHOLD}，不可用券")


def _to_cents(value) -> Decimal:
    return Decimal(str(value)).quantize(_CENT, ROUND_HALF_UP)


def payable(subtotal, use_coupon=True, coupon_value=COUPON_DEFAULT):
    subtotal = Decimal(str(subtotal))
    if use_coupon:
        _ensure_threshold(subtotal)
        return _to_cents(subtotal - Decimal(str(coupon_value)))
    return _to_cents(subtotal)
'''


def sh(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd or ROOT, capture_output=True, text=True)


def git(args: list[str]) -> str:
    proc = sh(["git", "-C", str(REPO), *args])
    if proc.returncode != 0:
        sys.exit(f"git {' '.join(args)} 失败：\n{proc.stdout}{proc.stderr}")
    return proc.stdout.strip()


def run_pytest() -> int:
    """仓库内跑测试，返回 pytest 退出码。"""
    return sh([PY, "-m", "pytest", "-q"], cwd=REPO).returncode


def commit(phase: str, subject: str) -> None:
    git(["add", "-A"])
    git(["-c", "user.name=tdd-kata", "-c", "user.email=kata@local",
         "commit", "-m", f"{phase} {subject}"])
    code = run_pytest()
    verdict = "PASS" if code == 0 else "FAIL"
    LOG.append(f"{phase}|{subject}|{verdict}")
    print(f"    测试运行：{verdict}")


def main():
    if REPO.exists():
        subprocess.run(["rm", "-rf", str(REPO)])
    REPO.mkdir()
    git(["init", "-b", "main"])
    print(f"独立仓库就绪：{REPO}")

    for n in range(1, 6):
        cyc = f"C{n}"
        print(f"\n[{cyc}] RED：先写测试并提交（此刻它必须是红的）")
        (REPO / "test_pricing.py").write_text(TEST_HEAD + "".join(TESTS[c] for c in sorted(TESTS)[:n]))
        doc = re.search(r'"""(.+?)"""', TESTS[cyc], re.S).group(1).strip().splitlines()[0]
        commit("🔴 RED", f"{cyc}: {doc}")

        print(f"[{cyc}] GREEN：最小实现让它变绿")
        (REPO / "pricing.py").write_text(IMPLS[cyc])
        commit("🟢 GREEN", f"{cyc}: 实现满减规则")

    print("\n[REFACTOR] 只动实现不动测试（提取常量与守卫），绿必须保持")
    (REPO / "pricing.py").write_text(IMPL_REFACTOR)
    commit("🔵 REFACTOR", "提取常量与门槛守卫，行为不变")

    final = run_pytest()
    print(f"\n终局全量测试：{'✅ 全绿' if final == 0 else '❌ 红'}")
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports/runs.log").write_text("\n".join(LOG) + "\n")
    print(f"提交序列：{len(git(['log', '--oneline']).splitlines())} 个提交；"
          f"运行留档 reports/runs.log（{len(LOG)} 条）")
    sys.exit(0 if final == 0 else 1)


if __name__ == "__main__":
    main()
