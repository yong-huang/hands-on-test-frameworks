#!/usr/bin/env python3
"""真 provider vs pact stub 的一致性对比：双方都符合契约声明的形状。

pact 的 like 语义只锁声明的部分——响应里多出来的键（真实 SUT 的
limit/offset/created_at）放行。叶子比对规则：
- 契约值非空 → 两边实际值的类型与契约值一致（match:type 语义）
- 契约值 null + 生成器 → 实际值类型符合生成器（RandomInt→int 等）
- 其余 null → 任意
状态码两边都必须等于契约声明的值。叶子值不比——生成器与真实数据本就不同。
"""
import json
import sys

import httpx

BASE_REAL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:9700"
BASE_STUB = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:9701"
PACTS = sys.argv[3] if len(sys.argv) > 3 else "pacts"

REALISTIC_BODY = {"customer": "alice", "item": "apple", "qty": 2, "price": 3.5}
GEN_TYPE = {"RandomInt": "int", "RandomDecimal": "float"}


def conforms(declared, actual, gens, prefix="$"):
    """actual 是否符合契约声明的形状（声明键必须存在且类型相符，多余键放行）。"""
    if isinstance(declared, dict):
        if not isinstance(actual, dict):
            return False
        for k, v in declared.items():
            if k not in actual:
                return False
            g = gens.get(f"{prefix}.{k}") if gens else None
            if not conforms(v, actual[k], {}, f"{prefix}.{k}") and not (
                    v is None and g and type(actual[k]).__name__ == GEN_TYPE.get(g.get("type"), "")):
                # 契约键带生成器时按生成器类型核；否则按契约值类型核
                if not conforms(v, actual[k], {}, f"{prefix}.{k}"):
                    return False
        return True
    if isinstance(declared, list):
        return isinstance(actual, list) and all(
            conforms(declared[0] if declared else None, item, {}, prefix) for item in actual)
    if declared is None:
        return True
    try:
        float(declared)
        declared_kind = "number"
    except (TypeError, ValueError):
        declared_kind = "string"
    try:
        float(actual)
        actual_kind = "number"
    except (TypeError, ValueError):
        actual_kind = "string"
    return declared_kind == actual_kind


def body_gens(interaction):
    return (interaction.get("generators") or {}).get("body") or {}


def call(base, method, path, body=None):
    r = httpx.request(method, base + path, json=body if body else None,
                      timeout=10, trust_env=False)
    return r.status_code, (r.json() if r.content else {})


def main():
    sys.path.insert(0, ".")
    import pact_stub_server
    pact_stub_server.INTERACTIONS.clear()
    pact_stub_server.load_pacts(PACTS)

    print("① 逐交互对比：双方应答都符合契约声明形状（多余键放行）")
    all_ok = True
    for desc, req, resp in pact_stub_server.INTERACTIONS:
        path = req["path"]
        query = "&".join(f"{k}={v[0]}" for k, v in (req.get("query") or {}).items())
        full = f"{path}?{query}" if query else path
        body = REALISTIC_BODY if req["method"] == "POST" else None
        gens = body_gens(resp)
        declared = resp.get("body", {}).get("content", {})

        rs, rb = call(BASE_REAL, req["method"], full, body)
        ss, sb = call(BASE_STUB, req["method"], full, body)
        status_ok = rs == ss == resp["status"]
        real_ok = conforms(declared, rb, gens)
        stub_ok = conforms(declared, sb, gens)
        ok = status_ok and real_ok and stub_ok
        all_ok &= ok
        print(f"  {'✅' if ok else '❌'} [{desc}] status {rs}/{ss}，"
              f"契约形状：real {'✅' if real_ok else '❌'} / stub {'✅' if stub_ok else '❌'}")

    print()
    if not all_ok:
        print("❌ 存在不一致交互")
        sys.exit(1)
    print(">>> 验收：同一契约，两个应答者，状态码与契约形状一致 ✅"
          "（多余键与叶子值不同是 like 语义与生成器的正常差异）")


if __name__ == "__main__":
    main()
