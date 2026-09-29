# 04 · 认证与多用户矩阵：登录一次，双角色复用全套件

> 每条用例都走一遍登录表单，是 E2E 套件最常见的时间黑洞与 flaky（时好时坏的不稳定）源。
> 本实验用 Playwright 官方的 setup project + storageState 模式：每角色只真实登录一次，
> 之后全部用例带着登录态直达。admin 与 customer 两个 project 复跑同一套用例，
> 六条权限断言 + 三条会话行为用例，16 个执行全绿。

## Background

认证（登录态）处理不好，测试套件会同时变慢和变脆：慢，因为每条用例重复填表单等跳转；
脆，因为登录页的任何改动（验证码、文案、按钮位置）会让所有用例一起红。

更隐蔽的问题是权限测试的缺失：很多团队只用 admin 账号跑全部用例，
customer 视角的"看不见"与"被拒绝"从未被断言——越权漏洞就是这么漏进生产的。

Playwright 的解法分两层：storageState（浏览器上下文状态的快照文件，
含 cookies 与 localStorage）把"登录一次"变成可复用资产。

projects（同一套用例 × 多份上下文模板）让 admin 与 customer 两套登录态
各自驱动同一套用例跑两遍。登录成本从 O(用例数) 降到 O(角色数)。

## What

本实验的配置里有三个 project：setup（只跑登录脚本）、admin、customer（依赖 setup）。
执行顺序天然成立：setup 先把两份 storageState 写进 `.auth/`，
两个角色 project 再各自带着登录态跑后面的用例。

可以把 setup project 想成物业的统一办卡日：开工前办两张门禁卡（admin / customer），
之后每个测试员进楼不再排队办卡，刷各自的卡直达楼层。

但和门禁卡不同，storageState 是本地文件，可以入库检查、可以过期重造，
甚至可以手工编辑来模拟异常会话（本实验的伪造 token 用例就是这么做的）。

![setup 预登录 + 双角色矩阵的数据流](images/auth.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/playwright/04_pw_auth/images/auth.html)
> （或本地打开 [`images/auth.html`](images/auth.html)）。
> 图上两条并行的"注入"边是矩阵的关键：同一套用例代码，两份上下文各跑一遍。

## When to Use

| 场景 | setup + storageState | 每用例现登录 |
|:---|:---|:---|
| 常规功能回归（多页面、多用例） | ✅ 登录成本摊薄到角色数 | ❌ 每条重复付登录成本 |
| 登录流程本身的测试 | ❌ 矛盾——它必须走真实表单 | ✅ 就该这么做 |
| 双角色权限矩阵 | ✅ 项目级注入天然支持 | 每条用例手工切换，繁琐易漏 |
| 登录态有效期短、频繁过期 | ⚠️ 需加过期重登逻辑 | ✅ 每次都是新会话 |

判断口径：**登录是被测功能时现登，是前置条件时预存**。两者在真实仓库里常常共存。

## Quick Start

```bash
cd playwright/04_pw_auth
./auth_matrix.sh          # apply 体检 → observe 三 project 协作 + 审计 → clean
```

observe ① 的输出能直接看到三个 project 的接力：先 2 条 setup 用例（每角色真实登录一次），
随后 14 个执行（7 条用例 × 2 角色 project）：

```
✓  1 [setup]    › tests/auth.setup.ts › login once as admin (167ms)
✓  2 [setup]    › tests/auth.setup.ts › login once as customer (131ms)
✓  3 [admin]    › tests/permission.spec.ts › UI 层：删除按钮的可见性随角色变化
  ……（✓ 4-9 省略）
✓ 10 [customer] › tests/permission.spec.ts › UI 层：删除按钮的可见性随角色变化
  16 passed (3.3s)
```

验收三条：`.auth/` 下生成两份登录态文件；免登录用例断言后续
`/api/login` 调用为 0；权限矩阵 6 条断言（UI 可见性 ×2、删除授权 ×2、重置授权 ×2）全过。
clean 会删掉 `.auth/`（登录态是运行时产物，不入库）。

## How It Works

**storageState 捕获的是"登录的结果"，不是"登录的过程"。** pw-store 登录后把 token
写进 localStorage，所以快照里最重要的就是那一条 localStorage 记录。

角色 project 创建浏览器上下文时恢复快照，SPA 启动读到 token，直接进入已登录视图，
登录表单从未出现。`tests/auth.setup.ts` 每个角色只执行一次真实 UI 登录，
`page.context().storageState({ path })` 负责落盘。

**角色要走两条通道，不是一条。** UI 通道：页面内的 fetch 由应用自己带上 token。

API 通道：测试直接调 `page.request`（与页面共享 cookie 但不执行应用的 JS），
没有应用代码帮忙加头，所以 config 里用 `extraHTTPHeaders` 按角色注入
`authorization` 头。

pw-store 的 token 是可逆的 base64（靶场的刻意设计），
config 能静态构造两把角色头——生产系统请改从环境变量或密钥服务读取。

**权限判定必须落在服务端。** 前端把 customer 的删除按钮藏起来只是体验优化，
不是授权边界。

矩阵用例的策略：UI 层断言可见性（admin 见按钮 / customer 见不到），
API 层绕过 UI 直接 DELETE（admin 200 / customer 403）。两层都绿，
才能说"纵向上权走不通"。

**extraHTTPHeaders 的优先级是网络层的。** 用例"会话过期模拟"先清空注入头
（`test.use({ extraHTTPHeaders: {} })`）再伪造 token，否则注入的有效角色头
会在网络层覆盖页面发出的伪造头，服务端看到的就不是"过期会话"了。

这条用例同时也是 extraHTTPHeaders 语义的活教材。

## Pitfalls & Q&A

**Q：为什么伪造 token 要"先 goto 再 evaluate 再 reload"，而不是 addInitScript？**
项目级 storageState 的恢复发生在上下文初始化时序里，addInitScript 注入的值
会被恢复动作覆盖（本实验实测踩过：welcome 一直显示旧角色）。

先加载让快照生效，再用 `page.evaluate` 覆盖 localStorage，reload 后应用读到的
必然是伪造值——每一步的时序都是确定的。

**Q：storageState 文件会过期吗？**
会。token 有有效期（或被服务端吊销）后，快照照样恢复，但接口开始 401。
本实验的"伪造 token"用例就是这种状态的模拟。工程实践：setup 阶段校验快照有效性
（打一个轻量探活接口），失效就重新登录落盘。

**Q：两个角色 project 会不会互相污染数据？**
会共用同一个 pw-store 内存态（同一进程、同一端口），所以用例遵循两条纪律：
不精确断言全局计数（用 `filter` 断言自己造的数据），admin 的重置用例
把状态拉回种子。真正的并行隔离是 lab 10 的主题，这里先把"串行矩阵"跑稳。

**Q：为什么用例里用 `test.info().project.name` 分支，而不是写两份用例文件？**
权限矩阵的本质是"同一操作在两个角色下的不同预期"——写在一起，diff 一眼可见；
拆成两份，角色语义散落且容易只改一份。project 名就是用例内的"当前角色"变量。

**Q：登录页本身怎么测？**
不进 storageState 体系：为登录页单独建一个不带 `storageState` 的 project
（如 `guest`），用例直接走表单的成功/失败分支。pw-store 的冒烟套件
（lab 02）里已有登录失败用例，登录页的专项测试照那个模式写即可。
