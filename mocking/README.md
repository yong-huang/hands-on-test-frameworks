# 🎭 mocking/：服务虚拟化与 API 模拟 18 实验（Python 栈）

> 把 [../docs/mocking.md](../docs/mocking.md) 清单落成的可真实跑通系列——把「依赖不可控」练成「替身随手起」：
> 声明式地基（01-04）→ 录制回放与故障注入（05-07）→ 契约融合与零漂移（08-10）→ 多协议矩阵（11-14）→ 企业场景与治理（15-18）。
> 贯穿场景：**订单聚合 BFF（Backend for Frontend，聚合多个下游、专供前端的后端层）依赖支付/风控/短信三个 HTTP 下游**——
> 15 是设定本体，16/18 复用；07 先在同域的结账单下游上练穷举故障矩阵，15 再扩成三下游聚合。
> 与兄弟系列互补：labs/04 是进程内替身（monkeypatch），本线全是「独立 mock 服务」层；labs/14 是「真依赖」端、本线是「虚拟化」端；
> labs/15 的 Pact 产物被本线 09 直接当 stub 数据源；architect/08 的假支付网关在 05/06 直接复用。
> 每个实验 = apply/observe/clean 主演示脚本 + 六段式 README + 交互架构图三件套；环境一条命令见下方「快速开始」。

进度：**18/18 (100%)** ██████████████████

## 🚀 快速开始

前置条件：仓库根 venv（labs/00 体检通过）或任意 Python 3.11+；01 的服务端纯标准库，脚本另用 curl 与 lsof（macOS 自带）。

```bash
cd mocking/01_declarative_mock
./declarative_mock.sh all    # 起替身(:9100) → 特异度阶梯/响亮未命中/并发零错答 → 清理
```

诚实预期：02/03/04/07/14/17/18 需要 Docker（WireMock 官方镜像、testcontainers 拉 Kafka、act、compose 全家桶——
本机 Java 未装，WireMock 走 Docker）。

05/12/18 需要 `brew install hoverfly|grpcurl`（grpcurl 是 12 与 18 的 gRPC 探针）；16 需要 k6、08/10 用
`npx @stoplight/prism-cli`。本系列不需要任何模型/AI 环境。

## 📚 实验总表

| 实验 | 主题 | 一句话产出 | 验收亮点 |
|:---|:---|:---|:---|
| [01](01_declarative_mock/README.md) | 声明式替身 | 纯标准库按规则表自动应答的 mock server，改规则不改代码 | 特异度阶梯 0→10→20→30 分；「50 线程 × 20 轮，1000 个请求零错答」；hits=1006 对账 |
| [02](02_wiremock/README.md) | WireMock 迁移 | 01 的六条 stub 等价迁成 WireMock，同序列双打对账 | 10 场景逐字段等价；verify 从 unmatched 抓出 DELETE /orders/42 |
| [03](03_stateful_mock/README.md) | 状态机替身 | WireMock scenario 实现订单四态状态机 | 「4 态 × 3 动作转换表的 9 个非法跳转格子全部 409 且状态不变」 |
| [04](04_dynamic_response/README.md) | 响应模板 | Handlebars 模板让替身带随机性、请求回填与延迟 | 「100 次返回 100 个不重复订单号」全过 Schema；800ms stub「P95 806ms（95 分位延迟）」 |
| [05](05_hoverfly/README.md) | 代理录制回放 | Hoverfly capture 真上游、杀上游后 simulate 离线回放 | 「回放与录制逐字节一致 ✅（上游已死）」；注入 500 可逆 |
| [06](06_vcr_pytest/README.md) | 进程内录制 | vcrpy + pytest-recording 录成 cassette，socket 断网门防偷跑 | 回放全绿「2 passed in 0.06s」；新用例必红 `Network is disabled` |
| [07](07_fault_matrix/README.md) | 故障矩阵 | admin API 逐格注入 7 类场景，穷举结账客户端 7 个降级分支 | 「格子 7/7、分支 7/7」100% 命中专属分支、错格即红 |
| [08](08_prism/README.md) | 契约驱动 mock | Prism 吃 OpenAPI 起 mock，请求先验、应答按契约 | 契约 v2（+必填 channel）重启后「旧请求 422 红、新请求 201 绿」 |
| [09](09_pact_stub/README.md) | pact-as-stub | 自研百余行 stub 把 labs/15 的 pact 文件直接伺服成替身 | 「5 passed in 0.41s」；契约外 500 `interaction_not_found` |
| [10](10_drift_gate/README.md) | 漂移门禁 | 以真服务为基准做双向结构 diff 巡检，漂移归类为退出码 | 注入 created_at 删减 → `mock_missing: $.created_at` + 退出码 1 |
| [11](11_graphql_mock/README.md) | GraphQL 替身 | Ariadne 实现 schema 感知 mock：字段级错误、`X-Mock-Scene` 切换 | 「Cannot query field 'nonexistentField'」结构化 errors；场景 b amount=9999.0 |
| [12](12_grpc_mock/README.md) | gRPC proto 替身 | protoc 编译桩实现 unary + server-streaming，grpcurl 与 Python 双探针 | 反射发现服务；「流式 5 条事件全收且 seq 严格递增 1..5」 |
| [13](13_ws_mock/README.md) | WS 流式替身 | FastAPI WebSocket 三场景：订阅推送/断点续传/心跳踢线 | 「收 2 条断线重连后恰好续传 3..5」「静默超时被踢（close code 4000）」 |
| [14](14_event_mock/README.md) | Kafka 事件虚拟化 | testcontainers 拉真 Kafka，注入 正常/乱序/毒丸 三类事件 | 「毒丸进 DLQ（死信队列，收留处理失败消息的队列）：1 条」；「毒丸之后的正常事件不被阻塞（seq 4 已处理）」 |
| [15](15_downstream_chain/README.md) | BFF 依赖链 | 01 的替身顶上支付/风控/短信三下游，杀光真下游照样全绿 | 「真下游存活数 3/3 → 0/3」两模式全绿；注入 500 → PENDING_RETRY 不崩 |
| [16](16_perf_mock/README.md) | 虚拟化压测 | k6 100 VUs（并发虚拟用户）压虚拟化 BFF，双档延迟做容量敏感性实验 | 「P95 228 → 1555 ms」两档全程零错答；「替身命中 3000（精确对账，真下游未在场）……」 |
| [17](17_ci_lifecycle/README.md) | CI 生命周期 | act 真跑 mock 生命周期工作流：健康门、零残留、配置哈希缓存 | 「第 2、3 次缓存命中：mock 启动与冒烟全部 Skipped」 |
| [18](18_final_platform/README.md) | 🏁 终极平台 | 十七实验的替身能力串成 compose 六容器一键冷启动 | 「冒烟全绿：REST ✅ GraphQL ✅ gRPC ✅ BFF ✅ 消息 ✅」；漂移抓红归零放行 |

