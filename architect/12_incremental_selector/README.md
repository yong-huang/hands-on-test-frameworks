# 12 · 静态增量测试选择器：不跑一个测试，0.22 秒圈出影响面

> 精准测试有两条腿（面试标准答案）：项目 4 的**运行时路线**（覆盖率上下文，精确到行）
> 和本实验的**静态路线**（AST import 依赖图，零执行成本）。实测：88 个模块、42 个测试
> 文件的仓库里，对 store.py 的一行变更，0.22 秒选出 4 条测试并给出理由链——
> 同一变更运行时路线推荐 2 条，报告并列对比两条路线的选择差。清单第 12/28 项。

## 1. 为什么需要它

- 没有覆盖档案的仓库（新接手/历史包袱）也需要增量能力——静态路线不依赖任何历史运行；
- PR 流水线的第一道筛选要快：0.22 秒的静态圈选先裁剪，再让运行时推荐做精修；
- 「变更影响分析」是 AI 测试热题的地基——没有依赖图，AI 也是空谈。

## 2. 总览：核心机制一图看懂

![静态增量选择](images/incremental_selector.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/architect/12_incremental_selector/images/incremental_selector.html)
> （或本地打开 [`images/incremental_selector.html`](images/incremental_selector.html)）。

心智模型一句话：**AST 提取每个文件的 import → 建立「谁用了谁」的反向索引 →
从变更文件反向 BFS，可达的测试文件即选中集**——每条选中项带理由链
（store.py → 谁引了它 → 哪个测试）。

## 3. 快速开始

```bash
cd architect/12_incremental_selector
./incremental_selector.sh apply     # 扫全仓建 AST 注册表（零执行）
./incremental_selector.sh observe   # 造真实变更 → 静态选择 → 断言 → 与项目 4 对比 → 还原
./incremental_selector.sh clean
```

实测输出（同一变更，两条路线对比）：

```
② 静态选择：选中 4 条（0.22s，零测试执行）
   - labs/13_db_tests/tests/test_concurrent.py   理由链：store.py → test_concurrent.py
   - labs/13_db_tests/tests/test_isolation.py    理由链：store.py → test_isolation.py
   - labs/13_db_tests/tests/test_migration.py    理由链：store.py → test_migration.py
   - labs/14_testcontainers/tests/test_postgres.py（经 conftest import 链间接命中）
③ 验收断言：labs/13（直接 import store）在列 ✅；无关 labs（02/05/06）未误选 ✅
④ 双路线对比：静态选中 4 / 运行时推荐 2
   结论：静态是「可能受影响」的超集（宁多选不漏选），运行时是「真实碰过」的精确子集
```

## 4. 核心概念

### 4.1 模块注册表与过近似
扫描全仓 `*.py`，按文件名（stem）注册模块名 → 定义文件列表（同名模块多个定义全部保留）。
import 解析刻意只取顶层名：**静态分析的本分是保守过近似**——宁多选不漏选，
精确性交给运行时路线补刀。

### 4.2 反向 BFS 与理由链
变更文件入队 → 每个引用它的文件入队并记录来源 → 测试文件（test_*.py）即选中。
理由链是选择器的可信度来源：「为什么选我」必须能一路指回变更点，否则就是黑盒。

### 4.3 静态路线的天然盲区
labs/12 的 API 测试（httpx 打 SUT，不 import store）对静态路线**完全不可见**——
HTTP 层依赖只有运行时/契约路线看得见。这不是缺陷是边界：两条路线互补的根源
（本实验报告直接并列对比，差异一目了然）。

## 5. 关键设计

| 设计 | 为什么 | 坑 |
|:---|:---|:---|
| 只保留仓内注册的 import | 排除 stdlib/三方包的噪音 | 同名模块（conftest/main）会过近似——可接受 |
| conftest.py 也算测试资产 | 它的 import 变了同样影响用例（labs/14 经它命中） | 只统计不选中，选中集仍以 test_*.py 为准 |
| 理由链取末 3 跳 | 链太长没人看 | 截断处要标「…」，别伪装成直接依赖 |
| 变更文件 .py 过滤 | 非代码变更（README）不触发 | yaml 配置变更应走配置感知路线（项目 17） |

## 6. 文件结构

```
architect/12_incremental_selector/
├── README.md
├── incremental_selector.sh    # apply(建注册表) → observe(选择+断言+对比) → clean
├── selector.py                # AST 扫描/反向 BFS/双路线对比（约 160 行）
├── reports/selection.md/.json # 选择报告（clean 清除）
└── images/                    # 图三件套
```

## 7. 深入要点

**Q1：静态和运行时路线怎么组合投产？** 标准两级流水：PR 上静态秒级圈选（保底集合）→
若覆盖档案存在，运行时推荐做精修（交集跑、并集报）。没有档案时静态独挑——
这正是新项目冷启动的答案。

**Q2：为什么 import config_parser 的 labs/03 测试没被选中？** 变更是 store.py，
labs/03 不 import store——「不选」恰是正确行为。增量选择的纪律：只对变更负责，
不对「测试可能挂」负责（那是 flaky 治理的事）。

**Q3：AST 解析会不会被动态 import 骗过？** 会。`importlib`/字符串拼接的 import 对
AST 不可见——这是静态路线漏报的唯一来源。治理靠规范（禁止魔法 import）+
运行时路线兜底，而不是把解析器写成解释器。

**Q4：理由链为什么取末 3 跳？** 人的工作记忆容不下 6 跳引用链；末 3 跳足够回答
「它和变更的关联是什么」。全链存 JSON 供机器审计，MD 报告给人看——双表示是
报告设计的通用模式。

**Q5：和 AI 变更影响分析什么关系？** 依赖图是「事实层」，LLM 是「解释层」：
把图+diff 喂给模型让它生成影响说明与补测建议，比裸问模型可靠一个量级——
2026 年面 AI 测试题，答出「先建图再谈智能」就是分水岭。

## 8. 总结

0.22 秒、零执行、4 条选中全部带理由链，与运行时路线的对比直接写进报告——
增量选择的两条腿至此都齐了。下一篇是清单项目 13「flaky 检测与隔离平台」：
当「通过」不再可信，前面所有绿灯都要重新定义。
