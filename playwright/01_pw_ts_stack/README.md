# 01 · Playwright TS 原生栈：从 pytest 插件到类型安全的测试工程

> Playwright 由微软开发，本体是 TypeScript 库，Python 的 pytest-playwright 只是一层封装。
> 本实验换到 TS 原生栈（`@playwright/test`）：配置收进一个声明式文件、
> fixture（测试的前置依赖对象，如一个现成的已登录用户）变成带类型的代码函数、
> 三浏览器矩阵由 projects 一段配置完成。一条命令跑完 5 条用例 × 3 浏览器，共 15 个组合全绿。

## Background

pytest-playwright（实验 16-20 使用的 Python 集成）能完成常规 E2E，但它的能力边界来自封装层：
浏览器矩阵靠 `--browser` 命令行参数逐个传，报告靠另一个插件（pytest-html）拼装，
失败重试、并行隔离都要分别找 pytest 生态里的对应插件。

原因是 Playwright 的新能力先在 Node/TS 侧落地：组件测试、UI Mode（watch 模式调试界面）、
projects（多浏览器/多设备矩阵的声明式模板）等特性，Python 封装要么滞后、要么没有。
维护一套与产品同栈（TS）的测试，还能直接复用前端的类型定义与工具链。

TS 原生栈把这些散落件收进一个 `playwright.config.ts`：baseURL、超时、重试、报告、
被测服务的启停全部声明式描述。测试工程从"一堆命令行参数的集合"变成一个可版本化、可审查的工程文件。

## What

`@playwright/test` 是 Playwright 的测试运行器（test runner，负责发现用例、调度执行、产出报告的框架）。
一个测试工程 = 用例文件（`*.spec.ts`）+ 配置文件（`playwright.config.ts`）+ 运行器三者。

可以把运行器想成一条自动化流水线的调度台：用例是工件，config 是工艺参数单，
调度台按参数单把每个工件依次送进三台机床（Chromium/Firefox/WebKit）。

出件时自动附上质检照片：失败截图与 trace（整条用例执行过程的轨迹录制，
含每步截图、DOM 快照与网络请求，可在报告里逐步回放）。
但和真实流水线不同，参数单改动不需要停线——config 是纯声明，改完即生效。

![TS 原生测试栈一次跑批的完整链路](images/ts_stack.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/playwright/01_pw_ts_stack/images/ts_stack.html)
> （或本地打开 [`images/ts_stack.html`](images/ts_stack.html)）。
> 图上虚线是 webServer 的生命周期控制：运行器负责起服务、探活、收尾，用例代码完全不管这些。

## When to Use

| 场景 | 用 TS 原生栈 | 用 pytest-playwright |
|:---|:---|:---|
| 需要组件测试、UI Mode、projects 矩阵 | ✅ 完整支持 | ❌ 无此层封装 |
| 团队产品栈是 TS/React，想复用类型与工具链 | ✅ 同栈 | 需跨语言维护两套模型 |
| 团队测试代码全在 Python，被测系统也是 Python | 可用，但成两套栈 | ✅ 同栈 |
| 用例要复用 pytest 生态（db fixture、hypothesis） | 不便 | ✅ 直接组合 |

判断口径：**跟随被测产品与团队的技术栈**。本系列选 TS 是为了走 Playwright 的完整能力面；
组织内若 Python 是唯一通用语言，pytest-playwright 依然是合理选择。

## Quick Start

```bash
# 首次运行前：准备 node 依赖与三浏览器构建（缺失时 ts_stack.sh 也会提示）
bash playwright/load_resources.sh

cd playwright/01_pw_ts_stack
./ts_stack.sh          # 全流程：apply 体检 → observe 三步 → clean 清理
./ts_stack.sh observe  # 已体检过，只看演示
```

apply 阶段做类型检查（`tsc`——TypeScript 编译器，把 TS 转成 JS 顺便做全量类型校验），
之后 observe ① 用 Chromium 单浏览器跑 5 条用例。被测服务不由脚本手工拉起，
config 的 `webServer` 字段让运行器自动完成"起服务 → 探活 → 跑用例 → 收尾"：

```
=====> [observe] ① 单浏览器（chromium）：5 条用例，webServer 由框架自动托管

Running 5 tests using 1 worker

  ✓  2 [chromium] › tests/ts_stack.spec.ts:20:5 › 异步列表：点击加载后无需 sleep 直达结果 (1.4s)
  ✓  3 [chromium] › tests/ts_stack.spec.ts:34:5 › 订阅表单：提交后等待确认号出现 (904ms)
  ✓  5 [chromium] › tests/ts_stack.spec.ts:67:5 › 动态时钟始终是 时:分:秒 形状 (1.4s)

  5 passed (5.7s)
```

