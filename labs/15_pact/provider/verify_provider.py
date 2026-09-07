"""Provider 端校验（FFI 版）：拿 pacts/*.json 逐条回放验证真 SUT。

用法：python verify_provider.py --base-url http://localhost:8902
退出码 0=契约满足；非 0=契约破坏（CI 门禁语义）。
"""
import argparse
import sys
from pathlib import Path

from pact.verifier import Verifier


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8902")
    args = ap.parse_args()

    pact_files = sorted(str(p) for p in Path("pacts").glob("*.json"))
    if not pact_files:
        print("pacts/ 下没有契约文件——先跑 consumer 测试生成", file=sys.stderr)
        return 2

    v = Verifier("ministore-api")       # provider 名
    for f in pact_files:
        v.add_source(f)                 # 逐个添加契约文件
    v.add_transport(url=args.base_url)  # 被测 provider 的地址
    v.verify()                          # 不匹配会抛异常 / results 里带明细
    print("RESULT: PASS ✅ 契约满足")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # noqa: BLE001——mismatch 时库会抛异常，退出码非 0
        print(f"RESULT: FAIL ❌ 契约破坏")
        print(str(e)[:3000])
        sys.exit(1)
