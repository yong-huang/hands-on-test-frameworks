# ⬅️ shiftleft/：测试左移 20 实验（Python 栈）

> 把 [../docs/shiftleft.md](../docs/shiftleft.md) 清单落成的可真实跑通系列——架构师线管「体系怎么设计」，本线管「左移每个动作怎么落地」：
> 成本漏斗 → 需求可测性审计 → Example Mapping → 追溯矩阵 → 契约先行/挡板先行（挡板＝按契约生成的替身服务） → 可测性重构/TDD/变异 → 静态门禁/SAST/供应链/pre-commit → 防复发/PR 评审/CI 分层/性能预算 → 度量漏斗 → 🏁 全景串联。
> 不新造业务：治理对象就是 labs/11 的 FastAPI 订单应用，把它当「真实团队的代码库」做左移改造。
> 01-18 同一脚本生命周期：apply 自检 → observe 出证据 → clean 清残留（19 为 python 入口、20 为六阶段串联运行器，见总表备注）。
> 重叠项目已在各实验 README 标注与 architect 的分工（如 05↔15、06↔08、12↔22）。

进度：**20/20 (100%)** ████████████████████

## 🚀 快速开始

前置条件：仓库根 `.venv`（labs/00 体检通过）；01 用端口 8931/8932 仅本机使用。

```bash
cd shiftleft/01_cost_funnel
./cost_funnel.sh    # apply（依赖自检）→ observe（漏斗 + 对照）→ clean（清残留）
```

诚实预期：秒级数字每台机器不同（0.x 秒量级），「相差两个数量级」的结论稳定；02 的 AI 双引擎对比（规则分 vs LLM 语义分）
默认调本地 Ollama（本机大模型运行时），脚本输出「离线时加 `--no-ai` 跳过」——AI 全量耗时随模型与机器差异大，以 02 实测为准。

除 12/13 需联网拉规则库与漏洞库、03 复用 cucumber/ 的 node 依赖外，全系零 Docker、零外部服务。

## 📚 实验总表

| 实验 | 主题 | 一句话产出 | 验收亮点 |
|:---|:---|:---|:---|
| [01](01_cost_funnel/README.md) | 缺陷成本漏斗 | 同一个 float 缺陷放进六个关卡逐关实测拦截成本 | 「6/6 个运行关卡检出缺陷」；最左 5.0 分钟 vs 生产 480.0 分钟 → 96.0× |
| [02](02_testability_audit/README.md) | 需求可测性审计 | 五类规则+结构封顶对用户故事打分并逐条给改写建议 | 「39 passed——每条规则坏查得出、好零误报」；好故事 ≥80、坏故事 ≤60 |
| [03](03_example_mapping/README.md) | Example Mapping | 三色卡片一键转成结构合法的 Gherkin 骨架与疑问清单 | 「3 个场景（含大纲），6 条例子」解析零错误；脏故事 strict 模式 exit 1 |
| [04](04_trace_matrix/README.md) | 追溯矩阵 | pytest 收集×映射×需求三方对账的双向追溯矩阵，缺口即卡点 | 「收集 12 个测试 = 已映射 11 + 孤儿 1 ✓」；缺口演示「打回（exit 1）」 |
| [05](05_contract_first/README.md) | 契约先行 | OpenAPI 契约进 git，schemathesis 把契约变成 property 测试 | 「364 条 / 5 passed」；篡改实现「2 failed, 3 passed」、契约升级「1 failed, 4 passed」 |
| [06](06_mock_first/README.md) | 挡板先行 | 从契约动态生成挡板，provider 不存在消费方先开发 | 「5 passed in 0.22s（provider 从未启动）」；停挡板「5 failed（预期失败）」 |
| [07](07_dft_refactor/README.md) | 可测性重构 | 会话域依赖注入端口化，行为等价前提下过期测试提速 | 「过期测试墙钟 1.06s → 5µs」「加速 >10000×」；诚实标注 7 行 → 8 行 |
| [08](08_tdd_kata/README.md) | TDD 红绿重构 | 独立 git 仓库回放 5 轮红→绿 + 1 次重构，提交历史机械核验 | 「红 5 轮 / 绿 5 轮」「11 条运行记录与提交一一对应」 |
| [09](09_mutation/README.md) | 变异测试 | 自研 AST 变异器给定价模块造 7 个变异体，弱/强测试两轮对比 | 「mutation score 28.6% → 85.7%」；幸存者 #0 是等价变异 |
| [10](10_antipattern/README.md) | 反模式检测 | 纯标准库九类测试反模式只读检测器，可一键变 CI 卡点 | 坏样本 10 埋点全命中；好样本零误报；labs 全量「37 个测试文件，22 个反模式点」 |
| [11](11_static_gate/README.md) | 静态分级门禁 | ruff+mypy 发现按配置表分级：error 阻断、warning 留档 | 升降级三连：放行（exit 0）→ 阻断（exit 1）→ 放行（exit 0） |
| [12](12_sast_rules/README.md) | SAST 自定义规则 | semgrep 三条 FastAPI 自定义规则三路验证 | 「检出 4 / 5」+ 干净对照误报 0；漏检的第 5 条是规则盲区教学 |
| [13](13_supply_chain/README.md) | 供应链双闸 | pip-audit + gitleaks：依赖 CVE 与密钥扫描四项验收 | CVE 靶场「38 条已知漏洞」退出码 1；gitleaks「命中 2 处泄漏」 |
| [14](14_precommit_chain/README.md) | pre-commit 门禁链 | 四道检查编排成快层挡提交/重层管深查的本地链 | 「快层实测耗时 1s（<15s 达标）」；假密钥提交真实阻断 exit 1 |
| [15](15_recur_rules/README.md) | 防复发规则库 | 三个真实 bug 域沉淀为 2 条 semgrep 规则 + 1 个并发复现模板 | 「semgrep 拦截类别：2 / 3」；并发模板喂新代码「当场红（预期失败）」 |
| [16](16_pr_bot/README.md) | PR 评审机器人 | Danger 风格（评论不阻断）diff 评审，四条规则扫 PR 靶场 | 4 个问题 PR 全部命中、干净 PR 零警告，「实测耗时 0s（<5s 达标）」 |
| [17](17_ci_tiers/README.md) | CI 分层与预算 | 真 GitHub Actions YAML + 本地模拟器同源三层流水线 | 「actionlint 零告警」；三层预算 0.7s/1.85s/2.31s 全达标；埋 F401 后短路「已按预期退出 1」 |
| [18](18_perf_budget/README.md) | 性能预算左移 | 性能预算写成可执行断言：p95 与错误率超支即红 | 注入延迟「p95 1533ms 超预算 200ms」「已按预期退出 1」 |
| [19](19_metrics_funnel/README.md) | 左移度量漏斗 | 30 条跨阶段缺陷数据产出七阶段漏斗看板 | 「左移率：23/30 = 77%」；逐条可追溯出处 |
| [20](20_pipeline_all/README.md) | 🏁 全景串联 | 一条 run_all.sh 串联 6 阶段检查器 + 缺陷注入叙事 + 方案书 | 「编码阶段拦截 ≈2 min vs 生产 ≈480 min——左移杠杆 >200×」 |

