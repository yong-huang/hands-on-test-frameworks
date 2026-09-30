# 09 · Fixture 体系与类型安全 POM：让新用例只剩业务语言

> 用例里的样板（登录、造数、定位）每重复一次，套件就老化一分。
> 本实验用 `test.extend` 两层 fixture（test 级 + worker 级）与类型安全的
> Page Object（POM，页面对象模式——把页面操作封装成类）把样板抽干：
> 新增一条"admin 创建订单并验证"用例只需 6 行，三条验收线脚本自动把关。

## Background

lab 03-05 的用例各自带着登录脚手架（`login()` 帮助函数复制了四份）、
裸定位器散落在断言之间。后果有两层：改一个 testid 要全仓库搜索替换；
新人的第一条用例要先读懂 30 行 setup 才能写 3 行业务。

两个经典解法各管一半：fixture（测试的依赖注入机制——声明需要的对象，
框架负责构造与清理）管"脚手架供给"；POM 管"操作与定位的内聚"。

Playwright 把两者做成了类型安全的一体：fixture 返回页面对象实例，
用例参数解构即可用，拼错属性名在编译期报错。

## What

本实验的 `fixtures.ts` 分两层 extend：test 层（adminPage / customerPage /
orders / orderTitle，每条用例全新实例）与 worker 层（adminToken，
整个 worker 进程只登录一次）。

页面对象收在 `pages/`，选择器全仓库只允许住在这里。

可以把这套结构想成餐厅的动线：用例是顾客，只点菜（业务动作）；
fixture 是中央厨房（备料——登录、造数、实例化），worker 层是大宗采购，
POM 是传菜口（和后厨的所有接触都走这里）。

但和餐厅不同，Playwright 的依赖是按需构造的：
用例参数里写了什么，什么才会被创建，没写的零成本。

![fixture 分层与 POM 收口](images/fixtures.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/playwright/09_pw_fixtures_pom/images/fixtures.html)
> （或本地打开 [`images/fixtures.html`](images/fixtures.html)）。
> 图上虚线是两条跨层供给：worker 层向 test 层复用 token；fixture 直连 API 登录绕过 UI。

## When to Use

| 场景 | fixture + POM | 复制粘贴脚手架 |
|:---|:---|:---|
| 套件超过 20 条用例 | ✅ 样板摊薄到接近零 | 每条重复付登录/导航成本 |
| 多角色用例频繁切换 | ✅ adminPage/customerPage 即取即用 | 手工切换易漏步骤 |
| UI 改版（选择器变化） | ✅ 只改 pages/ 一个目录 | 全仓库搜替 |
| 一次性验证脚本 | ⚠️ 抽象成本不划算 | ✅ 直接写 |

判断口径：**重复第三次就该抽 fixture**。页面对象同理——被两个以上用例
操作的页面才值得建类，别为单条用例造空壳 POM。

## Quick Start

```bash
cd playwright/09_pw_fixtures_pom
./fixtures_pom.sh          # apply 体检 → observe 用例 + 三条验收线 → clean
```

observe ① 跑 6 条用例（fixture 驱动，无一条带登录样板）：

```
  ✓  2 [chromium] › 角色随取随用：customerPage 与 adminPage 互不串号 (158ms)
  ✓  6 [chromium] › worker 级 fixture：adminToken 整个 worker 只登录一次 (6ms)
  6 passed (1.2s)
```

observe ②-④ 是三条自动化验收线：

```
>>> tests/new_order.pom.spec.ts 有效行数（去注释/空行）: 6
>>> ≤10 行 ✓
>>> tsc 零错误 ✓
>>> tests/ 零选择器 ✓（全部收口在 pages/）
```

验收方式：三条线全过（6 行新用例、`tsc --noEmit` 零错误、
tests/ 目录 grep 不到任何定位表达式）。

变异实验：往用例里加一行 `await page.goto('/x')`——`page` 不在参数解构里，
TS 直接标红，这正是类型安全 fixture 的含义。

## How It Works

**两层 extend 各管一个生命周期。** test 层 fixture 每条用例初始化一次
（`adminPage` 给你一个已注入登录态的全新页面）；worker 层用
`{ scope: 'worker' }` 声明，整个 worker 进程只初始化一次（`adminToken`）。

签名上 worker 层写在第二个类型参数：`testBase.extend<{}, WorkerFixtures>`——
这不仅是语法，更是纪律：worker 层拿不到 page，想依赖 test 层资源类型上就不允许。

**登录态注入走 addInitScript。** fixture 先用 fetch 调 `/api/login` 拿 token，
再 `page.addInitScript` 把 token 写进 localStorage——此后任何 `goto` 都带着登录态。

与 lab 04 的 storageState 方案相比：fixture 版是代码内联、按角色即时生成，
不用落盘文件；storageState 版适合 setup project 预生成、多 project 复用。
两者可以叠加，按团队口味选主。

**POM 的纪律比类图重要。** 本实验的页面对象只有三条规则：
选择器只出现在 pages/（私有字段 `root` 是唯一出口）；
方法返回 locator 而不是断言结果（`row(title)` 返回定位器，`toHaveCount` 留给用例）；
导航细节内聚（`create()` 自己会 `goto`）。

断言不进 POM——页面对象管"怎么做"，"验证什么"永远是用例的事。

**orderTitle 工厂是并行隔离的地基。** 每条用例拿到的标题都带时间戳与随机数，
天然唯一。

lab 10 打开并行（workers > 1）后，撞数据的 bug 会先撞在这道防线上——
fixture 提前把它堵住了。

## Pitfalls & Q&A

**Q：为什么 worker 层 fixture 拿不到 page？**
生命周期决定的：worker 初始化发生在该 worker 的任何用例之前，
那时连浏览器上下文都还没有。

需要"每 worker 一份浏览器资源"时，正确做法是 worker fixture 里自己起
（比如一个 API 上下文）——类型签名直接禁止引用 test 层对象，想违规都编译不过。

**Q：fixture 里能做清理（teardown）吗？**
能。fixture 函数在 `use(x)` 之后的代码就是清理阶段，
天然在用例结束后执行（资源构造 → use → 清理的夹子形状）。

本实验的 orderTitle 不需要清理（唯一标题不污染别人），但有副作用的
fixture 都应该写成这个形状。

**Q：`orders.create()` 内部会 goto，这算不算 POM 藏断言？**
它藏的是导航，不是断言。POM 禁止的是把 `expect` 埋进页面对象——
那会让"验证什么"失去用例视角。

"去到这个页面"是操作的一部分，内聚进去让用例更短。
边界：方法名必须讲业务（create/goto），不讲实现（clickAndNavigate）。

**Q：选择器收口检查怎么防"注释里的字样"误报？**
脚本的 grep 匹配代码形态，注释换一种措辞即可避开——
本实验的脚本注释就为此改过一次措辞（实测踩过）。

更严格的做法是 AST 检查或 ESLint 规则（`no-restricted-syntax`），
仓库化时值得升级。

**Q：POM 要不要包 await？**
方法返回 locator 时不要（`row()` 同步返回，让用例 `await expect(...)`）；
方法执行动作时要（`create()/delete()` 内部 await）。

混合形态最容易出错——本实验的 OrdersPage 严格二分：
动作方法 async，定位方法纯同步。
