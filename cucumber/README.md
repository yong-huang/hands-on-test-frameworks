# 🥒 cucumber/：Cucumber BDD 14 实验动手系列（TypeScript 栈）

> 把 [docs/cucumber.md](../docs/cucumber.md) 清单落成的可真实跑通系列：
> Gherkin 闭环 → 步骤设计/World → 数据驱动/好坏 Gherkin → hooks/profiles/报告/并行
> → 方法论两连（Example Mapping/活文档）→ CI 集成 → 🏁 终极 BDD 套件。
> 与仓库两条既有系列**互补**：labs/ 的 Python 栈与 playwright/ 的 TS 命令式栈
> 都没有 BDD——本系列补上"业务可读的测试"这一维度。
> 每个实验 = apply/observe/clean 脚本 + 六段式 README + 交互架构图三件套。
> 共享靶场 pw-store（playwright/02），端口约定 91NN。

进度：**14/14 (100%)** ██████████████

## 🚀 快速开始

```bash
bash cucumber/load_resources.sh          # node 依赖（cucumber 13 + playwright 1.62 + tsx）
cd cucumber/01_gherkin_basics && ./gherkin_basics.sh   # 第一个实验：中文 Gherkin 三场景
cd cucumber/14_final_suite && ./run_suite.sh all       # 🏁 全系列回归（7 场景 + 门禁）
```

## 📚 实验总表

| 实验 | 主题 | 一句话产出 | 验收亮点 |
|:---|:---|:---|:---|
| [01](01_gherkin_basics/README.md) | Gherkin 最小闭环 | 中文 Feature 三场景打真浏览器 | 静默失效演示：关键字写错不报错 |
| [02](02_step_design/README.md) | 步骤层设计 | 参数捕获 + 页面对象收口 | grep 门禁：步骤层零定位器 |
| [03](03_world_state/README.md) | ⛓️ World 状态 | 类型安全 World + 隔离 | 探针不泄漏；token/展示同源 |
| [04](04_outline_examples/README.md) | 场景大纲 | 1 骨架 × 4 组例子 | 失败定位到组；方言关键字查表 |
| [05](05_data_table/README.md) | DataTable | rows/hashes 双形态 | When 输入表 + Then 期望表 |
| [06](06_good_gherkin/README.md) | 好坏 Gherkin | 命令式 → 声明式重构 | 语义等价 + UI 操作词门禁 |
| [07](07_hooks_tags/README.md) | Hooks 与标签 | 四钩子时序 + 圈选表达式 | 实测时序输出；@smoke/not @wip |
| [08](08_profiles/README.md) | Profiles 多环境 | --profile 双环境切换 | ESM 函数形态；default 键必填 |
| [09](09_reports/README.md) | 报告体系 | json/junit/HTML 三路 | 失败标本截图附件；xmllint 合法 |
| [10](10_parallel/README.md) | 并行隔离 | 4 workers × 10 场景 | 唯一前缀零串号 |
| [11](11_example_mapping/README.md) | Example Mapping | 三色卡 → 红绿闭环 | UI+API 双层权限断言 |
| [12](12_living_doc/README.md) | 活文档 | pending 语义 + 清单抽取 | 黄≠红；功能清单自动生成 |
| [13](13_ci_github/README.md) | CI 集成 | bdd.yml + act 校验 | API 冒烟集容器可跑 |
| [14](14_final_suite/README.md) | 🏁 终极串联 | 三业务域 + 门禁 | 7 场景 36 步全绿；中文名净化坑 |

## 🗺️ 学习路线

```
 阶段一 (01-03)          阶段二 (04-06)          阶段三 (07-10)
 Gherkin 闭环      →    数据驱动/好坏      →    hooks/profiles/报告/并行
                        Gherkin 表达力          工程化四件套
 ─────────────────────────────────────────────────────────────────
 阶段四 (11-12)                       阶段五 (13-14)
 方法论两连                      →    CI 集成 → 🏁 终极 BDD 套件
 (Example Mapping/活文档)             (一条命令 + 门禁)
      ↑ 全程共用 playwright/02 的靶场 pw-store（91NN 端口实例）↑
```

## 🖼️ 架构图

每个实验 README 的 What 节内嵌双主题 SVG，交互版 HTML 在各自 `images/` 目录。

## ⚠️ 预期失败诚实标注

- 09 的 `reports_demo.feature` 一条人为失败标本（验证截图附件挂载）
- 12 的 `@planned` 场景保持 pending（黄，教学点：pending ≠ failed）
- 13 的 act 校验依赖代理与本地镜像（踩坑链同 playwright/18）

## 🧪 本机实测基线（2026-09-30）

| 能力 | 结论 |
|:---|:---|
| @cucumber/cucumber 13.2.1 + @playwright/test 1.62.1 + tsx | ✅（官方适配器 peer 锁 ^7 不可用，自建 World 方案） |
| 终极套件 run_suite.sh | ✅ 7 场景 36 步全绿，门禁通过 |
| multiple-cucumber-html-reporter 兼容 cucumber 13 | ✅（清单 ⚠️ 已实测转 ✅） |
| 中文 Gherkin 方言 | ✅（关键字以 gherkin-languages.json 为准） |
