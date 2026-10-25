# 17 · 🏁 终极套件（Python）

## Background

前 16 个项目攒下的能力——POM、数据驱动、失败留证、多浏览器——只有拧成
「一条命令出全绿报告」的回归套件，才算真正可交付。终极套件的原则是**组装而非重写**：
POM 直接 sys.path 复用项目 10 的三层，数据直接读项目 11 的 orders.json。

## What

- 回归集：购买支付全流程（POM）+ 表单 5 组国际地址（数据驱动）+ 首页加载
- 矩阵：Chrome / Firefox 各出一份 pytest-html 报告（Safari 因原生点击坑留项目 14 专项）
- 证据链：`INJECT_FAILURE=1` 注入失败 → 自动留截图 + page source（通过用例零附件）
- 核验：≥3 份 HTML 报告 + 失败证据存在 + 双浏览器零红

## When to Use

- 发布前的回归门禁：一条命令、一份报告、一处证据目录
- 团队新成员理解「完整套件长什么样」的样板

## Quick Start

```bash
cd selenium/17_final_python
./17_final_python.sh
```

实测输出（2026-10-26，节选）：

```text
—— 浏览器: chrome ——  … passed
—— 浏览器: firefox —— … passed
- Generated html report: …/reports/report_inject.html
✅ 终极套件核验：3 份 HTML 报告 + 失败证据 FAIL_test_injectable_guard_….png
```

## How It Works

- `pytest -m regression --html=…` 按 marker 收集；矩阵用 `SELENIUM_BROWSER` 环境变量循环注入
- 失败留证钩子只在 `INJECT_FAILURE=1` 时落盘——平时报告干净，演示时才有现场
- POM/数据的复用通过 sys.path 指向兄弟项目目录，零代码复制

## Pitfalls & Q&A

- **坑：跨项目 sys.path 复用**——被复用项目的 conftest 不会被 pytest 加载（夹具仍来自
  当前 rootdir 链），跨目录只复用「纯类」，夹具要自带
- **Q：为什么矩阵只有 Chrome/Firefox？** Safari 的原生点击坑（项目 14 差异清单 #5）会让
  iframe 内购买流程不稳定；Safari 专项留在 14，不混进发布门禁
- **Q：注入开关为什么用环境变量？** 让「套件永远绿」和「演示失败样貌」共用同一条命令，
  CI 里不设变量即是全绿口径
