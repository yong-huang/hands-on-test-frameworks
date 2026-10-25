#!/usr/bin/env python3
"""GraphQL mock 演示客户端：3 条 query 各自预设 → 结构化 errors → AB 切换。

GraphQL 的语义载体是 {data?, errors?} 应答体——HTTP 状态码由服务端实现
决定（本实验的 Ariadne ASGI：校验错误与字段级执行错误都回 400），断言对象
是 errors 的内容与结构化程度，不是状态码。
"""
import json
import sys

import httpx

BASE = "http://127.0.0.1:9750/graphql"
FAILURES = []


def gql(query, scene=None, variables=None):
    headers = {"X-Mock-Scene": scene} if scene else {}
    r = httpx.post(BASE, json={"query": query, "variables": variables or {}},
                   headers=headers, timeout=10, trust_env=False)
    return r.status_code, r.json()


def check(name, ok, detail=""):
    print(f"  {'✅' if ok else '❌'} {name}{(' — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(name)


def three_queries():
    print("\n① 三条 query 各自命中预设响应（场景 a）")
    s, d = gql("{ order(id: \"x\") { id customer amount status } }", "a")
    o = d["data"]["order"]
    check("单订单 query → ORD-A-1", s == 200 and o["id"] == "ORD-A-1",
          f"amount={o['amount']}")
    s, d = gql("{ orders(limit: 2) { id status } }", "a")
    lst = d["data"]["orders"]
    check("列表 query → 2 条（limit 生效）", s == 200 and len(lst) == 2,
          f"ids={[x['id'] for x in lst]}")
    s, d = gql('{ riskyOrder { id } }', "a")
    check("riskyOrder query → 进字段级错误分支", "errors" in d,
          "见 ② 的结构化断言")


def structured_errors():
    print("\n② 结构化 errors：schema 外字段与字段级错误都是 JSON errors 数组")
    s, d = gql('{ order(id: "x") { id nonexistentField } }', "a")
    msg = d.get("errors", [{}])[0].get("message", "")
    check("schema 外字段 → errors 带 Cannot query field（非 500 文本）",
          "Cannot query field" in msg, f"http {s}；{msg[:55]}")
    s, d = gql('{ riskyOrder { id } }', "a")
    e = d.get("errors", [{}])[0]
    check("字段级错误带 path 定位",
          e.get("path") == ["riskyOrder"]
          and "风控数据不可用" in e.get("message", ""),
          f"http {s}；path={e.get('path')}")


def ab_switch():
    print("\n③ AB 切换：同一 query，X-Mock-Scene 头决定两套数据")
    _, da = gql('{ order(id: "x") { id amount review } }', "a")
    _, db = gql('{ order(id: "x") { id amount review } }', "b")
    a, b = da["data"]["order"], db["data"]["order"]
    check("场景 a → review=false（常规）", a["review"] is False,
          f"amount={a['amount']}")
    check("场景 b → review=true（大额）", b["review"] is True,
          f"amount={b['amount']}")
    check("两套数据确实不同", a != b)


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else BASE
    globals()["BASE"] = base
    three_queries()
    structured_errors()
    ab_switch()
    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 项断言失败：{'、'.join(FAILURES)}")
        sys.exit(1)
    print(">>> 验收：3 query 各自预设 ✅ 结构化 errors ✅ AB 切换 ✅")


if __name__ == "__main__":
    main()