## 🧭 学习路线

按编号 01 → 18 即路线，五个阶段即能力等级：

1. **01-04 声明式地基**：自己写一个 → 等价迁到业界标准 → 加状态 → 加随机与延迟
2. **05-07 录制与故障**：代理录制回放 → 进程内 VCR → 穷举故障矩阵
3. **08-10 契约融合**：契约驱动 mock → pact 当 stub 数据源 → 漂移巡检门禁
4. **11-14 多协议矩阵**：GraphQL → gRPC → WebSocket → Kafka 事件
5. **15-18 企业场景与治理**：BFF 依赖链 → 受控压测 → CI 生命周期 → 🏁 compose 全家桶

## 🖼️ 架构图

每个实验 README 内嵌图三件套：images/*.svg（静态）+ 同名 .html（交互版，本地直接打开）+ .json 数据源（workflow/lifecycle），见各实验 What 节。

## ⚠️ 预期失败诚实标注

- 01 的「② 404 响亮未命中」是设计好的教学点：缺幂等键时两条候选规则各自说出拒绝原因
- 06 的新用例红来自断网门（`RuntimeError: Network is disabled`），不是环境故障
- 09 契约外交互打 stub 是 500、打真 provider 是 404——「stub 的职责边界就是契约」，不是 bug
- 12 的字段校验会让 grpcurl 非零退出（INVALID_ARGUMENT）——「红是验收的一部分」
- 16 首跑 100 VUs 错答率 1.27% 是实验产出（stdlib BFF 连接池缺陷），加固后归零
- 17 的 `reuse=true` 会跳过启动与冒烟两步（act 每次都是新容器）——「跳过即诚实」
- 18 的 compose up --build 首次较慢（拉镜像 + 编译），后续秒起；漂移注入被巡检抓红后恢复归零是收尾演示

## 🔧 环境要求

macOS（Apple Silicon 实测）/ Python 3.11+（venv）。

Docker：02-04/07 用 `wiremock/wiremock:3.13.0`、14 用 Kafka arm64 原生镜像、17 的 act、18 的 compose 六容器。

brew 工具按需：05 hoverfly 1.12.16、12/18 grpcurl 1.9.4、16 k6、17 act 0.2.89；Node 20+（08/10 的 Prism CLI 5.16.0）。

各实验统一 `apply | observe | clean | all`，`clean` 后零残留、端口确认空闲。
