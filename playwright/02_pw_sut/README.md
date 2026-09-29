# 02 · 靶场 SUT「pw-store」：一个端口装下整个系列的全部靶点

> 被测系统（SUT，System Under Test）决定测试能练到什么。
> 本实验造一个 Vite + React 的多功能区应用：双角色登录、订单 CRUD、
> WebSocket（浏览器与服务器的全双工长连接通道）实时状态推送、文件上传下载、慢接口、
> iframe（页面内嵌另一个文档的框架）与 Shadow DOM（挂在元素内部的独立 DOM 子树，
> 常规 CSS 选择器看不到）。后续 17 个实验全部打它，靶点稳定且可复现。

## Background

拿公共演示站（如 the-internet）练 E2E，问题有三个：结构随时可能变、网络不可控、
场景凑不齐——想测"实时推送驱动的状态变更"或"admin 才能删的权限差异"，公共站没有这些功能。

真实业务系统又太重：登录要接 SSO，数据要过审批。折中方案是自造一个**功能超集靶场**：
每个测试特性（认证、上传、实时、慢加载、帧嵌入）都有一个专设的页面与接口，
并且所有行为可重置、可预测。

pw-store 就是为这个系列定制的靶场。它故意保留一些"教学事故现场"：
订单状态由服务端定时器自动演进（created → paid → shipped），慢接口固定延迟 1.2 秒，
文件列表跨请求累积——这些正是后续实验要驯服的不确定性来源。

重启进程后一切回到种子状态（seed，预置的初始数据集，进程启动时写入内存），
实验之间互不污染。

## What

pw-store 是一个单进程 Node 服务：静态托管 Vite 构建出的 React 单页应用（SPA），
同端口提供 JSON API 与 WebSocket（WS，浏览器与服务器的全双工长连接通道）。
双角色账号（admin / customer）贯穿全部功能区。

可以把整个服务想成一栋四层的自助仓储大楼：前台（登录）发两张不同权限的门禁卡，
订单区的大屏（WS）实时播报每件货物的状态变化，文件区提供带封条编号
（sha256，文件内容的哈希指纹——内容相同则值相同）的存取柜，
顶楼还有一间故意走线很慢的办公室（慢接口）。

但和真实大楼不同，这栋楼每晚打烊即复原——重启进程，一切回到种子状态。

![pw-store 靶场架构：浏览器进程与 pw-store 进程的六条通路](images/pwstore.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/playwright/02_pw_sut/images/pwstore.html)
> （或本地打开 [`images/pwstore.html`](images/pwstore.html)）。
> 图中两条虚线是 WS 的两个方向：服务端定时器把状态演进广播给全端（右下绕行线），
> SPA 订阅后驱动 UI 更新（左下绕行线）。

## When to Use

| 场景 | 自造靶场 | 公共演示站 | 生产环境冒烟 |
|:---|:---|:---|:---|
| 练框架能力（等待/定位/断言） | ✅ 场景凑齐 | ✅ 够用 | ❌ 动生产数据 |
| 测认证矩阵、实时推送等复合场景 | ✅ 专设靶点 | ❌ 无此功能 | 需专门测试账号 |
| 断言稳定性要求高（视觉基线、sha256 比对） | ✅ 完全可控 | ❌ 随时会变 | ⚠️ 数据不可预测 |
| 验证线上真实可用性 | ❌ 不是生产 | ❌ | ✅ 唯一正确选择 |

判断口径：**学测试技术用自造靶场，验业务健康用受控的生产冒烟**。两者不可互相替代。

## Quick Start

```bash
# 首次运行前：准备 node 依赖与三浏览器构建（缺失时脚本也会提示）
bash playwright/load_resources.sh

cd playwright/02_pw_sut
./sut_app.sh          # 全流程：apply 构建+启动 → observe 五步探活 → clean 清理
./sut_app.sh observe  # 已在跑，只看演示
```

apply 阶段做三件事：`tsc` 类型检查、`npx vite build` 构建前端（产物进 `app/dist`）、
起服务并用 `/api/health` 探活。observe ① 先在 API 层验证登录与订单：

```
=====> [observe] ① 六大功能区 API 层探活
>>> health: {"status":"ok","zones":["orders","upload","slow","embed"]}
>>> admin token: YWRtaW46YWRtaW4=…
>>> orders:  {"orders":[{"id":"55d9c2eb","title":"机械键盘","status":"shipped",…
```

observe ③ 用 5 行 Node 脚本验证 WebSocket 通道（连接即收到 welcome 帧）：

