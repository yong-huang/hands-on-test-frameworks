# 15 · 契约测试（Pact）：前端与 API 的握手协议，不用 Broker 也能闭环

> 集成测试证明"现在能跑"，但前端和 API 各自发版后还能跑吗？契约测试把
> "前端期望 API 长什么样"固化成 pact 文件：consumer 端定义期望并生成契约，
> provider 端拿契约回放验证真服务——字段一改，verify 当场红。
> 读完本篇你能走通"生成契约 → 校验绿 → 破坏红 → 修复绿"四幕闭环，
> 全程本地文件交换，不碰付费 Broker。

## Background

前后端各自发版时，最怕的是接口字段悄悄对不上：前端期望 `customer`，
后端改成了 `customerName`，两边的集成测试各自都绿——因为各自都"正常"，
只是对不上。等联调或线上炸出来，代价已经翻了几倍。

现有手段各有盲区：集成测试又慢又脆（两边要一起起、一起跑），而且测的是
"此刻凑巧一致"；各自维护的 mock 又各自为政（前端 mock 的响应和后端真实现
没有任何机制保证一致）。缺的是一份**双方共同签收的字据**。

契约测试（consumer-driven contract testing）就是这份字据：消费者（consumer，
接口的使用方）声明自己期望的请求与响应，生成契约文件；提供者（provider，
接口的实现方）拿契约逐条回放验证真服务。字据不一致，谁发版谁被拦。

## What

Pact 是契约测试的事实标准实现。一份契约（pact 文件）= 若干交互，
每个交互 = 请求期望 + 响应期望 + 匹配规则。匹配器（`like`/`each_like`/`integer`）
**只锁类型不锁值**——契约测的是结构，不是具体数据。

可以把契约测试想成租房合同：租客（consumer）把"要什么样的房子"写成条款
（几居室、带独卫——但不规定墙漆编号），房东（provider）每次翻新房子
（发版）都要拿合同逐条验收。但和租房合同不同的是，验收是自动化的：
provider 的 verify 脚本把合同里每个请求真的发给真服务，一条不满足就非 0 退出。

本实验的闭环：consumer 测试在 **mock server** 上跑真实的客户端代码
（`frontend_client.py`），通过后写出 `pacts/*.json` → 文件交换（git 提交
代替付费 Broker）→ provider 拿契约回放验证真 SUT。

## When to Use

典型场景：

- 前后端独立部署的团队：改字段必须先过契约，verify 就是部署安全带。
- 多消费者共享一个服务：每个 consumer 的期望独立成契约，provider 一并验证。
- 微服务间接口回归：provider CI（持续集成，提交后自动跑检查的服务）拉取全部最新契约验证，不用拉起所有消费者。

何时不用：内部纯私有接口、消费者和提供者永远同步发版（monorepo 同仓）时，
类型/schema 校验（lab 12 的 pydantic 锁）通常够用；契约会成为额外维护面。

同类方式对比：

| 方式 | 差异 | 什么时候选它 |
|:---|:---|:---|
| 集成测试 | 两边一起跑，慢而全 | 关键路径端到端 |
| schema 校验 | 单边锁结构，测不到期望 | 简单消费关系 |
| Pact 契约测试 | 两边立字据，快而准 | 独立发版的团队 |

## Quick Start

前置条件：labs/00 体检通过（pact-python 已装）；注意系统代理会干扰 mock server
（见 Pitfalls）。

```bash
cd labs/15_pact
./pact_lab.sh            # 生成契约 → provider 校验绿 → 破坏变红 → 修复回绿
cat pacts/*.json         # 契约长什么样：交互 = 请求期望 + 响应期望 + 匹配规则
```

provider 校验通过的真实输出（2026-09-28 实测，节选；ANSI 着色已剥离）：

