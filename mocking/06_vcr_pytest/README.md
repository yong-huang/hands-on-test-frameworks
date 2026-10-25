# 06 · VCR 式 pytest 离线化：进程内录制回放，socket 级防偷跑

> 05 的 Hoverfly 是独立服务，本篇把录制回放塞进测试进程：vcrpy（进程内 HTTP
> 拦截库）+ pytest-recording（pytest 插件）让集成测试打一轮真上游后，交互
> 落成 YAML cassette（磁带文件）。实测：杀掉上游进程断网，`--record-mode=none
> --block-network` 回放全绿——socket 级断网门保证零真实网络请求；新增无
> cassette 的用例必红（`Network is disabled`），防偷跑有硬保证。

## Background

测试替身的两条路线在此会师：手工替身（[labs/04](../../labs/04_mock/README.md) 的
monkeypatch——运行时把函数临时替换成假实现的手法；freezegun——把时钟冻结在
指定时刻的库）精确但每条要手写。

独立服务替身（[05](../05_hoverfly/README.md) 的 Hoverfly）能录真实交互，但要
多跑一个进程、管一套端口与生命周期。

pytest 套件要的是第三种形态：拦截发生在测试进程内部，用例代码一行不改，
录制产物是普通文件随仓库走。代价是拦截依赖客户端库的补丁机制——
「请求真的被拦住了吗」从架构直觉变成必须验证的问题，本实验的断网门
就是为这个问题准备的。

## What

vcrpy（名字取自 VCR，盒式磁带录像机——与下文 cassette/磁带的比喻同源）
是进程内录制回放库：在测试期间给 HTTP 客户端库（httpx/requests 等）
打补丁，请求先经它检查——cassette 里有匹配记录就回放，没有就（录制模式下）
放行到真实网络并把交互记下来。

pytest-recording 是它的 pytest 插件：`@pytest.mark.vcr` 一个标记管一次
录制，cassette 落成 YAML 文件（`tests/cassettes/<模块>/<用例>.yaml`）。

可以把 cassette 想成一盘只属于单个用例的录音磁带：里面录的是「请求-响应对」，
格式是 YAML，随测试文件进 git。但和独立服务替身不同的是：拦截发生在
进程内——「没拦住」不会报错而会泄漏，所以需要一把 socket 级的锁
（下文的断网门）。

![录制轮经 vcrpy 打真上游落 cassette，回放轮 socket 断网下回放并无录制必红](images/vcr.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/mocking/06_vcr_pytest/images/vcr.html)
> （或本地打开 [`images/vcr.html`](images/vcr.html)）。

图里录制轮（左）与回放门禁轮（右）共用同一批测试代码；cassette 是两轮
之间的唯一纽带，socket 断网门保证回放轮零真实网络。

## When to Use

典型场景：

- pytest 套件离线化：集成测试录一轮，CI 里永远回放——快且不受第三方
  可用性拖累。
- 第三方 API 的 fixture 沉淀：真实响应形状比手造数据可信，cassette 就是
  最诚实的测试数据。
- 防偷跑红线：团队要求「单测绝不触网」——none 加 block-network 是
  可执行的门禁，而非口号。

何时不用：

- 替身要给多个消费方共享（前端、其他服务）→ 独立服务形态
  （[05 Hoverfly](../05_hoverfly/README.md)、[01 声明式](../01_declarative_mock/README.md)）。
- 拦的是浏览器请求 → [playwright/05](../../playwright/05_pw_network_pro/README.md)。

| 方案 | 差异 | 什么时候选它 |
|:---|:---|:---|
| 独立服务替身（[05](../05_hoverfly/README.md)/[01](../01_declarative_mock/README.md)） | 进程外，多消费方共享 | 联调环境、跨团队共享 |
| 进程内录制回放（本篇） | 零部署，用例级生命周期 | pytest 套件离线化与防偷跑 |
| 手工替身（labs/04） | 每条手写，无录制 | 替代纯函数级依赖 |

## Quick Start

前置条件：仓库根 venv 已装 `pip install vcrpy pytest-recording httpx`
（本机 vcrpy 8.3.0、pytest-recording 0.14.0、httpx 0.28.1 ✅）。

上游复用 [architect/08](../../architect/08_mock_server/README.md) 的假网关；
另用 curl 与 lsof（macOS 自带）。

```bash
cd mocking/06_vcr_pytest && ./vcr_pytest.sh all
```

