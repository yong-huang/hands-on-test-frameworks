# 01 · 自建靶场 + 首个套件

## Background

学 Robot Framework 的第一道坎不是语法，是「表格从哪来、套件怎么跑、报告在哪看」。
本实验一次把三件事立起来：自建一个**独立靶场**（Web 下单表单 + 4 个 REST 接口，
与 selenium 线的靶场互不依赖），再写第一个两用例套件打通 Web 与 API 两条路。

## What

- `../shop/`：Python http server（端口 8952）——下单表单页 + `/api/orders` 创建/查询/支付/取消
- `first_suite.robot`：SeleniumLibrary 开页断言标题 + RequestsLibrary 健康检查断言 200
- 产物：`reports/log.html + report.html + output.xml` 三件套

## When to Use

- 新环境装完 Robot Framework 后的冒烟
- 新系列开线时，照这个结构起自己的靶场

## Quick Start

```bash
cd robotframework/01_shop_first_suite
./01_shop_first_suite.sh            # apply 拉靶场 → observe 跑套件 → clean 清产物
```

实测输出（2026-10-26，节选）：`2 tests, 2 passed, 0 failed`

## How It Works

- 套件结构：Settings（Library 引入）/ Test Cases / Keywords 三张表起步
- 靶场生命周期在 sh 层（apply 幂等拉起），robot 只管跑——「sh 先行，robot 只管跑」是本系列约定
- `--outputdir reports` 把三件套收进独立目录

## Pitfalls & Q&A

- **坑：Suite Setup 里写了不存在的关键字** → 整个套件 setup failed、全部用例连坐失败
  （实测首跑就翻车）；Setup 里的关键字必须已由 Library/Resource 提供
- **Q：为什么不用 conftest 式夹具？** Robot 的对应物是 Suite/Test Setup+Teardown 与资源文件，
  项目 2 起会展开
