# 02 · WireMock 等价重做：把自研替身换成业界标准

> 自研 mock（见 [01](../01_declarative_mock/README.md)）回答了「匹配引擎长什么样」，
> 但停在能跑。WireMock（JVM 生态事实标准的 HTTP 替身服务器；JVM 即 Java 虚拟机）
> 是同一套问题的产品化答案。
>
> 本实验把 01 的六条 stub（存根：一条「请求长什么样 → 应答什么」的规则）等价
> 迁移成 WireMock mappings（映射文件：请求匹配器 + 响应定义的 JSON 记录），
> 同一份 10 场景请求序列双打对账——status、命中规则、JSON body 逐字段全等，
> 再用 verify（WireMock 内建的请求验证查询）从请求留痕里抓出未预期请求。

## Background

01 造出最小匹配器后，一个工程问题悬着：真实团队不会用自研小工具，会选
成熟工具。换成成熟工具时，01 里「能跑」的场景还能跑吗——规则怎么搬、
语义差在哪、哪些能力是白造的、哪些是工具真没给的？

逐个接口人肉点一遍不可靠：请求一多就漏。可靠的做法是等价对账——把
01 的全部场景收成一份固定的请求序列，分别打到自研实例和 WireMock，
逐字段比响应。等价成立，迁移才敢上线；不等价的格子，就是差距清单本身。

## What

WireMock 是一个按预写规则自动应答的独立 HTTP 替身服务器，规则文件叫
mappings（一条 = 请求匹配器 + 响应定义），启动时从 `mappings/` 目录加载，
和管理端点（`/__admin/*`）同进程。01 的概念几乎一一对应，两处关键差异：

| 概念 | 自研（01） | WireMock |
|:---|:---|:---|
| 规则条目 | stub，存 `stubs/*.json` | mapping，存 `mappings/*.json` |
| 谁应答的标记 | `X-Mocked-By` 响应头 | 同样用响应头，但要在 mapping 里静态声明 |
| 优先级 | 特异度自动评分（约束多者胜） | 手工 `priority` 数字（1 最高） |

可以把 priority 想成 01 那张分数表的**手写版**：自动评分不会忘写，
手工数字一目了然但得自己保证「更细的规则数字更小」。01 的四级阶梯
在这里排成 P1（POS+大额）→ P4（兜底），颠倒一处对账当场翻车。

![WireMock 等价重做：同一序列双打两套替身，逐字段对账并留痕](images/wiremock.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/mocking/02_wiremock/images/wiremock.html)
> （或本地打开 [`images/wiremock.html`](images/wiremock.html)）。

图里两条对照通路：10 场景序列双打到两套替身，响应在逐字段 diff 处汇合
出等价结论；WireMock 侧另有全量留痕（`__admin/requests`），verify 从
unmatched（未被任何 stub 接住的请求）里抓出意外流量。

## When to Use

典型场景：

- 团队要统一替身工具：自研适合懂原理，落地协作要选有生态的（文档、
  IDE 插件、多协议扩展）。
- 需要「请求都发生了什么」的证据链：联调排障、CI 里审计意外流量。
- 后续要状态化、响应模板、录制回放：这些都是 WireMock 内建能力
  （状态化/模板见本系列 03/04，录制回放见 05）。

何时不用：只想理解匹配语义本身 → 01 的百行实现更短；要验证双方对接口
的预期 → 契约测试（[labs/15](../../labs/15_pact/README.md)）。

等价对账之外的六行能力差距表（验收产物，自研视角）：

| 能力 | 自研（01） | WireMock |
|:---|:---|:---|
| 优先级 | 特异度自动评分 | 手工 priority，规则多时靠人脑维护 |
| 未命中 | 404 带逐条失败诊断 | 404 空 body，诊断走 admin API 查询 |
| 请求留痕 | 逐 stub 命中计数 | 完整请求日志 + unmatched 过滤 |
| verify 断言 | 无，客户端自带断言 | 内建（匹配/近失（差一点就命中）计数查询） |
| 状态化/模板 | 无（03/04 主题） | scenario 状态机 + Handlebars（按请求生成响应的模板语言）模板 |
| 运行形态 | 纯标准库单文件 | JVM 应用，Docker 容器交付 |

## Quick Start

前置条件：仓库根已建 venv（labs/00 体检通过）；Docker 在跑，镜像已拉：
`docker pull wiremock/wiremock:3.13.0`（本机走镜像加速，2026-10-23 实测成功）；
脚本另用 curl 与 lsof（macOS 自带，Linux 需自行安装）。

```bash
cd mocking/02_wiremock && ./wiremock.sh all
```

实测输出（节选）：