> 注：19 的入口为 metrics_funnel.py（全系唯一无 .sh）；20 的 run_all.sh 为六阶段串联运行器，二者不适用三段生命周期。

## 🧭 学习路线

按编号 01 → 20 即路线，与 docs/shiftleft.md 的六阶段对应：

1. **01-04 需求与协作左移**：先算账（成本漏斗）→ 再把需求变可测（审计/卡片/矩阵）
2. **05-07 契约与设计左移**：契约先行 → 挡板先行 → 可测性重构
3. **08-10 编码左移**：TDD 节奏 → 变异测试体检测试强度 → 反模式检测
4. **11-14 提交左移**：分级门禁 → SAST 规则 → 供应链双闸 → pre-commit 链
5. **15-17 流程左移**：防复发规则 → PR 评审机器人 → CI 分层与预算
6. **18-20 非功能与度量收官**：性能预算 → 度量漏斗 → 🏁 全景串联

## 🖼️ 架构图

各实验 images/ 下为图三件套：`NN_name.html`（双击打开，可交互）· `.svg` · `.workflow.json`。

## ⚠️ 预期失败诚实标注

- 设计好的「预期红」贯穿全线：03 strict 退出码 1、06 停挡板 5 failed、11 严格档 exit 1、15 并发模板当场红、
  17 短路路径退出 1、18 延迟注入超预算——脚本内均有 `|| true` 或「已按预期」标注
- 01 的对照组 `--impl good` 仍会「1/6 检出」——关卡 1 拦的是测试计划缺口，与实现无关（不参与零误报统计）
- 09 的幸存变异体 #0 是等价变异（`"20.00"→"20.001"`），score 的理论边界需人工认定
- 12 检出 4/5 不是引擎故障——埋点 5 是「变量名无关的真密钥」，按变量名匹配的规则天然看不见
- 19 的入口是 `metrics_funnel.py`（全系唯一无 .sh 的实验）；13 的入口脚本名为 `scan.sh`

## 🔧 环境要求

macOS（Apple Silicon 实测）/ 仓库根 `.venv`（Python 3.13 实测；mutmut 3.8.0 直接可用）/ Node（仅 03，复用 cucumber/ 共享依赖）。

brew 工具按需自装（13/14 的 gitleaks、17 的 act 等）；联网点仅 12（semgrep 社区规则集）与 13（pip-audit 漏洞库）。

全线无 Docker 依赖（17 有 Docker 可用 act 真跑，无 Docker 由本地模拟器承担）。
