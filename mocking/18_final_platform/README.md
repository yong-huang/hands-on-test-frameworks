# 18 · 🏁 终极串联：compose 全家桶一键冷启动 + 五路冒烟 + 漂移门禁

> 前十七个实验攒齐的替身能力，本篇串成 compose 全家桶：WireMock（REST 声明式）、
> GraphQL（11 复用）、gRPC（12 复用）、BFF+替身链（15 复用）、Redpanda（14 复用）
> 一键冷启动；smoke.py 五路探针全绿后，篡改 WireMock 应答注入漂移 → 门禁抓红
> → 恢复归零 → 看板落盘（✅/🔴）。

## Background

01-17 逐个学会了各种替身能力，但它们散在十个目录里——真要用的时候，
你得记住哪个实验用什么端口、哪个协议、哪种启动方式。终极串联把这些
能力合成一个 compose 全家桶：`docker compose up -d --build` 一条命令
冷启动，smoke.py 五路探针验证一切就绪。

五路探针不是走过场：REST 用 labs/15 的契约形状（WireMock 声明式），
GraphQL 打场景 b（大额风控），gRPC 用 grpcurl 探 unary，BFF 走虚拟化
模式聚合三下游，消息事件读 worker 的 GREEN 结果——每一路都是前面某个
实验的验收标准重跑。

## What

虚拟化平台全家桶是五类替身的 compose 编排 + 一个统一冒烟脚本 + 一个
能力看板。漂移门禁在冒烟收尾时演示：篡改 WireMock 应答 → 巡检抓红 →
恢复归零——这是 10 的漂移巡检在全家桶里的常态化运行。

| 路探针 | 打的是什么 | 复用实验 |
|:---|:---|:---|
| REST | WireMock 声明式映射（labs/15 契约形状） | 02 |
| GraphQL | 场景 b 大额风控数据（Ariadne） | 11 |
| gRPC | grpcurl unary（proto 替身） | 12 |
| BFF | 三下游聚合（虚拟化模式） | 15 |
| 消息 | Redpanda worker 的 GREEN 结果 | 14 |

compose down -v 销毁全家桶——下次 `up --build` 又是全新环境，这正是
「即用即弃基础设施」的替身价值。

## When to Use

典型场景：

- 系列收官后日常回归：全家桶 + 冒烟一条命令跑完。
- 新成员入职：clone 后跑一次，看见五路全绿就懂了整个系列在做什么。
- 替身平台的样板：把 compose 与 smoke.py 搬进真项目，只换 mappings。

何时不用：只需单个替身能力 → 直接去对应的单篇；要跑全量 CI →
17 的生命周期工作流管这个。

## Quick Start

前置条件：Docker daemon 在跑（OrbStack 自动探测）；grpcurl（gRPC 探针）；
仓库根 venv（含 httpx、PyYAML）。

```bash
cd mocking/18_final_platform && ./final_platform.sh all
```

实测输出（节选）：

```
=====> [observe] ② 五路冒烟 + 漂移门禁演示（smoke.py 自带全部断言与看板生成）
① REST 探针
  ✅ REST：labs/15 契约形状（WireMock 声明式） — status=200
② GraphQL 探针
  ✅ GraphQL：场景 b 大额风控数据 — amount=9999.0
③ gRPC 探针
  ✅ gRPC：grpcurl unary 合法应答 — status=created
④ BFF 聚合探针
  ✅ BFF：三下游聚合全绿（虚拟化模式） — payment=TXN-MOCK-001
⑤ 漂移演示：篡改 WireMock 的 /orders 应答 → 巡检抓红 → 恢复归零
  ✅ 注入漂移被巡检抓红（items 字段删空） — 1 处
  ✅ 恢复后归零放行

>>> 冒烟全绿：REST ✅ GraphQL ✅ gRPC ✅ BFF ✅ 消息 ✅ + 漂移门禁演示 ✅
```

诚实预期：compose up --build 首次较慢（拉镜像 + 编译），后续秒起；
消息探针读 worker 结果文件（常驻 broker 多轮累积按守恒断言）；漂移
注入通过 admin API 完成，文件 mappings 目录只读挂载防 DELETE-all 误删。

## How It Works

**compose 是全家桶的装配清单**。六容器一个 YAML：WireMock 挂只读
mappings、GraphQL 与 gRPC 各自 Dockerfile 构建、Redpanda 开发模式。

BFF 与 mockdown 用 python slim 镜像卷挂脚本。每个容器都是前面某个
实验的产物，compose 只是宣布启动顺序与端口。

**冒烟是五路探针 + 看板生成**。smoke.py 按协议逐路发探针，每路断言
其对应实验的验收标准；结果写 dashboard.html（✅/🔴 逐行），本次
Green 后自动做漂移演示（改 WireMock 应答 → 巡检抓红 → 恢复归零）。

**只读挂载防 DELETE-all 误删**。WireMock 的 mappings 目录如果读写
挂载，admin API 的 delete-all 会把宿主文件也删掉——冒烟第一次跑漂移
演示后就 404 了。解法：:ro 挂载，admin API 的变更只影响内存，重启
即恢复文件里的原始映射。

## Pitfalls & Q&A

踩坑清单：

- **mappings 目录被 delete-all 清空**。现象：漂移演示后再查 /api/orders
  返回 404。原因：WireMock 的 admin API DELETE 会把读写挂载目录里的
  映射文件也删掉。解法：:ro 挂载，注入与恢复都走 admin API 而非文件。
- **compose 内容器间不可达**。现象：BFF 连 mockdown 报 Connection
  refused。原因：容器内服务绑 127.0.0.1，只收容器内回环。解法：绑
  0.0.0.0（容器化场景本该如此）。
- **compose down -v 会删卷**。现象：下次 up 后数据消失。原因：-v 删
  匿名卷与命名卷。解法：本篇替身全为无状态应答者，删卷即「全新环境」
  ——这正是想要的效果。

深入问答：

- **Q：这18 个实验跑完后，真实项目里怎么用？**
  按需组合：REST 依赖 → 01/02；GraphQL → 11；gRPC → 12；事件 → 14；
  聚合层 → 15；压测 → 16；CI → 17。全家桶（本篇）是它们的组合示范
  与系列收官，不是让你照搬 compose——搬的是模式，不是文件。
- **Q：看板只有一个 HTML，能接 Grafana 吗？**
  能：dashboard.html 的数据源是 reports/drift.md 与 status JSON——
  接 Grafana 需要把断言结果推成 Prometheus 指标或 JSON API，那是
  生产化方向，本篇用最小 HTML 让「看板」概念可跑可验。
- **Q：全系列 18 个实验做完，下一步学什么？**
  契约测试进阶（labs/15 的 Broker 模式）、混沌工程（随机故障注入）、
  流量录制回放的生产化（Hoverfly 集群）——替身是起点，不是终点。
