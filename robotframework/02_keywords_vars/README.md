# 02 · 关键字宇宙与变量体系

## Background

Robot 的核心思想是**分层的关键字**：测试用例说业务语言（「创建订单」「查询订单」），
实现细节下沉到资源文件（.resource）。变量体系（scalar `$/list `@/dict `&`）是第三根支柱——
数据与关键字组合，才搭得起可维护的套件。

## What

- `resources/shop.resource`：打开靶场首页 / 创建订单（带默认参数 qty=1）/ 查询订单
- `keywords_vars.robot`：业务语言用例（下单→查询断言状态）+ FOR/IF 组合批量下单
  （scalar `${GREETING}`、list `@{PRODUCTS}`、dict `&{DEFAULTS}` 三种变量全用上）
- `--dryrun` 干跑：不开浏览器校验全部关键字引用完整性

## When to Use

- 用例读起来像需求文档、实现细节可集中改——这就是该重构的信号
- 新关键字先在 resource 落地，测试层永远只加业务语句

## Quick Start

```bash
cd robotframework/02_keywords_vars
./02_keywords_vars.sh            # 正式跑 2 passed + dryrun 2 passed
```

实测输出（2026-10-26，节选）：`2 tests, 2 passed`（正式）+ `2 tests, 2 passed`（dryrun）

## How It Works

- 用户关键字：`[Arguments]`（`${qty}=1` 默认值）+ `[Documentation]` + `RETURN`
- FOR/IF：RF 7 的 `FOR ... IN ... END` / `IF ... ELSE ... END` 原生块，无需旧式反斜杠
- dryrun 会把所有关键字替换为占位执行——引用写错（名字打错、参数个数不符）在此现形

## Pitfalls & Q&A

- **坑：resource 里的变量 `${BASE_URL}` 与套件变量同名**——套件变量优先级更高，
  想全局统一就只放在 resource 或只放在套件，别两边都写
- **坑：`Should Be Equal As Strings` vs `Should Be Equal`**——前者先转字符串再比，
  状态码（int）与 "201"（str）比较必须用它
- **Q：dryrun 能发现等待/断言逻辑问题吗？** 不能，它只校验关键字解析；时序问题仍需正式跑