```
=====> [apply] ① 清场 + 起自研 mock(:9110，复用 01 代码与 stubs) 与 WireMock 容器(:9200)
--- WireMock 已加载的 mappings（priority 1 最高）---
  P1  order-pos-big        POST /orders
    ……

① 等价对账：10 个场景，自研 vs WireMock 逐字段比对
  ✅ [ 1] 兜底弱规则 — status 201/201 stub order-any/order-any body=
  ✅ [ 4] POS 头 + 大额体 — status 201/201 stub order-pos-big/order-pos-big body=
  ✅ [ 5] 边界 amount=1000 — status 201/201 stub order-any/order-any body=
  ✅ [ 9] 缺幂等键 — status 404/404（404 body 语义差异见差距表）
    ……

② verify 断言：抓出一次未被任何 stub 预期的真实请求
  ✅ DELETE /orders/42 出现在 unmatched 留痕 — unmatched 共 3 条
    ……

>>> 验收：10 场景逐字段等价 ✅ verify 抓到未预期请求 ✅
```

诚实预期：场景 1-8 命中的规则与 body 必须双方全等；场景 9-10 只对账
404 状态码——自研给诊断 body、WireMock 给空 body，这是差距表里的一行，
不是对账失败。验收线是「10 场景全 ✅ + verify 抓到 DELETE /orders/42」。

## How It Works

**mappings 是 01 规则表的产品化**。四级阶梯翻译成 priority 1-4，体条件用
`matchesJsonPath`（在 JSON body 上跑路径过滤，命中非空才算匹配），存在性
header 用正则 `".+"`——对照 01 的约定值 `"*"`：

```json
{"priority": 1, "request": {"method": "POST", "urlPath": "/orders",
  "headers": {"X-Channel": {"equalTo": "pos"}},
  "bodyPatterns": [{"matchesJsonPath": "$[?(@.amount > 1000)]"}]}}
```

每个 mapping 的响应静态携带 `X-Mocked-By`——Quick Start 输出里的
`stub order-pos-big/order-pos-big`，就是两边各自报出的应答者身份，
对账引擎据此断言「同一个请求，两套替身由同语义的规则接住」。

**等价对账是迁移的安全网**。同一请求序列双打后逐字段比 status、
`X-Mocked-By`、JSON body；场景 5（amount=1000 不满足 `> 1000`）和
场景 6（web 渠道不满足 equalTo pos）专门验证匹配边界——差一个比较符，
对账表当场翻红，这正是手工迁移最容易错的地方。

**留痕把「未预期」从猜测变成查询**。WireMock 记录每个进站请求，
`GET /__admin/requests?unmatched=true` 直接列出没被任何 stub 接住的；
verify 断言（验收②）就是查这个列表并断言目标请求在里面。

## Pitfalls & Q&A

踩坑清单：

- **mappings 文件裸数组不认**。现象：容器启动即抛
  `MappingFileException ... Cannot deserialize ... Array`。原因：单文件多
  规则要 `{"mappings": [...]}` 包裹，裸 JSON 数组不在反序列化预期里。
- **健康检查「任一通过」输给 JVM 慢启动**。现象：apply 打印 mappings 时
  拿到空响应。原因：自研 mock 毫秒级就绪就触发了「任一 URL 通过」，而
  WireMock 的 JVM 还在启动；解法：健康门改成「列表里全部 URL 通过才放行」。
- **bash 变量后跟全角标点**。现象：`MOCK，: unbound variable` 一类乱码报错。
  原因：`$MOCK，` 里的全角逗号被 bash 连同多字节编码吞进变量名；解法：
  非 ASCII 字符紧邻变量时写 `${MOCK}`。

深入问答：

- **Q：等价对账能证明两套替身完全等价吗？**
  证明的是**选定序列上的可观测行为等价**：status、应答规则语义、body
  字段。响应 header 只比了 `X-Mocked-By` 一项（WireMock 不发
  `X-Match-Score`——它没有特异度概念，这正是差距表第一行）。序列覆盖
  越狠，结论越可信。
- **Q：WireMock 为什么不给未命中写诊断 body？**
  工具哲学不同：它把「为什么没命中」做成留痕查询（unmatched 留痕 + near-misses
  近失分析，近失 = 差一点就命中的候选请求），响应本身保持干净；01 把诊断
  塞进 404 是教学选择——客户端不开调试器也能看到原因。两种取向都能做到
  「未命中响亮」。
- **Q：既然等价，生产该用哪个？**
  等价只覆盖这 10 个场景。选型看差距表：团队协作、留痕审计、后续要
  状态化与录制 → WireMock；嵌入式单测、零依赖起停 → 01 那种自研
  （或 vcrpy 这类进程内录制回放库，本系列 06 的主题）。
