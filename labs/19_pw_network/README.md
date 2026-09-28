# 19 · 网络拦截与登录态复用：前端测试不再看后端脸色

> E2E 必须整条链路都活着才能跑？Playwright 的 `page.route` 能把任何请求桩掉、
> 改写、注入错误——后端挂了照样测前端；`storageState` 把登录态存成文件，
> 双角色会话随取随用，且互不串号。读完本篇你能给前端测试装上"不依赖后端"
> 的自由，并正确处理对话框这类事件型断言。

## Background

E2E 测试默认依赖整条链路活着：后端挂了、接口慢了，前端测试集体变红——
但红的原因是后端，不是前端。这带来两个具体损失：前端逻辑
（降级提示、状态机、边界渲染）明明不依赖真后端，却只能在后端健康时验证；
"后端 500""断网""慢响应"这类故障路径在真实后端上几乎无法按需制造。

另一个重复纳税点是登录：几乎每条用例都要先登录（UI 填表、提交、等跳转），
登录成了最慢的用例前置——十人用例十次登录，时间全烧在同一件事上。

Playwright 给出两个机制：`page.route` 在浏览器出网口拦截请求（中间人），
`storageState` 把登录态快照成文件复用。前端测试从此独立自主。

## What

`page.route(pattern, handler)` 是浏览器内的请求拦截器：请求离开浏览器即被handler 接管——`fulfill` 给假响应、`abort` 模拟断网、`continue` 放行。

`storageState` 是浏览器上下文（context，一组独立的 cookie/localStorage）的状态快照：存成 JSON，注入任意新 context 即"带着登录态出生"。


可以把 route 想成小区门口的代收点：快递（请求）出小区就被代收，
前台（真后端）全程无感；代收点可以按你的剧本发货（fulfill 假响应）、
直接拒收（abort）。但和代收点不同的是，拦截必须**在快递出门之前注册**——
route 注册发生在 `goto` 之前，晚了第一个请求已经漏过去。

storageState 则像酒店的房卡复制：真住一次（UI 真登录一次）拿到房卡
（快照文件），之后每次进门（新 context）直接刷卡，不再重复办理入住。
但和房卡不同的是，房卡长期有效，登录态快照会过期——token 失效后刷卡
会被拒（401），需要重建快照。

## When to Use

典型场景：

- 前端降级逻辑验证：abort 模拟断网，banner 停留加载态、列表为空——
  优雅降级（graceful degradation，依赖不可用时界面退到明确的提示状态
  而不是白屏报错）路径被真实测到。
- 错误分支：POST 注入 500，前端弹"下单失败"——故障注入一行代码即可制造。
- 提速：`**/api/slow-config` 被 fulfill 成 5ms 的 mock——同样结构、快 300 倍，
  banner 逻辑照常验证。
- 多角色权限测试：admin/user 两份登录态各自注入，UI 层与 API 层双重验证边界。

何时不用：要验证的是"前后端集成正确性"时（真链路套件的领地，如 lab 12/16），
桩会把集成问题挡在门外——mock 后端测不到后端；单一角色、登录极快的内网系统，
storageState 的收益也有限。

同类方式对比：

| 方式 | 差异 | 什么时候选它 |
|:---|:---|:---|
| 真链路 E2E | 集成真实，但依赖后端健康 | 集成回归 |
| route 桩 | 前端独立、故障可控 | 前端逻辑与降级分支 |
| API 造态登录 | 比 UI 登录快一个量级 | 登录态的常规生产方式 |

## Quick Start

前置条件：labs/16 的 Playwright 浏览器就绪。

```bash
cd labs/19_pw_network
./pw_network.sh    # 三组观察：网络桩 / 错误注入 / 双角色会话
ls .auth/          # admin.json / user.json 两份登录态
```

observe 的真实输出（2026-09-28 实测，节选）：

```
=====> [observe] ① 网络桩：不启动后端响应也能跑前端交互（route 全拦 /api/*）
============================== 3 passed in 0.47s ===============================

=====> [observe] ② 错误注入：500/断网 下 UI 优雅降级
======================= 2 passed, 4 deselected in 0.41s ========================

=====> [observe] ③ 登录态复用：storageState 保存 admin/user 双会话，互不串号
============================== 3 passed in 0.81s ===============================
-rw-r--r--@  1 hyhit  staff  183 Sep 28 21:09 admin.json
-rw-r--r--@  1 hyhit  staff  182 Sep 28 21:09 user.json
```

诚实预期：三组应全绿且都很快（合计不到 2 秒——没有一次真实登录、没有一次
慢接口等待，这正是桩与登录态复用的收益）。`.auth/` 下的两份 JSON 是运行时
生成的登录态文件，体积只有 180 字节左右。

关键代码（这段在做什么：拦截、注入、等待事件、存取登录态的五个关键调用）：

```python
page.route("**/api/**", handler)          # handler 里 fulfill 或 abort
route.fulfill(status=500, body=json.dumps(...))
with page.expect_event("dialog") as di:   # 对话框的确定性等待
    ...
context.storage_state(path=".auth/admin.json")
browser.new_context(storage_state=".auth/admin.json")
```

## How It Works

**route 桩的位置**：请求出浏览器即被拦截——fulfill 的假响应结构必须与真后端
一致（字段名、类型），前端处理逻辑才被如实验证。测的是前端处理响应的能力，
不是后端的快慢。glob 写 `**/api/**` 才能覆盖子路径；注册必须发生在
`goto` 之前，否则首个请求漏网。

**错误注入的两种形态**：`route.abort("connectionrefused")` 让请求在网络层
失败——与后端返回 4xx/5xx 不同，它模拟的是"根本连不上"；
`fulfill(status=500, ...)` 模拟"连上了但服务炸了"。两条降级路径都要测。

**对话框断言的事件等待**：前端弹 `alert` 时，Playwright 里它是事件而非元素。

`with page.expect_event("dialog") as di:` 建立等待上下文后再触发动作——本实验踩过坑：click 之后立即读回调列表是竞态，必须用事件上下文等待。

这是 lab 17 "断言结果不断言时刻"在事件型 UI 上的延伸。


**storageState 的内容与边界**：存档的是 localStorage 里的 token/role（SUT 据此鉴权）。

注意 `localStorage` 依赖站点 origin（协议+域名+端口的 origin概念）——about:blank 上读取会被拒，先 `goto` 再读。

双角色不串号的验证：admin 打开控制台看到统计、user 看到拒绝、user 的 token 直接打 admin API 仍是 403。


## Pitfalls & Q&A

踩坑清单（本实验真实踩过）：

- **about:blank 上读 localStorage**。现象：evaluate 被拒。原因：localStorage
  依赖站点 origin。解法：先 `goto` 到目标站点再读。
- **route 注册晚了**。现象：第一个请求没被桩住、打了真后端。
  解法：route 写在 `goto` 之前。
- **click 后立即读对话框回调**。现象：时绿时红。解法：
  `expect_event("dialog")` 事件上下文等待。
- **登录态过期**。现象：注入了 storageState 却仍然 401。
  解法：存"刷新凭证"或改用登录接口造态（API 登录比 UI 登录快一个量级），
  在 fixture 里自动重建。

深入问答：

- **Q：mock 后端后 E2E 还算端到端吗？** 分层看：前端交互层是端到端
  （浏览器→网络层→UI），业务正确性由真链路套件保障——两者互补，按目标选层。
- **Q：故障注入还能做哪些？** 超时（fulfill 延迟）、弱网（节流）、半响应
  （截断 body）——route 回调里都是一行事。
