# 07 · 期望失败与失败留证

## Background

负向用例的难点在「红得正确」：要红在预期的错误上，而不是红在用例自己的语法上。
本实验覆盖三类期望失败写法（expected_status / Run Keyword And Expect Error / TRY-EXCEPT），
外加 Teardown 自动截图留证。**本轮实测还抓到 RF 7.5 的两个真坑**（见踩坑节）。

## What

- 负向一：空客户下单 → 服务端 422 + error 字段（`expected_status=` 让异常变可断言响应）
- 负向二：UI 空表单 → 页面显示「下单失败」且回读无 ROB- 订单号
- 负向三：缺失元素 → `Run Keyword And Expect Error` 按错误文本匹配
- 负向四：TRY/EXCEPT/FINALLY——FINALLY 必达 + 捕获消息内容断言
- 留证：故意失败用例 + Test Teardown `Capture Page Screenshot`，核验脚本把关
  （负向 4 条全绿、注入失败恰 1 条、截图存在）

## When to Use

- 异常路径覆盖（422/409/404 系列）
- 需要失败现场留痕的 CI 套件

## Quick Start

```bash
cd robotframework/07_expected_failures
./07_expected_failures.sh            # 预期 1 failed（素材）+ 核验 ✅
```

实测输出（2026-10-27，节选）：`✅ 负向 4 条全绿；注入失败 1 条已留证：selenium-screenshot-3.png`

## How It Works

- `expected_status=` 是 RequestsLibrary 负向测试的关键参数：4xx 变成普通响应供断言
- 留证：`[Teardown] Run Keywords Capture Page Screenshot AND Close Browser`——截图在关浏览器前完成

## Pitfalls & Q&A

- **⚠️ 坑（RF 7.5 实测）：EXCEPT 的 glob 模式不生效**——`EXCEPT *pattern*` 与显式
  `type=glob` 均捕获失败，只有**精确消息**或**无模式 AS 捕获**可用；
  需要按内容分支时先 AS 捕获再 `Should Contain` 断言内容
- **坑：`Page Should Not Contain` 查的是页面源码**——内联脚本里写死的「订单号」三个字
  会让空表单用例误红；改断言元素的实际文本（Get Text + Should Be Empty/Contains）
- **坑：页面 JS 不处理非 2xx**——服务端 422 后页面显示「订单号 undefined」（实测）；
  修页面加 r.ok 防护后，负向断言才有的放矢
