# 05 · 契约先行工作流：先写契约再写实现，漂移一秒报红

> 接口文档和实现各自演化，联调时才发现对不上——这是集成阶段最贵的意外之一。
> 本实验把契约写成进 git 的 OpenAPI 文件（接口的机器可读描述），schemathesis
> 把契约的每个操作变成 property-based 测试：忠实实现被 364 条随机生成案例
> 全绿放行；篡改实现、或契约单方面升级，同一条命令报红并给出 curl 复现命令。

## Background

之前的做法：接口文档躺在 wiki 里，实现按开发者的理解演化，对接方按过期
文档开发。文档靠人手维护，从写下的那一刻就开始腐烂。

痛点的核心是**偏差发现得太晚**：实现与文档的漂移要到集成联调才炸——正是
项目 1 漏斗里靠右、贵的关卡。契约先行的主张：把「接口长什么样」做成机器
可读、可校验、进 git 的文件（OpenAPI），让机器代替人盯一致性。

本实验交付这套工作流的最小闭环：先写 `contract.yaml` 再写实现，schemathesis
从契约自动生成大量随机请求打真实服务，任何单向偏离一秒报红。

## What

契约先行是一种开发工作流：先把接口写成 OpenAPI 契约（描述路径/方法/参数/
响应结构的标准格式）并提交版本库，实现与测试都以契约为唯一真理；
schemathesis 基于契约做 property-based 测试——自动生成大量随机输入调用
接口、逐响应校验，例子不用人写。

可以把契约想成合同的甲乙方条款，schemathesis 是按条款随机抽查的审计员。
但和审计员不同的是，它只核对「实现是否符合条款」「条款自身是否自洽」，
条款本身合不合理（业务对错）仍要人来审。

![契约、实现、schemathesis 三者的防漂移关系](images/contract_first.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/shiftleft/05_contract_first/images/contract_first.html)
> （或本地打开 [`images/contract_first.html`](images/contract_first.html)）。
> 双向箭头是本实验的题眼：实现→契约与契约→实现两个方向的漂移都会报红。

## When to Use

- 多团队对接的接口：契约进 git，消费方按契约先开发——对方还没实现时，先用
  挡板（stub，按契约假装成真实服务的替身）顶着联调（替身服务属规划中的项目 6）。
- 重构防回归：重构实现期间契约测试保持全绿，等于对外行为没变。
- 公共库/网关接口的准入：新实现过契约测试才允许接入。

何时不用：单人原型快速迭代期（契约维护成本大于收益）；一次性内部接口。

同类方案对比：

| 方案 | 差异 | 什么时候选它 |
|:---|:---|:---|
| 手写接口测试 | 例子人写，覆盖靠自觉 | 核心路径的定向断言 |
| 本工作流（schemathesis） | 契约生成海量案例，覆盖结构 | 契约已存在的接口 |
| pact 消费方驱动契约 | 消费方期望驱动，可平台化治理 | 微服务多消费方（见 architect 15） |

## Quick Start

前置：仓库根 `.venv`（schemathesis 4.x + fastapi + uvicorn + pyyaml）。
三份道具内置：`contract.yaml`（真理）、`app_good.py`（忠实实现）、
`app_bad.py`（篡改版）。

两个实现都是 FastAPI（Python 的 Web 框架）应用，由 uvicorn（把应用跑成本机
HTTP 服务的服务器）启动。一条命令跑完整动线：

```bash
./contract_first.sh   # apply → observe（全绿+两种报红）→ clean
```

第一步，忠实实现 × 契约——property-based 案例全绿，规模看实测统计：

```text
.....                                                                    [100%]
============================== schemathesis 执行规模 ===============================
实际执行生成案例：364 条
5 passed in 2.10s
```

第二步，篡改实现（响应漏掉 price 字段 + 未声明的 400）——报红且给复现命令：

```text
  | - ST108 Response violates schema
  |     curl -X POST -H 'Content-Type: application/json' -d '{"name": "0", "price": false}' http://127.0.0.1:8933/api/items
  | - ST103 Undocumented status code
  |     curl -X GET http://127.0.0.1:8933/api/items/0
2 failed, 3 passed in 1.10s
```

第三步，契约单方面升级到 v2（Item 新增必填 createdAt，实现未跟进）——同样红：

```text
  | - ST108 Response violates schema
  |     "createdAt" is a required property
    | "createdAt" is a required property
1 failed, 4 passed in 1.56s
```

诚实预期：案例数每次运行不同（随机生成，本机实测 236~364 条，5 个操作）；
验收线「≥50」是下限。报红定位到「检查编号 + 违反点 + curl」三要素，可复现。

## How It Works

**从契约到测试是全自动的一跳**：`schemathesis.openapi.from_dict` 读契约文件，
`@parametrize(schema=schema)` 把契约里每个操作变成一个 pytest 测试项。

执行时由底层的 hypothesis（随机输入生成库）分两阶段生成输入——合法（应被接受）与非法（应被
明确拒绝），`call_and_validate` 发真请求并逐响应校验。核心三行：

```python
schema = schemathesis.openapi.from_dict(raw)          # 契约是唯一输入
@parametrize(schema=schema)                           # 每个操作一个测试项
def test_contract_first(case, base_url):
    case.call_and_validate(base_url=base_url, checks=CORE_CHECKS)
```

**检查集显式只留核心四件**：不允许 5xx、状态码在契约内、内容类型一致、
响应体符合 schema。默认集还带 Allow 头等框架向检查（ST205），与 FastAPI 的
405 行为打架——那是框架怪癖不是契约违反，聚焦语义就显式圈定。

**被测实现热切换**：conftest（pytest 约定自动加载的共享配置文件）按 `APP_IMPL` 环境变量起对应的 uvicorn 子进程
（good/bad），测试代码零改动——「同一条命令报红」的对照就是这么来的。
契约文件本身用 `CONTRACT` 环境变量切换，v2 演示契约领先实现。

**防漂移是双向的**：改实现不改契约（漏字段、私有状态码）→ ST108/ST103 红；
改契约不改实现（新增必填字段）→ 「createdAt is a required property」红。

契约进了 git，两边谁先动、谁没跟上，测试说话——这正是 contract-first 的
工作流本体：任何变更先落契约（一个 diff 可评审），实现跟进，测试转绿。

## Pitfalls & Q&A

常见故障与解法：

- **契约必须如实记录实现的错误形状**：FastAPI 校验失败的 422 里 `detail` 是
  错误对象数组，畸形 JSON 是 400 且 `detail` 是字符串。形状写错，忠实实现
  也会红——红的时候先分辨「实现错」还是「契约错」。
- **4.x 的 parametrize 只收关键字参数**：`@parametrize(schema)` 位置传参会
  `TypeError`，必须 `@parametrize(schema=schema)`。
- **默认检查集与框架打架**：见到 ST205（Allow 头）先判断是契约问题还是框架
  怪癖，怪癖用显式 `checks=[...]` 圈定语义范围，不要一刀切关检查。

Q&A：

- **364 条案例怎么来的，会不会重复？** 5 个操作 × hypothesis 每操作默认生成
  量，随机不重复（可配 `GenerationConfig.max_examples`）。案例多不是堆数量：
  非法输入那半正是手写测试懒得写的部分。
- **随机请求会不会打脏数据？** 本实验实现是内存字典随起随销。真实服务要考虑
  状态性——schemathesis 支持状态机测试，进阶再开。
- **和 architect 15 的契约测试什么关系？** 那边是消费方驱动的 pact（平台化
  治理 provider 版本矩阵）；这边是 provider 侧的契约先行开发流，两个方向互补。
