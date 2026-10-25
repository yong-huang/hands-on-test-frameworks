# 09 · Schema 校验与负向矩阵

## Background

断言单个字段远远不够——响应的**结构**漂移（字段改名、类型变了、status 多了个新值）
才是上下游联调的头号杀手。JSON Schema 把结构契约写进文件，用 jsonschema 引擎逐字段验证。
负向矩阵则把「接口 × 异常输入」的九宫格逐格打穿，每格断言状态码 + error 字段。

## What

- `order.schema.json`：id 格式（ROB-+8 位十六进制）/ 字段类型 / status 枚举
- 正向：创建订单响应过 Schema ✅；反向：非法实例 `{foo:1}` 必须被识破
- 3×3 负向矩阵（模板关键字 `负向一格` 分发）：
  创建×(缺客户/缺商品/空字典)→422、查询×(不存在/畸形ID)→404、
  支付/取消×(不存在/状态不允许)→404/409，逐格断言状态码 + error 字段

## When to Use

- 契约测试的前置层：先保结构，再保语义（与 labs/15 Pact、mocking/09 呼应）
- 服务端状态机改版后的快速回归（矩阵一格一个状态转移约束）

## Quick Start

```bash
cd robotframework/09_api_schema
./09_api_schema.sh            # 3 tests, 3 passed
```

实测输出（2026-10-27）：`3 tests, 3 passed, 0 failed`（负向矩阵以模板用例承载 9 格）

## How It Works

- `Evaluate jsonschema.validate($instance, json.loads($schema)) modules=jsonschema`
  ——validate 失败抛 ValidationError，成功静默；反向用例用
  `Run Keyword And Return Status` 捕获成布尔再断言「必须失败」
- 模板关键字 `负向一格` 按「动作」分发构造输入，按「标识」决定是否先准备前置状态
  （如「取消-已支付」先造一笔 paid 订单）

## Pitfalls & Q&A

- **坑：矩阵分发关键字越来越长**——把「造输入」和「断言」固定成两段，动作分支只管构造；
  格子超过 12 个就该拆成多个矩阵文件
- **Q：为什么 Schema 反向演示是必须的？** 只验证「合法数据通过」无法证明 schema 本身
  写得对；用 `{foo:1}` 证明引擎真的在拦
