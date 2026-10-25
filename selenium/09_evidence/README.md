# 09 · 截图证据链

## Background

UI 用例失败时只留一句 assert 消息，等于案发现场被毁了——定位器改版？弹窗挡住？渲染抖动？
没有现场就只能靠猜。本实验把「失败自动留证」做成夹具：失败用例自动留截图 + page source，
通过用例零附件（对照 appium/13 的纪律）。

## What

- 局部 conftest：`pytest_runtest_makereport` 钩子记录结果 + autouse 夹具在失败时落证
- 2 条用例：1 条通过（结账页可打开）、1 条**故意失败**（在结账页找首页横幅）
- `verify_evidence.py` 核验：恰好 1 组 FAIL_*.png + FAIL_*.source.html，截图 >10KB，通过用例零附件

## When to Use

- 一切要进 CI 的 UI 套件——证据链是失败排查的第一现场
- 复现困难的偶发失败：有 page source 才能确认「当时页面长什么样」

## Quick Start

```bash
cd selenium/09_evidence
./09_evidence.sh            # 预期 1 failed（素材）+ 证据链核验 ✅
```

实测输出（2026-10-26，节选）：

```text
1 failed, 1 passed in 1.32s
✅ 证据链核验通过：FAIL_test_injected_failure_produces_evidence_021558.png
   + FAIL_test_injected_failure_produces_evidence_021558.source.html；通过用例零附件
```

## How It Works

- `hookwrapper=True` 包住 makereport，把 `rep_call.failed` 挂到 item 上
- autouse 夹具 yield 之后读结果：失败则 `driver.save_screenshot` + `page_source` 落盘
  （文件名带用例名与时间戳，重跑不互相覆盖）

## Pitfalls & Q&A

- **坑：证据留在 driver 已 quit 之后**——夹具必须在 driver 夹具**之后**声明依赖（参数顺序即销毁顺序），
  否则截图时浏览器已经关了
- **坑：只留截图不留 page source**——截图能看布局，page source 才能查「DOM 里到底有没有这个元素」
- **Q：为什么通过用例零附件？** 附件是证据不是纪念品；全留会淹掉真正重要的失败现场
