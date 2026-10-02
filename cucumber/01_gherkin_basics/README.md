# 01 · Gherkin 最小闭环：用业务语言驱动真浏览器

> BDD（Behavior-Driven Development，行为驱动开发）的核心载体是 Gherkin——
> 一门"业务的人与机器都能读"的半结构化语言。本实验用中文 Gherkin 描述 pw-store
> 登录行为，3 个场景打真 Chromium 全绿，并演示一个 BDD 最危险的隐性失效：
> 步骤关键字写错不会报错，而是静默消失。

## Background

没有 BDD 时，测试代码直接表达操作（fill、click、expect）——产品经理看不懂，
需求变更时没人能确认"测的还是不是需求"。测试与需求之间隔着一层代码翻译，
翻译损耗就是缺陷藏身的空间。

Cucumber（BDD 工具链的事实标准）把这一层显式化：需求用 Gherkin 写成
Feature 文件（Given-When-Then 三段结构），代码只做"句子到动作"的绑定。

Feature 文件因此可以进需求评审——这是 BDD 与普通测试框架的本质区别。

## What

一次 cucumber 运行的四个角色：`.feature` 文件（Gherkin 语法的需求描述）、
步骤层（把每个句子绑定成代码）、World（场景间的上下文对象，本实验建了
最小形态）、运行器（解析 Gherkin、匹配步骤、驱动执行）。

可以把 Gherkin 想成需求与代码之间的"通关文牒"：业务方在文牒上写清楚
"过五关"的标准，实现方逐条盖执行章。但和真实文牒不同，Gherkin 的措辞
宽容度极低——关键字（假如/当/那么）必须一字不差，差一个字母整个句子
就不再是步骤。

![Gherkin 最小闭环：feature 经解析与步骤匹配后驱动真浏览器](images/gherkin.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/cucumber/01_gherkin_basics/images/gherkin.html)
> （或本地打开 [`images/gherkin.html`](images/gherkin.html)）。
> 主链路是"feature 文件 → Gherkin 解析 → 步骤匹配 → 浏览器执行"；World 沿虚线为每个场景装备全新上下文。

## When to Use

| 场景 | 中文 Gherkin（本实验） | 英文 Gherkin | 代码直接写 |
|:---|:---|:---|:---|
| 团队以中文为工作语言 | ✅ 业务侧可参与评审 | 阅读多一层翻译 | ❌ 业务侧不可读 |
| 需求频繁变更、需快速对齐 | ✅ 改句子即改需求 | ✅ | ❌ 改代码要走评审 |
| 一次性技术验证脚本 | ⚠️ 写 Gherkin 是额外成本 | ⚠️ | ✅ 直接写更快 |
| 步骤复用度高的回归套件 | ✅ 一套句子多种数据 | ✅ | ⚠️ 复用靠抽象能力 |

判断口径：**Gherkin 的价值与"非技术读者"的数量成正比**。
全员技术团队用它并非错误，但买到的主要是结构强制而非协作收益。

## Quick Start

```bash
cd cucumber/01_gherkin_basics
./gherkin_basics.sh          # apply 起靶场 → observe 三场景 + 静默失效演示 → clean
```

apply 阶段做类型检查并用脚本启动 pw-store（端口 9101）——cucumber 没有
`@playwright/test` 那样的 webServer 托管概念，SUT 生命周期归脚本管。
observe ① 跑 3 个中文场景：

```
2 hooks (2 passed)
3 scenarios (3 passed)
14 steps (14 passed)
0m 0.514s
```

observe ② 是本实验最重要的演示——把 `假如` 写成 `Givens` 再跑：

```
4 scenarios (4 passed)
16 steps (16 passed)
>>> 退出码 0、场景 3→4；steps 14→16 多出的 2 个只是该空场景的 Before/After
>>> 钩子计数——真实步骤一个没加。拼错的行被 Gherkin 当成场景描述文本
>>> 静默消失，空场景照常通过：这就是 BDD 套件最大的隐性风险。
```

