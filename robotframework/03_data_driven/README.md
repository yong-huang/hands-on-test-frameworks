# 03 · 数据驱动两板斧

## Background

「同一流程 × N 组输入」是接口测试的常态。Robot 有两板斧：
**板斧一 [Template]**（数据写在用例表，轻量直观）、
**板斧二 外部 CSV + FOR 循环**（数据在文件里，加一行数据不加代码）。

## What

- `resources/orders.resource`：下单并断言（expected 参数支持 201 正向 / 422 负向；
  RequestsLibrary 的 `expected_status=` 让 4xx 不抛异常、按普通响应断言）
- 板斧一 `template_style.robot`：5 组数据（中/英/日文正向 + 空客户/空商品负向）
- 板斧二 `csv_loop_style.robot`：`Evaluate(csv.DictReader)` 读外部 orders.csv，FOR 逐行跑同一关键字
- 验收：模板式数据组 5、CSV 式数据组 4，负向断言（422 + error 字段）全部在案

## When to Use

- 数据少（≤10 组）用板斧一：所见即所得
- 数据多或由非自动化同学维护时用板斧二：改 CSV 不碰 .robot

## Quick Start

```bash
cd robotframework/03_data_driven
./03_data_driven.sh            # 两板斧各跑一遍 + 数据量核验
```

实测输出（2026-10-27，节选）：`模板式数据组 5；CSV 式数据组 4 → ✅ 两板斧数据量与负向断言达标`

## How It Works

- `expected_status=${expected}` 是 RequestsLibrary 的关键参数：让 4xx 成为「可断言的响应」而非异常
- 板斧二用 `Evaluate ... modules=csv` 在 Robot 内直接读 CSV，无需 Python 胶水文件

## Pitfalls & Q&A

- **坑：RequestsLibrary 默认对 4xx/5xx 抛 HTTPError**——负向用例必须传 `expected_status`，
  否则「预期失败」直接变成「用例崩了」
- **⚠️ 生态兼容性实测：DataDriver 插件 1.11.2 与 Robot Framework 7.5 不兼容**——
  官方 README 的极简样例（DataDriver + Suite Template + CSV）同样报
  `Unassigned requiered argument detected`。本清单的板斧二因此改用 CSV+FOR 实现
  （目标一致：加一行数据不加代码）。等 DataDriver 发布兼容 RF 7.x 的版本后可换回插件式
- **坑（DataDriver 路线备用知识）**：它要求 Suite 级 `Test Template`、模板关键字必须定义在
  本文件 Keywords 表（外部 resource 不算）、CSV 参数列头必须是 `${变量}` 形式——三处都对才跑得通