observe ② 不带 `--project` 参数，三核全跑，5 条用例 × 3 浏览器 = 15 个组合：

```
Running 15 tests using 1 worker
  ✓  6 [firefox] › tests/ts_stack.spec.ts:9:5 › 页面标题与三个功能区可见 (810ms)
  ✓ 11 [webkit]  › tests/ts_stack.spec.ts:9:5 › 页面标题与三个功能区可见 (2.1s)
  15 passed (23.4s)
```

两个 GUI 工具需手动打开：`npx playwright show-report`（HTML 报告）、
`npx playwright test --ui`（UI Mode，watch 模式调试界面，
时间旅行指可回退到用例的任意一步查看当时的页面状态）。

验收方式：三浏览器 15 passed 全绿。再把端口从 9001 换成任意空闲端口——
共三处要同步改：config 的 `use.baseURL`、config 的 `webServer.url`、
`server.mjs` 的 `PORT`——改完重跑，用例文件零改动，仍然全绿。

## How It Works

**config 是唯一的参数入口。** pytest 时代 `--base-url`、`--tracing on`、`--html report.html`
散在命令行与 ini 文件里；这里对应 `use.baseURL`、`use.trace`、`reporter` 三个字段。

每个字段的"为什么"注释就在 `playwright.config.ts` 内，本节只展开两个关键机制。

**webServer 把环境准备声明化。** 字段声明"跑用例前要有服务在 9001 端口探活"，
运行器负责进程的起停与等待。`reuseExistingServer: true` 表示端口已被占用时直接复用，
本地反复单跑不用先杀进程。

Python 侧的等价物是脚本里手写的 curl 探活循环，这里收敛成一行声明。

**projects 是同套用例 × 多环境的乘法器。** 每个 project 是一份浏览器上下文模板，
`devices['Desktop Chrome']` 内置了视口、UA 等默认值。声明三个 project 后，
`npx playwright test` 自动展开为 15 个组合。

某个组合失败时，报告能直接定位到浏览器名、用例名与完整 trace，不需要人工重放。

**fixture 是带类型的依赖注入。** `test.extend<{ user: TestUser }>` 声明一个增强版 test，
用例参数里多出 `user` 对象，类型由 TS 推导。

pytest 的 fixture 靠函数名字符串约定匹配；这里拼错属性名会在 `tsc` 阶段报错，
而不是运行到一半才失败。

**web-first 断言是"无需 sleep"的机制来源。** `expect(...)` 系列断言会自动轮询重试，
直到条件成立或超过上限（config 的 `expect.timeout`，本工程设 5 秒）。
所以异步接口慢 800ms 不需要任何等待代码——断言替你等到渲染完成。

普通查询（如 `page.textContent()`）没有重试语义，拿到的是"此刻"的值，这正是两者的分界。

## Pitfalls & Q&A

**Q：`npx playwright test` 报 "Executable doesn't exist"，Python 侧明明跑过？**
Python 与 Node 两侧的 Playwright 各自匹配特定版本的浏览器构建，
统一存放在 `~/Library/Caches/ms-playwright`。

Python 侧下载的构建号与 Node 侧需要的可能不同，
`npx playwright install chromium firefox webkit` 按需补齐即可，两类构建共存互不覆盖。

**Q：组件测试的 `@playwright/experimental-ct-react` 为什么锁 1.62.1？**
它与 `@playwright/test` 必须同版本。本实验落地时 1.63 只有 alpha 构建，
npm 上不存在 1.63.0 稳定版，所以两包统一锁在 ct 侧最新的稳定线。

升级时两包要一起动，这是版本策略而非偶然。

**Q：tsc 检查和运行器的转译是什么关系？**
运行器内部用自己的转译器即时编译 TS，不读 `tsconfig.json` 的编译选项也能跑。

`tsc -p tsconfig.json` 是独立的静态校验步骤（本实验放在 apply 阶段），
作用是把类型错误挡在运行之前。两者互补而非重复。

**Q：为什么 observe ① 只跑 chromium？三核全跑不是更彻底吗？**
三核跑批 23.4s，是单核 5.7s 的 4 倍。开发循环里先用最快反馈定位问题，
提交前再全矩阵回归——这是矩阵套件的标准节奏，lab 18 的分片并行会把这个时长压回去。

**Q：动态时钟每秒都变，断言怎么写才不 flaky（时好时坏）？**
断言"形状"而不是"值"：`toHaveText(/^\d{2}:\d{2}:\d{2}$/)` 对任意时刻都成立。
对含时间戳、随机 ID 的页面做精确文本断言是 flaky 的常见来源，lab 13 会系统化治理。