验收方式：3 场景全绿；静默失效演示如实呈现（绿着通过、什么都没测）；
`bash -n` 与 `npx tsc -p tsconfig.json` 零错误。

## How It Works

**中文方言靠语言头激活。** feature 文件首行 `# language: zh-CN` 之后，
`功能/场景/假如/当/那么` 都是合法关键字——Gherkin 内置多语言方言表，
解析器按头部声明切换。

方言切换只影响关键字，步骤文本与代码字符串不受影响。
省略语言头时默认英文方言，中文关键字会被当成描述文本（见 Pitfalls）。

**World 是"每场景一次"的上下文。** `setWorldConstructor` 注册的类实例
在每个场景开始时新建、结束后丢弃——`Before` 往里放 page，步骤函数的
`this` 就是它。

与 `@playwright/test` 的对应关系：`Before` ≈ test 级 fixture，
`BeforeAll/AfterAll` ≈ worker 级。浏览器只启一次（BeforeAll），
页面每场景全新（Before），隔离与成本由此平衡。

**步骤绑定是全字符串匹配。** `当 以用户名 {string} 密码 {string} 登录`
里的 `{string}` 是 Cucumber 表达式参数占位——匹配后把引号内的值传入函数。

措辞与定义必须完全一致（忽略首尾空格），这既是复用的基础，
也是静默失效的根源。

**tsx 是 TS 步骤文件的转译钩子。** cucumber 13 自身不编译 TypeScript，
配置里 `import: ['tsx', 'features/**/*.ts']` 先加载 tsx（注册 TS 加载钩子）
再加载步骤文件。

tsc 仍独立做类型检查（apply 阶段执行）——运行器管转译，编译器管类型，
分工与 playwright/ 系列一致。

## Pitfalls & Q&A

**Q：关键字写错为什么连警告都没有？**
Gherkin 解析器把"非关键字行"当作 Feature/Scenario 的描述文本（description），
这是语言规范行为：描述文本允许任意措辞，供人阅读。

于是 `Givens 打开…` 静默落进描述，场景变成零步骤空壳，运行照常通过。
本实验实测：场景 3→4、steps 14→16（多出的 2 个只是该空场景的
Before/After 钩子计数）。对策是评审时盯步骤总数，以及 CI 里对"空场景"做检测。

**Q：为什么登录场景的欢迎语断言是"欢迎，admin"？pw-store 不是会跟随浏览器语言吗？**
会——这正是 World 里 `newContext({ locale: 'zh-CN' })` 的原因。

Playwright 默认 locale 是 en-US，pw-store 会随之切成英文界面，断言必红
（playwright/ 系列 lab 14 实测踩过同一个坑）。语言是环境变量，
测试要显式钉死自己依赖的那一档。

**Q：SUT 为什么由脚本启动，而不是像 @playwright/test 那样配 webServer？**
Cucumber 没有内置的 webServer 概念——它对"被测系统"一无所知，
只负责句子与步骤的翻译，这是 BDD 工具链的通用形态。

工程上的对策就是本实验的脚本：apply 起服务 + 探活，clean 杀干净。
lab 08 的 profiles 会让"指向哪个 SUT"变成配置项。

**Q：`import ... from '../support/world.ts'` 为什么带 .ts 扩展名？**
tsx 的加载钩子对显式 .ts 扩展名解析最稳；`.js` 扩展指向 `.ts` 的重映射
在本版本组合下实测不生效（ERR_MODULE_NOT_FOUND）。

代价是 tsc 需要 `allowImportingTsExtensions: true` 配合（仅 noEmit 模式可用）。

**Q：3 个场景共用"假如 打开 pw-store 首页"，这句复用有问题吗？**
没有——复用正是步骤层的价值。有问题的复用是"一个步骤里塞了点击+填写+
断言三件事"（步骤边界模糊，lab 02 专门讨论）。单动作步骤的复用是健康信号。