```
Verifying a pact between ministore-frontend and ministore-api

  a request for orders (0s loading, 95ms verification)
    returns a response which
      has status code 200 (OK)
      includes headers
        "Content-Type" with value "application/json" (OK)
      has a matching body (OK)

  a request to create an order (0s loading, 82ms verification)
    returns a response which
      has status code 201 (OK)
      includes headers
        "Content-Type" with value "application/json" (OK)
      has a matching body (OK)

RESULT: PASS ✅ 契约满足
>>> 退出码 = 0
```

破坏演练——consumer 期望 `customerName`、provider 返回 `customer` 后再校验
（observe ③，节选；**预期失败演示**）：

```
There were 1 pact failures

RESULT: FAIL ❌ 契约破坏
>>> 退出码 = 1（非 0：契约破坏被拦下，provider 不能随意改字段）
```

诚实预期：四幕应为 绿→红→绿。第③幕的 FAIL 是脚本故意制造的破坏演示
（`PACT_BREAK=1` 改期望字段重新生成契约），不是环境问题；
`./pact_lab.sh` 跑完会自动修复回绿并清理。`pacts/` 目录保留——契约是应提交的资产。

关键代码（这段在做什么：consumer 声明交互、provider 回放验证的四个关键调用）：

```python
Pact("ministore-frontend", "ministore-api")   # consumer / provider
.with_query_parameters({"limit": like("10")}) # query 是字符串
p.write_file(PACT_DIR)                        # 默认 merge，不是覆盖
Verifier("ministore-api").add_source(f).add_transport(url=...).verify()
```

## How It Works

**consumer 端：期望即契约**。

`upon_receiving / with_request / will_respond_with`声明交互，Pact 起一个 mock server 按期望响应——真实的 `frontend_client.py`代码对它发请求，客户端代码不改动。

跑通后 `write_file` 把交互写进契约。匹配器只锁类型不锁值：`like("10")` 表示"这里是字符串就行"，具体值无所谓。


**provider 端：拿字据对账**。`verify_provider.py` 把契约里每个请求重放给真 SUT，逐条比对状态码、头、体是否满足匹配规则。

退出码语义即 CI 门禁：0 满足，非 0 破坏——你在上面两段输出里看到的 `RESULT: PASS` 与`退出码 = 0` / `退出码 = 1` 就是全部机制。


**provider 状态**：契约要求 `items` 至少 1 条（`each_like min=1`）——空库的provider 必红。

脚本在验证前 POST 一条种子订单（`seed_sut`）：provider 有义务准备契约前提的状态，正规做法是 state handler（状态回调），本实验用种子数据演示最小闭环。


**破坏为什么集成测试测不出**：`customerName` vs `customer` 两边各自结构都
"正常"，集成测试只要这次联调恰好对齐过就绿；契约把期望固化成文件，
任何一侧偏离字据，下一次 verify 立即红——**对不上的成本被提前到发版前**。

## Pitfalls & Q&A

踩坑清单（本实验真实踩过）：

- **系统代理吃掉 mock server 的请求**。现象：客户端请求经代理回环返回 502。
  解法：客户端加 `trust_env=False` 直连。契约测试失败先查代理！
- **query 参数当数字写**。现象：匹配结果 missing。原因：query 参数是字符串，
  要 `like("10")` 而非 `like(10)`。
- **多份交互互相覆盖**。现象：契约文件只剩最后一个交互。
  原因：`write_file` 默认 merge，但 `overwrite=True` 会互相覆盖。
  解法：同一对 consumer/provider 的交互合并写入同一契约文件。
- **provider 状态没准备**。现象：verify 因数据前提不满足而红。
  解法：验证前 seed，或实现 state handler。

深入问答：

- **Q：契约测试和集成测试怎么分工？** 集成测试验证"两边一起干活"，慢而全；
  契约测试验证"接口预期一致"，快而准，可各自 CI 独立跑。
- **Q：没有 Broker 怎么落地？** pact 文件进 git、随 MR 评审；provider CI 拉取
  最新契约验证——本实验就是这个闭环的本地版。
- **Q：匹配器的意义？** 把"必须一致"（结构、类型）与"无所谓"（具体值）分开，
  让契约稳定又严格。
