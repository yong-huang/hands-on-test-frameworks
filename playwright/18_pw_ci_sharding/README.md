# 18 · 本地 CI 与 sharding：act 校验流水线，分片拆解套件

> 套件大到单机跑不完时，答案是把用例切成 N 份发给 N 台机器。本实验交付两件东西：
> 一份真实的 GitHub Actions 分片 workflow（4 shard 矩阵），以及 act 本地校验闭环
> （在 Docker 里真实执行一条分片腿）。另附宿主机 --shard 对照数据与并行三坑。

## Background

CI 上跑 E2E 与本地有一个本质差异：环境是"装配"出来的——checkout、装依赖、
装浏览器、跑批、归档产物，每一步都可能只在你机器上成立。workflow 文件
（GitHub Actions 的流水线声明）里写的就是这套装配过程，但它是否真的可执行，
要等 push 之后才知道——反馈周期以十分钟计。

act 把这套装配搬进本地 Docker：同一个 workflow 文件、同样的 action 语法，
在容器里逐 step 执行，装配错误（路径错、依赖缺）在 push 前暴露。

sharding（分片，把用例集按 `--shard=x/N` 切成 N 份）则解决"跑得慢"：
每份发一个 CI runner 并行执行，总时长理论上除以 N。

## What

本实验的 workflow 用 matrix strategy 声明 4 个分片 job：装依赖、装浏览器、
跑 `--shard=${{ matrix.shard }}/4`、归档各自的 JUnit 报告。

本地校验时 act 只跑一条腿（`--matrix '{"shard":"1"}'`），验证流水线语义。

可以把 workflow 想成菜谱：CI 厨房按菜谱开 4 个灶台同时炒 4 锅，
act 是自家厨房按同一份菜谱试做一锅——味道对了再交给 CI 批量。

但和菜谱不同，act 的厨房与 CI 厨房有设备差异（无 checkout、网络受限），
需要用 ACT 环境守卫标注"本地试做时跳过的步骤"。

![分片流水线：一份配置，act 与 GHA 两种执行位](images/sharding.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/playwright/18_pw_ci_sharding/images/sharding.html)
> （或本地打开 [`images/sharding.html`](images/sharding.html)）。
> 虚线是本地校验路径：act 只跑一条分片腿，语义验证通过即代表 CI 全矩阵可执行。

## When to Use

| 场景 | act 本地校验 | 直接 push 看 CI |
|:---|:---|:---|
| workflow 语法/路径/依赖问题 | ✅ 分钟级暴露 | 十分钟级反馈循环 |
| 需要真实 GitHub runner 行为 | ⚠️ 容器有差异 | ✅ 唯一正解 |
| 调试分片分配与产物归档 | ✅ 单腿即可验证 | 全矩阵跑一轮 |
| 依赖 GitHub 特有 API（environments 等） | ❌ | ✅ |

判断口径：**act 管"装配对不对"，CI 管"跑得快不快"**。
本机验证过的 workflow push 上去，首次通过率显著提高。

## Quick Start

```bash
cd playwright/18_pw_ci_sharding
./ci_shard.sh          # apply 体检 → observe act 校验 + 宿主机分片对照 → clean
```

observe ① 用 act 在容器里真实执行 shard 1 的流水线（checkout/npm ci 按 ACT 守卫跳过，
bind 挂载复用本地 node_modules，浏览器经代理装进容器）。此前一次完整运行的产物：

```
[e2e-sharded/e2e-3] ⭐ Run Main 运行分片 3/4
[e2e-sharded/e2e-3]   |  ✓ 10 [chromium] › 分片池 25: 创建 + 回读一致
[e2e-sharded/e2e-3]   |  10 passed (2.3s)
[e2e-sharded/e2e-3] 🏁  Job succeeded
```

observe ② 是宿主机的分片对照——预起共享 SUT 后，4 个分片错峰并行：

