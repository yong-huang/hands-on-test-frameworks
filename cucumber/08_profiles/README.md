# 08 · Profiles 多环境：一份用例 × N 份配置

> dev 与 staging 只差一个 SUT 地址和一组账号——这份差异应该活在配置里，
> 而不是散落在用例的字面量里。本实验用 cucumber 的 profiles 机制
> （`--profile dev` / `--profile staging`）让同一套用例零改动跑两个环境，
> 并顺带演示双浏览器核矩阵。

## Background

用例里写死 `http://127.0.0.1:9108` 的时刻，就是它只能在开发机运行的时刻。
环境切换的需求天生长在配置里：本地一套端口、预发一套域名、CI 又一套，
凭据也各不相同。

cucumber 的 profiles 机制：配置文件里声明多个命名配置段，
`--profile 名字` 选择本次生效的段，段内的 `env` 键向进程注入环境变量。
World 与步骤只消费环境变量——环境怎么来的，用例一概不知。

## What

本实验的 cucumber.mjs 导出一个函数（ESM 的正确形态），返回三个 profile：
default（兜底）、dev（9108）、staging（9109）。每个 profile 声明步骤加载
路径与 `env` 注入项；World 顶层的 `process.env.BASE_URL` 等常量消费它们。

可以把 profiles 想成游戏存档槽：同一份游戏代码（用例）读不同的存档，
进度各玩各的。

但和存档不同，profile 的切换发生在进程启动时——一次运行只用一个
profile，中途不切。

![profiles 多环境：一份用例与多份环境配置](images/profiles.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/cucumber/08_profiles/images/profiles.html)
> （或本地打开 [`images/profiles.html`](images/profiles.html)）。
> 虚线是 profile 的 env 注入路径：配置向 World 供值，World 只管消费。

## When to Use

| 场景 | profiles | 环境变量硬编码 |
|:---|:---|:---|
| 同套件跑多环境（dev/staging） | ✅ --profile 一键切换 | 复制整套用例 |
| CI 与本地差异化（headless 等） | ✅ CI profile | 脚本里 if/else |
| 单一环境的小项目 | ✅ 只有 default 也算 profile | 也能活 |

判断口径：**差异只有"值"时用 profile，差异是"行为"时用标签或独立套件**。
profile 能注入环境变量与 cucumber 配置项，不能改变步骤逻辑。

## Quick Start

```bash
cd cucumber/08_profiles
./profiles.sh          # apply 起双环境 → observe 双 profile + 双浏览器 → clean
```

observe ①②③ 分别是 dev profile、staging profile 与双浏览器核运行，
同一套 env.feature 在三种组合下全绿：

```
=====> [observe] ① --profile dev
2 scenarios (2 passed)
10 steps (10 passed)
=====> [observe] ② BASE_URL 覆盖演示：staging profile 指向 9109
2 scenarios (2 passed)
```

验收方式：dev 与 staging 两 profile 全绿（各打各的 SUT 实例），
`--name "双浏览器"` 过滤的双核场景也全绿。

变异实验：把 staging 的 BASE_URL 改成 9999 端口重跑——连接拒绝，
证明 profile 的 env 注入真实生效。

## How It Works

**ESM 配置的正确形态是默认导出函数。** cucumber 加载 .mjs 配置时拿到
的是模块命名空间；若默认导出是静态对象，cucumber 只把命名空间的
default 属性当 profiles 表——dev/staging 全部失效（实测踩坑）。

默认导出一个返回 profiles 表的函数，cucumber 调用它取表——
这是 ESM 形态的官方解法。

**default 键是必填的底座。** `--profile dev` 的语义是"把 dev 段 merge 到
default 段之上"——没有 default 键时 dev 段也加载不出来（实测踩坑）。

通用键放 default，环境差异放各命名段。

**env 注入的边界是进程环境变量。** profile 的 env 键只影响本次运行的
process.env，`process.env.BASE_URL ?? 默认值` 是消费点。

用例与步骤不直接读 profile 对象——配置到消费只隔一层环境变量。
来源可替换：真实 CI 注入而非配置文件。

## Pitfalls & Q&A

**Q：为什么我的 --profile 报 "doesn't exist"，明明配置里写着？**
两个叠加的坑（实测都踩了）：一是 .mjs 静态导出对象被模块命名空间包裹，
cucumber 读到的顶层只有 default——解法是默认导出函数。

二是 default 键缺失时其他 profile 无法被请求。
修完的形态见本实验 cucumber.mjs：默认导出函数 + 必含 default 键。

**Q：profile 之间能继承吗？**
可以组合表达：让 staging 段显式写全（与 dev 平行），或用
default 函数返回前先展开公共段（`{ common, dev: { ...common, overrides } }`）。
显式写全的冗余换来"每段独立可读"，小配置建议显式。

**Q：--name "双浏览器" 是在过滤什么？**
`--name` 按标题子串过滤场景（本实验场景标题含"双浏览器核"）。
与 --tags 是两种正交的圈选方式：tags 是显式标记，name 是标题匹配。
组合使用（--tags + --name）取交集。

**Q：双环境同时起服务，端口冲突怎么办？**
两个 profile 指向两个端口（9108/9109），各起各的实例——本实验的
`profiles_env.sh` 就是双环境启停器。若两环境共用一个端口，
profile 切换前必须先停旧实例，否则 env 注入的 URL 指向的是"上一个环境"。

**Q：真实项目的 staging 是远程域名，本实验为什么用本地双端口？**
机制完全一致：profile 的 env 换成 `BASE_URL=https://staging.example.com`
即可。本地双端口的价值是"零网络依赖也能演示机制"。

但要注意 staging 环境的数据状态不受本实验控制
（reset 只作用于本地实例），真实 staging 需要专用测试账号与清场策略。
