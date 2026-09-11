# 15 · 契约测试（Pact）：前端与 API 的握手协议，不用 Broker 也能闭环

> 集成测试证明"现在能跑"，但前端和 API **各自发版**后还能跑吗？
> 契约测试把"前端期望 API 长什么样"固化成 pact 文件：consumer 端定义期望并
> 生成契约，provider 端拿契约回放验证真服务。字段一改，verify 当场红。
> 本篇全程本地文件交换，不碰付费 Broker。

## 1. 为什么需要它

- 集成测试又慢又脆；mock 测试又各自为政——契约测试在**两边之间立字据**。
- 独立部署的前后端团队靠它实现"改字段必须先过契约"——部署安全带。

## 2. 总览：契约的生成、交换与验证闭环

<!-- 图: images/pact.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/labs/15_pact/images/pact.html)
> （或本地打开 [`images/pact.html`](images/pact.html)）。

consumer 测试在 mock server 上验证交互并写出 `pacts/*.json` → 文件交换
（git 提交代替付费 Broker）→ provider 拿契约回放验证真 SUT → 改字段当场红。

## 3. 快速开始

```bash
./pact_lab.sh            # 生成契约 → provider 校验绿 → 破坏变红 → 修复回绿
cat pacts/*.json         # 契约长什么样：交互 = 请求期望 + 响应期望 + 匹配规则
```

## 4. 核心概念

### 4.1 consumer 端：期望即契约

consumer 测试用 `upon_receiving / with_request / will_respond_with` 声明交互，
在 **mock server** 上跑真实的客户端代码（`frontend_client.py`），通过后把契约
写进 `pacts/`。`like/each_like/integer` 等匹配器**只锁类型不锁值**——契约测
结构，不测数据。

### 4.2 provider 端：拿字据对账

`verify_provider.py` 把 pact 文件里的每个请求重放给**真 SUT**，比对响应是否
满足匹配规则。退出码语义即 CI 门禁：0 满足，非 0 破坏（脚本 ①③④ 实测）。

### 4.3 破坏演练：改字段名必红

observe ② 用 `PACT_BREAK=1` 让 consumer 期望 `customerName`（provider 实际
返回 `customer`）→ 重新生成契约 → provider verify 立即 FAIL。
**集成测试测不出这个**——结构两边都"正常"，只是对不上。

### 4.4 provider 状态

契约要求 `items` 至少 1 条（each_like min=1）——空库的 provider 必红。
脚本在验证前 POST 一条种子订单（`seed_sut`）：**provider 有义务准备契约
前提的状态**，正规做法是 state handler，这里用种子数据演示最小闭环。

### 4.5 易错点（本实验真实踩过）

- **系统代理会吃掉 mock server 的请求**（httpx 走代理回环 → 502）——
  客户端加 `trust_env=False` 直连。契约测试失败先查代理！
- query 参数是字符串：`like("10")` 而非 `like(10)`，类型匹配对不上就是 missing。
- 同一对 consumer/provider 的多份交互要**合并写入**同一契约文件
  （write_file 默认 merge；overwrite=True 会互相覆盖只剩最后一个）。

## 5. 关键字段

```python
Pact("ministore-frontend", "ministore-api")   # consumer / provider
.with_query_parameters({"limit": like("10")}) # query 是字符串
p.write_file(PACT_DIR)                        # 默认 merge，不是覆盖
Verifier("ministore-api").add_source(f).add_transport(url=...).verify()
```

## 6. 文件结构

```
15_pact/
├── README.md
├── pact_lab.sh                    # 生成 → 校验 → 破坏 → 修复 四幕剧
├── configs/pytest.ini
├── consumer/
│   ├── frontend_client.py         # 被测的"前端"客户端（trust_env=False 直连）
│   └── test_pact_consumer.py      # 两个交互的契约定义
├── provider/verify_provider.py    # provider 校验器（退出码即门禁）
├── pacts/                         # 契约资产：应提交进版本库
└── images/
```

## 7. 深入要点

- **Q: 契约测试和集成测试怎么分工？** 集成测试验证"两边一起干活"，慢而全；
  契约测试验证"接口预期一致"，快而准，可各自 CI 独立跑。
- **Q: 没有 Broker 怎么落地？** pact 文件进 git、随 MR 评审；provider CI 拉取
  最新契约验证——本实验就是这个闭环的本地版。
- **Q: 匹配器的意义？** 把"必须一致"（结构、类型）与"无所谓"（具体值）分开，
  让契约稳定又严格。

## 8. 总结

阶段三毕业：SUT 造好、API 套件、数据层夹击、真库容器、契约闭环。
下一篇进入阶段四：[16_pw_basics](../16_pw_basics/README.md)——Playwright 现代名
E2E 的第一课。
