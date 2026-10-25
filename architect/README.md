# 🏛️ architect/：测试架构师系列实验区（28/28 ✅ 全部完成）

> 问题驱动的 28 项目清单（[../docs/test_architect.md](../docs/test_architect.md)）落地区：
> 每个项目对应本目录下一个 `NN_short_name/` 实验，编号 01-28，与 labs/、performance/ 三线并列互不干扰。

**治理对象**：本仓库已有资产——labs/ 的 30 个框架实验 + SUT（labs/11 的 FastAPI 订单应用）。
**产物形态**：代码为主（脚本/工具/mini 平台），策略类项目只配必要的说明文档。

- [01_pyramid_audit](01_pyramid_audit/README.md) ✅ 测试资产分层审计——418 用例的金字塔画像
- [02_risk_strategy](02_risk_strategy/README.md) ✅ 风险驱动策略生成器——10 功能 4 级分布+缺口对照
- [03_quality_gate](03_quality_gate/README.md) ✅ 质量门禁引擎——5 规则 0.8s 裁决 + CI 退出码
- [04_precise_testing](04_precise_testing/README.md) ✅ 精准测试原型——1 行变更推荐 2/10 条省 80%
- [05_plugin_suite](05_plugin_suite/README.md) ✅ qa_kit 插件套件——失败留现场/慢排行/分层零侵入生效
- [06_dsl_engine](06_dsl_engine/README.md) ✅ YAML DSL 引擎——10 用例 74 行+失败定位到行号
- [07_data_factory](07_data_factory/README.md) ✅ 数据工厂+GC——3 轮不涨+100 孤儿清扫真数据保护
- [08_mock_server](08_mock_server/README.md) ✅ 录制回放挡板——断网回放一致+超时磁带降级
- [09_self_healing](09_self_healing/README.md) ✅ 自愈定位器——改版自愈率 1.0+档案免愈
- [10_pipeline_tiers](10_pipeline_tiers/README.md) ✅ 三层流水线——act 23s 冒烟+门禁+夜间档案
- [11_shard_scheduler](11_shard_scheduler/README.md) ✅ LPT 分片调度——246 条提速 76% 均衡 1.08
- [12_incremental_selector](12_incremental_selector/README.md) ✅ 静态增量选择——0.22s 理由链+双路线对比
- [13_flaky_platform](13_flaky_platform/README.md) ✅ flaky 治理闭环——检出/隔离/联动/摘牌全可验收
- [14_failure_clustering](14_failure_clustering/README.md) ✅ 失败聚类——50 红→3 根因纯度 100%
- [15_contract_matrix](15_contract_matrix/README.md) ✅ 契约版本矩阵——v1 放行 v2 拦截
- [16_env_factory](16_env_factory/README.md) ✅ 环境工厂——双套并发隔离 4s 零残留
- [17_config_drift](17_config_drift/README.md) ✅ 配置漂移检测——三环境矩阵+变异拦截
- [18_canary_eval](18_canary_eval/README.md) ✅ 灰度判定器——健康放量/劣化回滚双判定
- [19_synthetic_probe](19_synthetic_probe/README.md) ✅ 合成探针——3 链路时序+告警触发/消除闭环
- [20_load_model](20_load_model/README.md) ✅ 压测模型——推导 93 TPS 实测容量 185
- [21_fault_injection](21_fault_injection/README.md) ✅ 混沌四阶段——有界退化/熔断/自愈全验证
- [22_security_gate](22_security_gate/README.md) ✅ 安全三层门禁——植入 CVE 被点名拦截
- [23_metrics_dashboard](23_metrics_dashboard/README.md) ✅ 度量看板——6 指标字典驱动抽查一致
- [24_coverage_gate](24_coverage_gate/README.md) ✅ 覆盖率卡点——bot 拦截+豁免留痕
- [25_llm_eval](25_llm_eval/README.md) ✅ LLM 评测量尺——mock 四维满分+真实模式可选
- [26_escape_analysis](26_escape_analysis/README.md) ✅ 逃逸分析——10 案例归因+改进映射真实校验
- [27_panorama_board](27_panorama_board/README.md) ✅ 效能全景看板——make 一键 6 面板 11 指标
- [28_evolution_plan](28_evolution_plan/README.md) ✅ 架构演进方案——30 条证据 100% 可复核：用清单里每个项目的 🤖 开始提示词启动

## ⚠️ 预期失败诚实标注

- 01 的审计对 labs 的故意失败用例（labs/01/06/10/17/20）声明 `expected_fail`——「默认不绿」不会被误报成审计发现
- 13 植入的 flaky 用例（随机失败 + 顺序依赖）是检测素材：检出并进隔离区即验收
- 18 的劣化 canary 是故意注入的坏：抓红并做出回滚判定即验收
- 22 的植入 CVE、24 的覆盖率不达标提交，被门禁点名拦截/打回即验收
