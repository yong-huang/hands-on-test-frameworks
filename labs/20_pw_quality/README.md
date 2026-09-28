# 20 · 多浏览器与失败留痕：三核回归 + 自动取证

> "在我机器上是好的"不是结论，"在三个内核上都是绿的"才是。读完本篇你能把
> 同一套冒烟用例（smoke test，只覆盖核心路径的最小快速用例集）跑在
> Chromium / Firefox / WebKit 三个内核上，并配置失败自动取证——
> 失败即得截图、视频、trace 三件套，复现成本从"人肉调试一小时"降到"打开 trace"。

## Background

浏览器差异真实存在：CSS 引擎、JS 时序、fetch 行为各有脾气——Chromium 上绿的
用例在 WebKit 上可能因为时序差异偶发红。只在单一浏览器上验证的 E2E 套件，
等于把"跨内核兼容性"这个变量留给了线上用户去发现。

另一半问题在失败之后：CI 上的 E2E 失败如果没有留痕，值班同学只能盲猜
"当时页面长什么样、请求发了没有、断言时 DOM 是什么状态"，复现要人肉调试一小时。
留痕（失败瞬间的截图、视频、trace）是测试套件对维护者的基本礼貌——
而且 Playwright 可以做到"成功即删、失败才留"，磁盘不爆炸。

本实验两件事：三核矩阵回归（3 条冒烟 × 3 内核 = 9 条执行），
人为制造一条失败用例验证取证三件套自动落盘。

## What

三核矩阵是把同一套用例 × 三个浏览器内核（Chromium / Firefox / WebKit）
的组合执行。

失败自动取证是 pytest-playwright 的三个 CLI 参数
（`--screenshot` / `--video` / `--tracing`）配合 `retain-on-failure` 语义：
成功即删、失败才留，产物按"用例名 + 内核"分桶归档在 `test-results/` 下。

可以把取证三件套想成行车记录仪 + 车载诊断仪的组合：截图是事故瞬间的照片，
视频是事故前的行车记录，trace 是完整的车载数据（每一步的 DOM 快照、
网络请求、控制台，可逐帧回放）。但和行车记录仪不同的是，trace 是
时间旅行式的——失败那一刻之前的每一步都能打开看当时的页面状态。

`retain-on-failure` / `only-on-failure` 的语义差异：
前者跑完才清理（全过程留）、后者只在失败时生成——CI 磁盘友好，本地聚焦。

## When to Use

典型场景：

- 发布前的跨内核回归：三核矩阵全绿才放行。
- PR 快速验证：只跑 Chromium（最快），夜间跑满矩阵（成本分层）。
- CI 失败排查：取证三件套作为 artifact 上传，值班同学直接打开 trace 定位
  （lab 30 的流水线就这么做）。

何时不用：内部工具只有一种浏览器用户时矩阵收益有限；视觉回归
（断像素，基线 diff，如 Percy/lostpixel）与本篇的失败截图是两件事——
后者是"留证据"，前者是"断像素"，需要单独的基线管理策略。

三件套速查：

| 产物 | 命令参数 | 用途 |
|:---|:---|:---|
| 截图 | `--screenshot only-on-failure` | 失败瞬间的画面 |
| 视频 | `--video retain-on-failure` | 失败前的操作回放 |
| trace | `--tracing retain-on-failure` | DOM/网络/控制台时间旅行 |

## Quick Start

前置条件：labs/00 体检通过且三核浏览器已装（labs/00 的体检项
"Playwright Chromium/Firefox/WebKit"，缺哪个 `playwright install` 补哪个）。

```bash
cd labs/20_pw_quality
./pw_quality.sh    # ① 三核回归 ② 人为失败取证 ③ 产物清单
```

observe 的真实输出（2026-09-28 实测，节选）：

