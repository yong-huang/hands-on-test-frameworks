# 07 · Hooks 与标签：生命周期四钩子和场景过滤表达式

> 套件成型后需要两类编排能力：生命周期钩子（适时装备与清理）
> 与标签过滤（@smoke/@wip 圈选本次要跑的子集）。
> 本实验演示四类钩子的真实执行顺序与三种圈选表达式。

## Background

没有钩子时，每个场景都得自带"登录 + 清场"样板——lab 02 的教训。
钩子（hooks）是 cucumber 在场景生命周期的固定时点执行的代码：
BeforeAll 整套件一次、Before 每场景一次、After 每场景结束、AfterAll 收尾。

lab 03 的隔离逻辑（reset + 新 context）正应该住在这些钩子里。

标签（tags）解决另一个方向的问题：全套件 50 个场景，本次只想跑冒烟 5 个。
`@smoke` 这样的标记贴在场景上，`--tags` 表达式圈选——布尔逻辑
（and/or/not）支持任意组合。

## What

四类钩子的真实时序（本实验实测输出）：

```
BeforeAll —— 整个套件一次
  Before —— 场景「冒烟集」开始
  After  —— 场景「冒烟集」结束（PASSED）
  Before —— 场景「时序探针」开始
  ...
AfterAll —— 整个套件一次
```

可以把钩子想成剧场的四班工作人员：BeforeAll 是开馆布置（一次），
Before 是每场开演前的道具组，After 是每场散场后的清场组，
AfterAll 是闭馆锁门（一次）。但和剧场不同，After 能读到刚才这场
的"演出结果"（scenario.result.status）——失败时附加截图就是用它。

![Hooks 生命周期与标签过滤](images/hooks.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/cucumber/07_hooks_tags/images/hooks.html)
> （或本地打开 [`images/hooks.html`](images/hooks.html)）。
> 左右两栏是四类钩子的执行时序与标签圈选的三种表达式。

## When to Use

| 钩子/能力 | 典型用途 | 本实验/系列落点 |
|:---|:---|:---|
| BeforeAll | 启动浏览器（贵资源共享） | lab 01 起的全系列 |
| Before | reset SUT + 新 context | lab 03 的隔离两翼 |
| After | 失败截图、关闭上下文 | 按 scenario.result 判定 |
| AfterAll | 关浏览器、汇总日志 | 全系列 |
| --tags | 冒烟子集、排除进行中 | @smoke / not @wip |

判断口径：**钩子放"无论场景成败都要做的事"，标签圈"本次要跑的场景"**。
别把业务断言塞进钩子——钩子失败会跳过整个场景且错误信息脱离用例语境。

## Quick Start

```bash
cd cucumber/07_hooks_tags
./hooks_tags.sh          # apply 起靶场 → observe 时序 + 标签 → clean
```

observe ① 的输出就是四类钩子的时序实录（World 里每个钩子打印标记行）：

```
[hooks] BeforeAll —— 整个套件一次
[hooks] Before —— 场景「冒烟集（登录可见）」开始
[hooks] After —— 场景「冒烟集（登录可见）」结束（PASSED）
[hooks] AfterAll —— 整个套件一次
3 scenarios (3 passed)
12 steps (12 passed)
```

observe ② 列出三条标签过滤命令与各自的场景数：
`--tags "@smoke"`（1 场景）、`--tags "not @wip"`（2 场景）、全量（3 场景）。

验收方式：时序输出里 BeforeAll/AfterAll 各出现一次、Before/After
按场景数成对出现；`--tags "@smoke"` 只跑 1 个场景、`not @wip` 跑 2 个。
变异实验：给场景 2 也贴上 @smoke，`--tags "@smoke"` 的场景数变 2。

## How It Works

**钩子的注册就是函数调用。** `Before(fn)`、`After(fn)`、`BeforeAll(fn)`、
`AfterAll(fn)` 从 `@cucumber/cucumber` 导入后全局注册——cucumber 收集所有
support 文件里的注册，按生命周期时点回调。

钩子函数的 this 也是 World 实例（Before/After），
所以钩子里放的 page/context 与步骤里看到的是同一个。

**After 能读到场景结果。** After 钩子参数带 `scenario.result.status`
（PASSED/FAILED），失败才截图的守卫写在这里：

```ts
After(async function (this: HooksWorld, scenario) {
    if (scenario.result?.status === 'FAILED') {
        const shot = await this.page.screenshot();
        await scenario.attach(shot, { mediaType: 'image/png' });
    }
});
```

attach 的附件会出现在 HTML 报告的失败详情里（lab 09 的报告体系消费它）。

**标签表达式是布尔逻辑。** `@smoke and not @wip`（交集减集）、
`@a or @b`（并集）、`not @wip`（排除）都是合法表达式。

标签可以贴在 Scenario 也可以贴在 Feature（整文件继承），
还能带参数（`@order:5` 形式，cucumber 13 支持）用于数据化标记。

## Pitfalls & Q&A

**Q：BeforeAll 里能用 this.page 吗？**
不能。BeforeAll 的 this 上没有 per-scenario 的字段——页面是 Before
创建的，BeforeAll 执行时场景还没开始。

BeforeAll 适合浏览器实例、数据库连接池这类"整套件共享"的贵资源；
场景级资源一律放 Before。

**Q：多个 support 文件都注册了 Before，执行顺序是？**
按文件加载顺序执行（cucumber.mjs import 数组的顺序），After 反序执行。

依赖特定顺序的钩子应合并到一个文件显式排序，别依赖加载顺序的隐式行为。

**Q：场景失败后，After 还会执行吗？**
会。After 无论场景成败都执行——这正是它放清理逻辑的原因。
`scenario.result.status` 让它有能力区分成败。

若 After 自身也抛错，报告会同时呈现场景失败与钩子失败——
After 里的清理代码自身也要稳（该 try/catch 的就包住）。

**Q：标签能不能传参数？**
cucumber 13 支持带值标签：`@order:5` 贴在场景上，
钩子里读 `scenario.pickle.tags` 解析。

典型用途：给"数据量档位"打标（@load:100），
钩子按值装备不同的数据集——比维护多个 profile 轻。

**Q：为什么我的 --tags 过滤后场景数是 0？**
标签写法或位置错了。常见错误：表达式里的 and 要小写、
整体要加引号（shell 会吞 `@`、`(` 等字符）。

标签贴在 Examples 行上时过滤的是"行"而不是场景。
排查顺序：先 `--tags @smoke` 单标签确认标记生效，再逐步加表达式复杂度。
