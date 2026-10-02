# 14 · 🏁 终极 BDD 套件：三个业务域、一条命令、活文档交付

> 前 13 个实验的积木在此组装：认证/订单/上传三个业务域的 .feature 集
> （7 场景 36 步）、统一 World（双角色会话 + reset 隔离）、活文档报告，
> 以及质量门禁（failed=0 才放行）。一条命令 `./run_suite.sh all` 全绿收官。

## Background

系列推进到此处，每个实验都验证过一块积木——但"整套 BDD 资产是否协同工作"
需要一次全量串联回答：三个业务域的 feature 混跑时，World 隔离、页面对象、
报告管线是否互不干扰？

串联的价值在首跑就兑现：本次开发中串联暴露了两个真实缺陷——
中文文件名被服务端净化成下划线（上传断言假绿）、logout 后 addInitScript
重新注入 token 导致"退出即复活"。修复后 7 场景全绿，门禁通过。

## What

终极套件的组织：`features/` 按业务域分文件（auth/orders/uploads），
共享一个 FinalWorld（双角色 setRole + reset 隔离 + 登录态注入），
`run_suite.sh` 串起"起靶场 → 全量跑批 → 活文档 → 门禁"四步。

可以把这个套件想成系列的"总装车间"：各实验生产的零件（World、页面对象、
步骤库、报告管线）在这里装成整车，门禁是出厂检验。但和总装不同，
BDD 套件的"零件"在总装时还会暴露零件间的兼容性问题——这正是串联不可省的原因。

![终极 BDD 套件：业务域分文件、统一 World、门禁](images/finalbdd.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/cucumber/14_final_suite/images/finalbdd.html)
> （或本地打开 [`images/finalbdd.html`](images/finalbdd.html)）。

## When to Use

| 场景 | run_suite.sh | 单实验脚本 |
|:---|:---|:---|
| 共享靶场（pw-store）改动后 | ✅ 全量回归 | 漏远处业务域 |
| 新 BDD 特性入库前 | ✅ 门禁把关 | 只验新特性 |
| 开发单个实验 | ❌ 过重 | ✅ |

判断口径：与 playwright/19 相同——**改共享物必跑串联**；
本系列的共享物是 pw-store 与 World 基座。

## Quick Start

```bash
cd cucumber/14_final_suite
./run_suite.sh all          # apply → 全量跑批 → 活文档 → 门禁
echo $?                     # 0 = 门禁通过
```

真实输出（本机实测）：

```
=====> [observe] 全量 BDD 回归（3 个业务域 feature）
2 hooks (2 passed)
7 scenarios (7 passed)
36 steps (36 passed)
=====> [gate] 质量门禁
>>> failed=0 pending场景标记=0
✅ 门禁通过：全系列 BDD 回归 GREEN 🏁
```

验收方式：7 场景全绿、门禁 exit 0、`reports/html/index.html` 活文档生成、
`reports/features.md` 功能清单与执行状态一致。变异实验：把 auth.feature
的预期文案改错一个字重跑——门禁返回非零。

## How It Works

**业务域分文件是并行与维护的双保险。** auth/orders/uploads 三个 feature
各自独立成文件——cucumber 的并行按文件分发（lab 10）。

改订单域不碰认证域的评审历史。步骤定义共享一份 shared_steps.ts，
业务动作都收口在 pages/。

**FinalWorld 是系列 World 的收官形态。** 双角色 `setRole`（lab 03）、
reset 隔离（lab 10）、登录态注入（lab 04）三合一。

logout 场景暴露了一个新边界：addInitScript 在 context 生命周期内
**每次导航都注入**——"退出登录"后 reload 会立刻复活登录态。

对策：登录类场景不 reload，直接在登出后的表单上操作。

**门禁从 json 统计而非解析终端输出。** `reports/cucumber.json` 里的
result.status 是权威数据源——Node 内联脚本统计 failed 场景数，0 才放行。

比 grep 终端文本可靠（formatter 输出格式可能随版本变化）。

**串联首跑暴露的两个缺陷都值得记住。** 一是中文文件名：服务端的
文件名净化正则把"终局-附件.txt"变成"__-__.txt"，断言按原名找必然落空——
测试数据用 ASCII 是跨层协议。

二是 logout 与 initScript 的相互作用：注入脚本的生命周期是整个 context，
不是"第一次加载"——会话类测试要理解注入的时机与范围。

## Pitfalls & Q&A

**Q：为什么 auth.feature 的三个场景都要先"点击退出登录"？**
World 为每个场景注入 admin 登录态（多数业务域场景需要它），
登录表单本身只有在未登录态才可见——先登出才能测表单。

这是"World 默认态"与"特定场景需求"冲突时的标准解法：
场景内主动脱离默认态，而不是给 World 加开关。

**Q：上传测试为什么必须用 ASCII 文件名？**
pw-store 服务端对文件名做净化（非单词字符替换为下划线，防路径注入），
中文字符全被替换——测试断言按原名找文件必然落空（实测踩坑）。

生产系统的等价问题是"非 ASCII 文件名的编码约定"——前后端必须一致，
测试把它钉住。

**Q：删除步骤为什么要先等行渲染（toHaveCount(1)）再点击？**
创建订单后 WS 广播触发列表 refetch，"当 删除订单"执行时行可能还在
渲染路上——直接点删除按钮会等不到元素（实测超时）。先断言行存在
（web-first 重试），再点击，是动作顺序的时序纪律。

**Q：门禁为什么只查 failed=0，不管 pending？**
终极套件的场景全部已实现（没有 pending 标注）。若未来加入 pending
场景（lab 12 语义），门禁应扩展为"failed=0 且 pending 有案由"——
阈值跟着套件的成熟度走，不是一刀切。

**Q：这个套件和 playwright/19 的终极串联是什么关系？**
同一靶场（pw-store）的两套回归视角：playwright/19 是命令式 E2E 全景
（163 用例），本套件是 BDD 活文档形态（7 场景 36 步，业务可读）。

两者共享 SUT 与隔离纪律，一个验"系统行为全集"，一个验"业务规则表达"。
