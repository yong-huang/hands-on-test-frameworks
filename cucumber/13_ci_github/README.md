# 13 · CI 集成：BDD 套件进流水线

> BDD 套件的 CI 化比普通 E2E 更轻——API 冒烟集不依赖浏览器，容器内即可执行。
> 本实验交付一份带 ACT 守卫的 GHA workflow（bdd.yml），并用 act 在容器里
> 真实执行；宿主机直跑的 3 条 API 冒烟作为快速反馈层。

## Background

BDD 套件不进 CI 就只是本地脚本。进 CI 的三个标准诉求：push 即跑、
结果以标准格式归档（JUnit）、失败产物可下载。这些诉求在 workflow 文件里
声明一次，push 后自动生效。

act（本地跑 GHA workflow 的容器工具）把"push 后才知道对不对"提前到
"push 前就验证"——lab 18 已踩平的三个开关（--bind/--pull=false/代理）
在本实验直接复用。

## What

bdd.yml 定义一个 bdd job：起 pw-store 靶场 → 跑 BDD 冒烟集（3 条 API
场景）→ 归档 cucumber.json。ACT 守卫三件（checkout/npm ci/upload-artifact）
在本地模式跳过——复用挂载的仓库与 node_modules。

可以把 workflow 想成菜谱与灶台的关系：GHA 是标准灶台（每次 push 自动开火），
act 是自家同款灶台（手动开火试菜）。菜谱只有一份，
两个灶台都能验证——但自家灶台缺的设备（checkout、artifact 上传）
要靠守卫标注"试做时跳过"。

![BDD 套件进 CI：act 本地校验与 GHA 执行位](images/ci.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/cucumber/13_ci_github/images/ci.html)
> （或本地打开 [`images/ci.html`](images/ci.html)）。
> 两条执行位共享同一份 bdd.yml；ACT 守卫标注本地模式的差异步骤。

## When to Use

| 场景 | act 校验 | push 看 CI |
|:---|:---|:---|
| workflow 语法/依赖/路径错误 | ✅ 分钟级暴露 | 十分钟循环 |
| 真实 GHA runner 行为 | ⚠️ 容器有差异 | ✅ |
| BDD 冒烟集是否全绿 | ✅ 同一套件 | ✅ |

判断口径：与 lab 18 相同——**act 管"装配对不对"，CI 管"跑得快不快"**。
BDD 套件无浏览器依赖（API 层），是所有套件里最容易容器化的一支。

## Quick Start

```bash
cd cucumber/13_ci_github
./ci_github.sh          # apply 体检 → observe act 校验 + 宿主机冒烟 → clean
```

observe ① act 在容器内执行 workflow（需要代理与本地镜像，踩坑链见
playwright/18）：

```
=====> [observe] ① act 容器内校验 workflow
>>> act 校验输出（Job succeeded / 具体报错见日志）
```

observe ② 宿主机直跑 BDD 冒烟集（3 条 API 场景，SUT 起在 9115）：

```
2 hooks (2 passed)
3 scenarios (3 passed)
9 steps (9 passed)
```

验收方式：宿主机冒烟 3 条全绿；act 单 job 容器内执行成功
（需要代理，本环境实测通过一条完整流水线）。cucumber.json 产物生成。

## How It Works

**API 冒烟集是 CI 的最优载体。** BDD 场景若走 UI（Playwright page），
容器里需要装浏览器——而 BDD 的 API 层场景（健康探活/创建闭环/种子完整）
用 fetch 直打，零浏览器依赖。这套"API 冒烟集"就是 CI 上最快的 BDD 形态：
3 条场景 0.3 秒。

**workflow 内托管 SUT。** 与本地脚本的 apply 相同：nohup 起服务、
探活循环等待。

CI 容器里没有 nohup 环境差异——bash 步骤内启动即可，
job 结束容器销毁，服务自然消失（无需 clean）。

**cucumber.json 是 BDD 的 CI 产物。** 与 lab 09 的 json formatter 相同，
CI 归档后可离线重放失败详情。upload-artifact 步骤在 ACT 模式跳过
（无网络），GHA 上自动归档。

**ACT 守卫的边界在本实验扩展了一处。** 除 lab 18 的三件
（checkout/npm ci/artifact）外，本实验的 SUT 构建步骤在 ACT 模式
也不需要——bind 挂载下构建产物已存在（playwright/02 已产出）。

守卫集合随仓库形态演化——每次加步骤都要问"act 环境里这步是否必要"。

## Pitfalls & Q&A

**Q：为什么 BDD 冒烟集只有 3 条场景？**
CI 冒烟集的定位是"最快的反馈"：健康、创建闭环、种子完整——
三条覆盖 SUT 生存能力的最小集。全量 BDD 回归（活文档套件）
放在夜间或发布前的工作流，与 playwright/ 系列的分层策略一致。

**Q：act 校验时报 "Requested profile doesn't exist"？**
lab 08 的 ESM 坑在 CI 配置里同样存在：默认导出函数返回 profiles 表。
本实验的 cucumber.mjs 已按正确形态写（返回函数），CI 与本地共用。

**Q：cucumber.json 里的敏感信息怎么处理？**
BDD 冒烟集的场景不传敏感参数（健康探活、匿名创建）。
若套件含登录场景，密码应来自环境变量（profile env 注入），
json 报告里参数值会原样记录——注入来源不进报告。

**Q：act 跑 workflow 时 SUT 起不来？**
容器内 nohup 起的服务在本 job 内存活（job 结束容器销毁）。
若探活循环超时，先在 workflow 里加 curl -v 排查网络，
再确认 server.mjs 的端口与探活 URL 一致（本实验 9115）。

**Q：BDD 套件能和其他套件（playwright/ 系列）共用一个 workflow 吗？**
可以——matrix strategy 按 suite 维度展开，每腿独立装依赖与跑批。

本实验保持独立 workflow 是为了演示清晰；仓库化时合并能省一次环境装配。