```
=====> [observe] ③ WebSocket 通道探活（连接即收 welcome 帧）
>>> WS 帧: {"type":"welcome","zones":1}
```

observe ④ 跑 8 条靶场自检冒烟用例，把每个功能区在真实浏览器里走一遍：

```
=====> [observe] ④ 靶场自检冒烟（8 条 UI 用例，chromium）
  8 passed (5.5s)
```

浏览器手动体验：`open http://127.0.0.1:9002`，账号 `admin/admin123` 或
`customer/customer123`。验收方式：`./sut_app.sh all` 全流程无报错，
冒烟 8 条全绿，clean 后 `lsof -i :9002` 无残留进程。

## How It Works

**单端口四类流量。** 一个 Node http server 同时承担：静态文件（`app/dist`）、
JSON API（`/api/*`）、文件上传下载、WebSocket。

WS 复用 HTTP 端口靠的是协议升级（upgrade）机制：浏览器先发一个带
`Upgrade: websocket` 头的 HTTP 请求，服务端同意后这条 TCP 连接就切换成
WS 帧协议（帧 frame，WS 连接上传输的最小数据单元，本实验里是一条 JSON 文本）。

对测试的意义：mock 或屏蔽一条端口就能同时控制页面与推送（lab 15 的做法）。

**双角色与可逆 token。** token 就是 `base64("role:username")`——明文可逆，
生产环境绝不这样做，但靶场里这是刻意设计：测试可以直接构造或解码 token
来断言角色语义，不必先破解签名机制。

admin 与 customer 的权限差异落在两处：`DELETE /api/orders/:id`（仅 admin）
与 UI 的删除按钮可见性，lab 04 逐条断言。

**状态演进的确定性异步。** 新订单创建后，服务端用两级 `setTimeout`（各 2 秒）
把它从 created 推到 paid 再到 shipped，每步经 `ws.send` 广播给所有连接。

这是**服务器时钟驱动的真实异步**——比"前端假装转圈"更接近生产，
也让"实时推送 1 秒内驱动 UI"这类断言有了稳定的时间窗。

**可测性三件套。** `/api/reset` 把订单重置回 3 条种子数据（seed，admin 权限）；
进程重启即全量重置（内存态）。

`data-testid` 属性贯穿全部交互元素——比如登录按钮写着
`<button data-testid="login-btn">`，测试用 `page.getByTestId('login-btn')` 定位
（见 `tests/sut_smoke.spec.ts`）。

定位优先走 testid 而不是脆弱的 CSS 样式路径，这是靶场与生产前端的共同最佳实践。

## Pitfalls & Q&A

**Q：为什么冒烟用例断言文件列表用 `filter({ hasText })` 而不是全量 `toHaveCount(2)`？**
本靶场真实踩过的坑：SUT 状态在服务器内存里**跨用例累积**——observe ② 已
用 curl 传过探活文件，UI 用例再传 2 个时列表是 3 条，全量计数断言必红。

正确做法有两个：断言"自己传的东西存在"（filter），或用例前置调 `/api/reset`。
lab 10（并行与隔离）会把这个问题系统化。

**Q：为什么上传接口用 raw body 而不是标准 multipart 表单？**
multipart（浏览器表单默认的编码，body 里混合边界符与文件段）需要服务端解析库；
raw body + `?name=` 参数让服务端零依赖。

对测试的影响：`setInputFiles` 照常工作（它只负责把文件塞进 `<input type=file>`，
怎么发是前端的事），lab 14 的下载比对还能直接用接口返回的 sha256 做完整性断言。

**Q：订单状态演进用例怎么写才不 flaky？**
状态跃迁发生在创建后约 2 秒，`expect(row).toHaveAttribute('data-status', 'paid', { timeout: 5000 })`
的 web-first 重试机制正好覆盖这个时间窗：断言反复轮询属性值，paid 出现即通过。

硬等 `waitForTimeout(2000)` 也能过，但它把"不确定"固化成了"固定等待"——
又慢又脆，是反模式。

**Q：端口为什么是 9002 而不是接着 labs/ 的 89xx 继续？**
labs/ 目录的 Python 系列已占用 8901-8930 段。playwright/ 系列从 01 重新编号，
端口用 90NN（本实验 9002），两套系列同时跑也不会撞端口。

**Q：iframe 里的页面是独立的站点吗？**
不是。`/embedded.html` 与主应用同源（同协议+同域名+同端口），只是被 iframe
嵌入展示。

同源意味着测试不需要处理跨域，`frameLocator` 可以直接穿透操作——
lab 03 专门讲 iframe 与 Shadow DOM 两类"嵌套文档"的定位。