```
=====> [observe] ① 三核回归：Chromium / Firefox / WebKit 同一套冒烟
============================== 9 passed in 7.98s ===============================

=====> [observe] ② 失败留痕演示：人为制造一条失败用例 → 自动产出截图+trace+video
============================== 1 failed in 5.48s ===============================

=====> [observe] ③ 留痕产物清单（回放命令见 README）
test-results/tests-test-deliberate-break-py-test-deliberately-wrong-chromium/test-failed-1.png
test-results/tests-test-deliberate-break-py-test-deliberately-wrong-chromium/video.webm
test-results/tests-test-deliberate-break-py-test-deliberately-wrong-chromium/trace.zip
```

诚实预期：① 的 9 passed = 3 条冒烟 × 3 内核，全绿；② 的 `1 failed` 是**故意失败的靶子用例**（`test_deliberately_wrong`），用于演示取证——它挂了才能看到三件套生成，不是环境问题。

回放命令：`playwright show-trace test-results/*/trace.zip`。


关键命令（这段在做什么：矩阵执行与取证配置的三个入口）：

```bash
pytest --browser chromium --browser firefox --browser webkit
pytest --screenshot only-on-failure --video retain-on-failure --tracing retain-on-failure
playwright show-trace test-results/<case>/trace.zip
```

## How It Works

**矩阵执行**：pytest-playwright 的 `--browser` 参数可重复传参——传三次就是三内核矩阵；每个用例在每个内核下独立执行一遍（用例名会带 `[chromium]`这样的参数后缀，lab 03 的参数化机制在这里复用于浏览器维度）。

产物目录按"用例名 + 内核"分桶，跨内核对比失败原因时不会混。


**WebKit 的正确姿势（诚实记录）**：本 SUT 上 WebKit 无需特殊处理即可全绿——
但保留两处差异意识：banner 的 fetch 时序在 WebKit 略不同，断言一律 `expect`
等待（而非假设时序，lab 17 的原则在这里兑现）。

若真遇到引擎特有 bug，正确姿势是 `pytest.mark.skipif(browser=="webkit")`
并附 issue 链接，而不是改断言迁就。

**取证的触发机制**：三个参数都是 pytest-playwright 的 CLI 参数（不是playwright.config——那是 Node 版 Playwright 的配置位；Python 线的等价物放pytest 插件/ini）。

`retain-on-failure` 的实现：过程性产物（视频、trace）全程记录，套件结束时清理成功用例的产物、保留失败用例的——所以"失败才留"不是魔法，是事后清扫。


**产物与 CI 的接线**：留痕目录 `test-results/` 要进 `.gitignore`
（不进版本库），但 CI 里要作为 artifact 上传（lab 30）——
本地排查靠人打开，CI 失败靠 artifact 远程取证。

## Pitfalls & Q&A

踩坑清单：

- **取证参数写进 playwright.config**。现象：参数不生效。原因：那是 Node 版
  Playwright 的配置位，Python 线用 pytest CLI/ini。解法：命令行或
  `configs/pytest.ini` 的 `addopts`。
- **`test-results/` 没进 .gitignore**。现象：几千个产物文件污染 git status。
  解法：ignore 掉，CI 里改为 artifact 上传。
- **三核矩阵全量跑**。现象：流水线时长翻三倍。解法：冒烟进矩阵、
  全量挑核、PR 跑 Chromium、夜间满矩阵。
- **为了过 WebKit 改断言**。现象：断言被削弱，Chromium 上也失去保护。
  解法：引擎特有问题用 `skipif` + issue 链接隔离，不动断言语义。

深入问答：

- **Q：三核矩阵的成本怎么控制？** 冒烟进矩阵、全量回归挑核；PR 跑 Chromium、
  夜间跑满矩阵；利用 pytest-xdist 把矩阵并行化。
- **Q：trace 和 video 二选一？** trace 信息密度远高于 video；video 给非工程师
  看过程，trace 给工程师定位问题——两者都要，但只在失败时留。
