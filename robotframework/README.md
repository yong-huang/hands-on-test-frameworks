# 🤖 robotframework/：Robot Framework 自动化 17 实验（Web + API + RPA 全家桶）

> 把 [../docs/robotframework.md](../docs/robotframework.md) 清单落成的可真实跑通系列——关键字驱动的完整闭环：
> 地基（靶场/关键字/数据驱动）→ Web（SeleniumLibrary 四连）→ API（RequestsLibrary 三连 + 混合场景）
> → 工程化与 RPA（自定义库/编排并行/Excel 批处理/桌面计算器）→ 🏁 三连串联（回归+CI / API 全集 / 全景流水线）。
> 全系列打自建的 **Robot 专属靶场**（`shop/`：Web 下单表单 + 订单查询页 + 4 个 REST 接口 + 慢元素/iframe/懒加载，
> 端口 8952，与 selenium 线靶场互不依赖）。
> 与 docs/selenium.md 互补：同一批 Web 能力，那边代码驱动、这边关键字驱动；与 appium/（库工程化）、
> mocking/（契约思想）双向复用。

进度：**17/17 (100%)** ██████████████████

## 🚀 快速开始

前置条件：仓库 venv 一条命令装全家桶（robotframework + seleniumlibrary + requests +
jsonlibrary + datadriver + pabot + rpaframework，命令见 docs/robotframework.md 环境配置）。

Chrome（headlesschrome）/ Firefox ✅；项目 14 另需 macOS 辅助功能权限（脚本自检并给路径）；
项目 15 的 act 离线跑需 Docker + selenium 镜像（labs/24 已拉）。

```bash
cd robotframework/01_shop_first_suite
./01_shop_first_suite.sh            # 建靶场 + 首个套件（2 passed）
bash ../shop/shop.sh clean          # 显式停靶场（公共设施，clean 不代停）
```

每实验同构：`apply` 幂等拉靶场 → `observe` 跑套件出 log/report 三件套 → `clean` 清产物。

## 📚 实验总表

| 实验 | 主题 | 一句话产出 | 验收亮点 |
|:---|:---|:---|:---|
| [01](01_shop_first_suite/README.md) | 靶场与首套件 | 独立靶场（Web+4 REST）+ 首套件 | 2 passed；Suite Setup 坑（不存在关键字连坐失败） |
| [02](02_keywords_vars/README.md) | 关键字宇宙 | 业务关键字下沉 .resource + FOR/IF | dryrun 校验关键字引用完整性 |
| [03](03_data_driven/README.md) | 数据驱动两板斧 | [Template] 内联 5 组 + 外部 CSV 4 组 | 负向 422 断言；⚠️ DataDriver 1.11.2×RF7.5 不兼容实测 |
| [04](04_web_intro/README.md) | Web 入门 | 下单主流程 + 慢元素 Wait Until | 无头/有头双跑 2×2 passed |
| [05](05_web_widgets/README.md) | 控件全集 | 多选/复选/radio/文件上传+汇总断言 | PASS；Radio Button Should Be Set To 正名 |
| [06](06_web_complex/README.md) | 三难 | iframe/多窗口/懒加载 30 件 | 3 passed |
| [07](07_expected_failures/README.md) | 期望失败与留证 | 4 负向全绿 + 注入失败截图 | ⚠️ RF7.5 EXCEPT glob 模式失效实测（精确/AS 可用） |
| [08](08_api_intro/README.md) | API 入门 | 4 接口全覆盖（5 用例 10 断言） | expected_status 一字诀；内联字典花括号坑 |
| [09](09_api_schema/README.md) | Schema 与矩阵 | JSON Schema 正反向 + 3×3 负向矩阵 | jsonschema 引擎在拦；逐格断言 error 字段 |
| [10](10_api_web_hybrid/README.md) | ⛓️ 混合场景 | API 造数 → Web 支付 → 复核清理 | 零 created 残留；等待唯一订单号防假命中 |
| [11](11_custom_library/README.md) | 自定义关键字库 | ShopLibrary 5 关键字 + libdoc 文档 | 4 用例双向验证；同毫秒撞后缀坑（计数器兜底） |
| [12](12_tags_pabot/README.md) | 标签与编排 | --include 筛选/pabot 并行/重跑合并 | rebot -R 合并 7/0（orig 在前的参数序坑） |
| [13](13_rpa_excel/README.md) | RPA Excel | 10 行批量下单（2 非法不中断）+ 结果回写 | 8 成功/2 失败如实入表 |
| [14](14_rpa_desktop/README.md) | RPA 桌面 | macOS 计算器 5 道四则 + 剪贴板 | 2 passed；结果层在 scroll area 2 |
| [15](15_web_regression_ci/README.md) | 🏁 回归+CI | 关键字库化回归 + act 离线真跑 | act 五步全 ✅（零 uses:+selenium 镜像 container） |
| [16](16_api_regression/README.md) | 🏁 API 回归全集 | 21 条（正向/异常/Schema/状态机） | 21/0；抓到靶场重复取消真 bug |
| [17](17_panorama/README.md) | 🏁 全景串联 | Excel→API→Web→回写→rebot 合并 | 10 行 → 8 笔 → 复核一致，五步闭环 |

## 🧭 学习路线

按编号 01 → 17 即路线：

1. **01-03 地基**：靶场与首套件 → 关键字分层 → 数据驱动两板斧
2. **04-07 Web 四连**：入门 → 控件全集 → 三难 → 期望失败与留证
3. **08-10 API 三连**：全覆盖 → Schema 与矩阵 → ⛓️ 混合场景
4. **11-14 工程化与 RPA**：自定义库 → 标签编排 → Excel 批处理 → 桌面计算器
5. **15-17 🏁 收官**：回归+CI → API 回归全集 → 全景串联

## ⚠️ 预期失败诚实标注

- 03 的板斧二因 DataDriver×RF7.5 不兼容改走 CSV+FOR（目标不变：加一行数据不加代码），不兼容实证在案
- 07 的 4 条负向按预期绿、1 条注入失败按预期红（取证素材）；RF7.5 EXCEPT glob 失效是本轮实测新发现
- 13 的 2 行非法订单**不是用例失败**——RPA 的验收是「处理完 + 结果表如实」
- 16 抓到的「重复取消未拦」是靶场真 bug（修服务端而非放宽断言）

## 🔧 环境要求

macOS（Apple Silicon 实测）/ 仓库 venv / Chrome+Firefox（headless）/ Docker（仅 15 的 act）。
项目 14 需辅助功能授权；全部实验 `clean` 后零残留（靶场由 shop/shop.sh 统一管生死）。