```
shard 1: 10 passed
shard 2: 10 passed
shard 3: 10 passed
shard 4: 10 passed
```

验收方式：4 分片 × 10 条全绿（40 条无遗漏无重复）；act 单腿 Job succeeded。
轻量套件（40 条 API 用例，总计 <1s）的分片收益会被启动开销吃掉——
这正是分片的适用边界，见 How It Works 与实测记录。

## How It Works

**ACT 环境守卫让一份 workflow 服务两个执行位。** act 无法执行的三类步骤——
checkout（仓库已挂载）、npm ci（挂载的 node_modules 复用）、
upload-artifact（本地无 GitHub API）——统一加 ACT 守卫跳过。

`act --env ACT=true` 打开守卫开关。这份 workflow 因此可以同时被 GHA 与 act
消费，而不需要维护两个版本。

**act 本地校验的三个关键开关（实测踩坑集合）。** 一是 `--bind`：
让容器路径与宿主一致，否则 working-directory 指向的宿主路径在容器里不存在。

二是 `--pull=false`：本机已有镜像时跳过 pull（本环境镜像源实测 Bad Gateway）。
三是代理变量要同时传给 act 进程与容器内步骤（`--env HTTPS_PROXY`），
容器内装浏览器走的是容器自己的网络。

**sharding 的价值边界要用数据理解。** 本实验的轻量套件（40 条 API 用例，
总计 <1s）分片对照：串行 770ms vs 4 分片并行 740ms——收益几乎为零，
每条分片的启动成本（进程、浏览器、webServer 探活）与执行成本同量级。

分片的真实主场是分钟级套件 × 真实多机：总时长 = 最慢单片 + 装配开销，
套件越大、加速比越接近 N。

**共享 SUT 是本地分片的隐藏约束。** 4 个分片同时起跑时各自触发 webServer
装配，端口争用会让部分分片误判"服务起不来"（实测踩坑）。

两个解法：脚本预起服务（分片全部复用，本实验采用），
以及分片错峰启动（间隔 1.5 秒，避开探活窗口重叠）。
CI 上每个 runner 独立起服务，天然没有这个问题。

## Pitfalls & Q&A

**Q：act 为什么弹"choose the default image"交互？**
act 首次运行没有镜像配置时弹交互菜单。

本系列用 `-P ubuntu-latest=catthehacker/ubuntu:act-latest` 写入 actrc 指定——
该镜像 lab 30 已拉取（2.25GB），配合 `--pull=false` 走本地缓存，
不依赖镜像源（本环境镜像源实测 Bad Gateway）。

**Q：--container-architecture linux/amd64 为什么是坑？**
Apple Silicon 上本地拉到的镜像是 arm64 变体；强制 amd64 会让 Docker 放弃
本地镜像去拉 amd64 版本——正好撞上坏掉的镜像源。

删掉该参数用本机架构，本地镜像直接命中。
报错信息（"image found but platform does not match"）就是诊断线索。

**Q：分片后某些用例会重复跑或漏跑吗？**
不会。Playwright 按"用例总数 ÷ N"均分（本实验 40 条 → 每片 10 条），
分配基于用例列表的确定性排序，同一份代码多次分片结果一致。

新增用例会导致重新洗牌——依赖"某用例固定在某片"的假设不成立。

**Q：JUnit 报告为什么按分片分文件？**
4 个 runner 各自生成 `junit-shard-N.xml`，CI 平台按文件聚合（lab 12 的
产物体系在这里接入）。合并成单文件需要额外步骤且会有文件锁问题，
分文件归档是官方推荐形态。

**Q：轻量套件分片收益为零，那 lab 里为什么还做分片对照？**
因为这个"零收益"本身就是最有价值的实测结论：分片是规模化工具，
不是速度开关。

本实验用数据划出了它的适用边界（套件时长 >> 启动开销），
并完整走通了从 workflow 到分片执行的链路——套件长大后这条链路直接可用，
不需要重写任何东西。
