# 13 · RPA——Excel 驱动批量下单

## Background

RPA（Robotic Process Automation）是 Robot Framework 的另一张面孔：不测「软件对不对」，
而是替人完成「流程怎么走」。Excel 批处理是最典型的场景——读单 → 逐行执行 → 结果写回 →
人工复核。与测试自动化的区别：**非法行是流程的一部分**（捕获、记失败、继续），不是用例失败。

## What

- `orders_source.csv`：10 行订单（含 2 行非法：无客户/空行）
- sh 用 openpyxl 从 CSV 预制真 xlsx；robot 用 RPA.Excel.Files 读表
- 逐行 `Run Keyword And Ignore Error` 下单：非法行捕获记「失败」、不中断批处理
- 汇总断言 8 成功 / 2 失败；结果工作表写回 `orders_result.xlsx` 供人工复核

## When to Use

- Excel 驱动的批量业务（订单导入、批量开票、员工入职）
- 「处理 + 留痕 + 人工复核」三段式的任何流程

## Quick Start

```bash
cd robotframework/13_rpa_excel
./13_rpa_excel.sh            # PASS（8 成功 / 2 失败不中断）
```

实测输出（2026-10-27）：`Excel 驱动批量下单（10 行含 2 非法，结果写回） | PASS`

## How It Works

- `Read Worksheet As Table`（单数！）把 sheet 读成 Table 对象，FOR 可迭代
- 失败隔离：`Run Keyword And Ignore Error` 返回 ${status}/${msg}，业务失败进结果表而非打断循环
- 写回：原簿开工作表加「结果」列，`Save Workbook    新路径` 另存（原输入保留）

## Pitfalls & Q&A

- **坑：RPA.Excel.Files 的关键字名是单数** `Read Worksheet As Table`（复数 Forms 不存在，
  实测报错自带 Did you mean）；Create Worksheet 没有 `overwrite=` 参数（另存用 Save Workbook 路径）
- **坑：Open Workbook 打不开不存在的文件**——RPA 不是创建工具，xlsx 得先由 openpyxl/手工备好
- **Q：为什么非法行不算用例失败？** RPA 的验收是「10 行处理完 + 结果表如实」，把 2 行失败
  记进表里才算合格；这与测试思维（红即不过）刚好相反，是 RPA 与测试的根本分野
