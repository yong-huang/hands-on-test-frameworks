# 17 · CI 里的 mock 生命周期：健康门、零残留、缓存判定

> CI 里 mock 服务最常见的三种病：没等健康就跑测试（偶发红）、挂了不清
> （污染下一个 job）、每次都重启（慢）。本篇用 act（本机跑 GitHub
> Actions 工作流的工具）把 mock 生命周期工作流真实跑 4 轮：健康门放行、
> 三连跑零残留、配置未变 reuse=true 跳过重启、配置变更缓存失效重启。

## Background

mock 服务进了 CI 就成了「共享基础设施的最小形态」：job 要依赖它活着，
它坏了要连累别人，它慢了整个流水线跟着慢。这三件事在本地脚本里都好
办（顺序执行、跑完就杀、写死启动），进了 CI 就变成工程问题：健康
检查做成门、清场放进 always 步骤、重启做成缓存判定。

本地 act（把 GitHub Actions 工作流跑在本机 Docker 里的工具）给了
「在提交前就把这套生命周期跑真」的能力——工作流文件、步骤语义、失败
行为与 CI 完全一致。

## What

mock 生命周期工作流是四个步骤的门禁链，每步可断言：

| 步骤 | 机制 | 实测表现 |
|:---|:---|:---|
| 缓存判定 | stubs 目录哈希存入跨运行保留的缓存 | 首跑 reuse=false，未变 reuse=true |
| 启动 mock（健康门） | 后台拉起 + 轮询健康端点，通过才放行 | 健康检查不过则 job 红 |
| 消费方冒烟 | 打 mock 的真实业务断言 | TXN-PERF 命中 |
| 零残留清场（always） | 杀进程 + socket 探测残留 | 三连跑零残留 |

可以把工作流想成 mock 的**上岗流程**：健康门是体检（不过不发工牌）、
冒烟是试岗（真活儿干一件）、always 清场是下班打卡（失败也要打卡）。
但和打卡机不同的是：缓存判定让「明天上岗」可以免体检——配置没变，
昨天的体检单还有效。

![缓存判定→健康门→冒烟→always 清场，四步生命周期链](images/lifecycle.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/mocking/17_ci_lifecycle/images/lifecycle.html)
> （或本地打开 [`images/lifecycle.html`](images/lifecycle.html)）。

图里 reuse=true 的分支跳过启动与冒烟——fresh 容器里没有长效 mock，
跳过即诚实（见 Q&A）。

## When to Use

典型场景：

- 替身服务进 CI 的标准姿势：健康门 + always 清场 + 缓存判定三件套。
- 流水线提速：mock 配置未变的 job 跳过重启（实测第 2、3 次全跳）。
- 「测试污染了环境」的排查基线：always 清场 + socket 探测让残留
  无处遁形。

何时不用：mock 是用完即弃的进程内替身（06）→ 无生命周期可管；CI
只有单一 job 且 mock 随 job 天然起停 → 现有步骤已足够。

| 方案 | 差异 | 什么时候选它 |
|:---|:---|:---|
| 脚本内 ad-hoc 起停 | 无门禁、易残留 | 本地一次性验证 |
| 生命周期工作流（本篇） | 门禁/清场/缓存步骤化 | CI 里的长效 mock 服务 |
| 外部常驻环境 | 环境永在但共享互扰 | 团队级联调（配漂移巡检） |

## Quick Start

前置条件：act（brew install act，本机 0.2.89 ✅）与 Docker daemon 在跑
（OrbStack 的 socket 脚本自动探测）；本目录含工作流、stub 与
mock_downstream.py（复用 16）。

```bash
cd mocking/17_ci_lifecycle && ./ci_lifecycle.sh all
```

实测输出（节选）：

```
② 第 1 次：缓存 miss → 启动 mock（健康门放行）→ 冒烟 → 零残留
reuse 判定：reuse=false
  ✅ 首跑 cache miss，mock 已启动

③ 第 2、3 次：配置未变 → reuse=true，跳过启动与冒烟
  ✅ 第 2、3 次缓存命中：mock 启动与冒烟全部 Skipped，零残留保持

④ 反向验证：改 mock 配置 → 缓存失效 → 重新启动
reuse 判定：reuse=false
  ✅ 配置变更后缓存失效，mock 重启

>>> 验收：健康门放行 ✅ 零残留 ✅×3 缓存命中 ✅ 配置变更失效 ✅
```

诚实预期：reuse=true 的运行会跳过「启动 mock」与「冒烟」两步（act
日志里标 Skipped）——act 每次 job 都是新容器，没有长效 mock 可复用，
跳过即诚实；这意味着缓存在本篇省的是「启动动作」，真正的长效复用
要配外部常驻环境（When to Use 表第三行）。

## How It Works

**健康门是顺序执行的放行条件**。mock 后台拉起后，curl 轮询健康端点
最多 20 次，任一次成功即放行——健康检查不过，job 在冒烟前就红，
错误不会伪装成业务失败。

**缓存判定是对配置文件的哈希对账**。stubs 目录哈希存进跨运行保留的
缓存文件，未变即 reuse：

```bash
HASH=$(find stubs -type f -exec md5sum {} \; | md5sum | cut -d' ' -f1)
if [ -f .mock-cache/mock_hash ] && [ "$(cat .mock-cache/mock_hash)" = "$HASH" ]; then
    echo "reuse=true" >> "$GITHUB_OUTPUT"
```

缓存文件在工作目录的 .mock-cache/ 下——act 以 --bind 方式挂载工作
目录，跨运行天然持久，无需额外卷。

**零残留是 socket 级断言**。pkill 后用 Python 探测 9810 端口连接
结果，非零（无人监听）才打印确认——「清了」必须被探测证实，不是
打印一句口号。

## Pitfalls & Q&A

踩坑清单：

- **act 的 `-v` 是 verbose 不是 volume**。现象：`-v host:ctr` 被当成
  事件参数，报 Could not find any stages。原因：act 的卷挂载要用
  `--bind`（绑定工作目录）；任意路径挂载不在 GH 语法里。解法：缓存
  文件放工作目录内（.mock-cache/），`--bind` 天然持久。
- **ubuntu 基础镜像没有 python3**。现象：步骤报 python3: command not
  found。原因：runs-on 镜像（ubuntu:24.04）是极简 ubuntu。解法：前置
  步骤 apt-get install curl python3。
- **失败的 job 会驻留容器**。现象：`docker ps` 里 act 容器 Up。
  原因：job 失败时 act 不自动删容器。解法：清场步骤里
  `docker rm -f` 断言前先清（本篇 ⑤ 步）。

深入问答：

- **Q：reuse=true 跳过了冒烟，那测试不就没跑？**
  是的——这正是本篇要暴露的语义：fresh 容器里「跳过重启」等于
  「没有 mock」，冒烟必须跟着跳过。真要既复用又测试，需要外部常驻
  mock 环境（job 打常驻地址），那时缓存判定管理的就是「环境是否
  需要重建」，语义同样成立。
- **Q：健康门轮询失败几次算门禁失败？**
  本篇 20 次 × 0.5s = 10 秒上限。门禁的价值是「快速失败而非慢速
  偶发成功」：mock 起不来大概率是配置坏了，重试救不了坏配置。
- **Q：这套能搬到真 GitHub Actions 吗？**
  工作流原样可搬（act 就是按 GH 语法跑的）；差异只在 runner：真
  Actions 的 ubuntu runner 自带 python3 与完整工具链，连 apt-get
  那步都可省。