实测输出（节选；pytest 计时逐次浮动）：

```
=====> [observe] ② 录制：pytest 打真上游，交互落成 YAML cassette
..                                                                       [100%]
2 passed in 0.07s
--- cassette 内容（test_pay_and_status.yaml，节选）---
interactions:
- request:
    body: '{"order":"ORDER-FIXED-001","amount":4200}'
    ……

=====> [observe] ③ 断网：杀掉上游进程，none 模式回放——测试代码零改动
..                                                                       [100%]
2 passed in 0.06s
断网回放全绿 ✅（上游已死 + none 模式 = 零真实网络请求）
    ……

>>> 验收：录制 ✅ 断网回放全绿 ✅ 零真实网络 ✅ 新用例必红防偷跑 ✅ cassette 可读可 diff 可进 git ✅
```

诚实预期：③ 的 2 passed 是回放——上游进程已被杀（脚本先验证端口清空），
叠加 `--block-network` 的 socket 断网，测试不可能碰到任何真实网络；④ 的
新用例红得可辨认：`RuntimeError: Network is disabled` 来自断网门，
不是环境故障。

## How It Works

**进程内拦截 = 给客户端库打补丁**。vcrpy 按 httpx 的传输层（真正发出
请求的那一层）包了一层：
请求先问 cassette「有没有匹配的交互」——有则原样回放，无则看模式。

`@pytest.mark.vcr` 声明这个用例要磁带，cassette 名默认取用例名，
落在 `tests/cassettes/<模块>/` 下。

**cassette 是普通 YAML**。请求方法、URI、头、body 与响应全部可读——
Quick Start 节选里那段 `body: '{"order":"ORDER-FIXED-001",…}'` 就是真
上游收到的原始请求。可 diff 意味着重录一次，评审只看增删行。

**断网门是 socket 级的**。`--record-mode=none` 管 vcrpy 的应答策略，
`--block-network` 则直接替换 socket 连接函数：任何出网尝试抛
`RuntimeError: Network is disabled`。

两把锁一起上，防偷跑不依赖「拦截器恰好覆盖了这个客户端库」——本实验
实测 vcrpy 8.3 + httpx 0.28 下未匹配请求存在穿透路径，断网门是兜底
的那把锁。

**none 模式的语义是「只读磁带」**。没有录制的用例在它面前活不下去：
这正是验收④要的——回放套件里混进一个没录过的新用例，门禁立刻红，
而不是静默打到真实网络把测试「跑绿」。

## Pitfalls & Q&A

踩坑清单：

- **系统级代理让「断网」漏网**。现象：新用例拿到 502 而不是连接错误——
  httpx 经 urllib 的 getproxies 拾取 macOS 系统级代理（`env` 里看不到），
  死端口的请求被代理接住。解法：测试客户端一律 `trust_env=False`
  （本实验代码如此），再叠加 `--block-network` 在 socket 层兜底。
- **vcrpy 对 httpx 的未匹配请求可能穿透**。现象：none 模式下无录制请求
  没抛 `CannotOverwriteExistingCassetteException` 而是流向真实传输层
  （版本组合相关）。解法：`--block-network` 作 socket 级兜底；穿透与
  否都不影响「零真实网络」。
- **cassette 按测试模块分子目录**。现象：找
  `cassettes/<用例名>.yaml` 落空。原因：pytest-recording 落盘在
  `cassettes/<模块>/<用例>.yaml`。解法：路径带上模块层。

深入问答：

- **Q：cassette 进 git 会不会腐化？**
  会，和 05 的 simulation（Hoverfly 录下的「请求-响应对」集合文件）同源同解：`--record-mode=all`（或 rewrite）
  定期重录，diff 评审变化；`recorded_at` 类元数据帮你判断磁带多旧。
  关键依赖保留真实联调抽查，磁带是降级方案不是终身方案。
- **Q：为什么选 vcrpy 而不是 respx？**
  respx 是纯 stub 库：每条匹配规则手写，没有「录制真实交互」的能力——
  它是 labs/04 手工替身在 httpx 世界的延伸。要「录一次、回放 N 次」
  必须是 vcrpy 这类录像机。
- **Q：与 05 的 Hoverfly 怎么分工？**
  生命周期决定形态：用例级、pytest 套件内 → 进程内（本篇）；跨团队、
  跨语言、要长期在线 → 独立服务（05）。磁带思想同源，部署形态是分水岭。
