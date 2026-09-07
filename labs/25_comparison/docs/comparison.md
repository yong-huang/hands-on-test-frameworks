# 三框架硬对比报告（同一 SUT · 同语义 5 用例矩阵）

> 数据来源：`./run_all.sh`（ROUNDS=3）在本机实测产出，CSV 见 `docs/results.csv`。
> 复现命令：`ROUNDS=20 ./run_all.sh`（验收场景可跑 20 轮；默认 3 轮以控制演示时长）。

## 1. 测试矩阵

统一 5 条同语义用例（每框架各自实现，断言语义一致）：

| # | 场景 | 考察点 |
|:--|:---|:---|
| 1 | 首页加载 | 启动/导航/元素出现 |
| 2 | 下单 | 表单交互 + 异步列表刷新 |
| 3 | 列表有行 | 轮询/等待策略 |
| 4 | 删除 | 定位+确认消失 |
| 5 | 慢接口 banner | 慢响应下的等待 |

## 2. 实测耗时（秒/轮，2026-09 本机）

| framework | r1 | r2 | r3 | 均值 | 说明 |
|:---|:---|:---|:---|:---|:---|
| Playwright 1.62 (Chromium) | 2.82 | 2.68 | 2.66 | **2.72** | 每轮起 3 个浏览器进程内会话 |
| Cypress 16 (Electron) | 3.00 | 3.01 | 30.58 | 3.00* | *第 3 轮含一次 30s 离群（Electron 冷启动抖动），如实记录 |
| Selenium 4.x (Chrome) | 5.89 | 5.30 | 5.72 | **5.64** | 每用例一个新 driver 会话 |

> 结论速读：快慢排序 Playwright < Cypress < Selenium；**绝对数值仅作量级参考**，
> 框架启动模型不同（PW 用例间复用会话、SE 每用例新 driver、CY 常驻浏览器）。

## 3. 稳定性（本轮实测 + 机制差异）

- 三框架各 15 次用例执行（3 轮 × 5 用例）全部通过，0 失败。
- 机制差异：Cypress 内置 runMode 重试（本实验配置 retries=1）；Playwright 靠
  expect 自动等待（lab 17）；Selenium 无内置重试，稳定性完全取决于显式等待纪律。

## 4. 调试体验（实测主观评价）

| 维度 | Playwright | Cypress | Selenium |
|:---|:---|:---|:---|
| 失败取证 | trace viewer 时间旅行（最强） | 命令日志 + 截图 + 时序悬停 | 只有 driver 日志（自建截图钩子） |
| 交互式调试 | PW Inspector / codegen | `cypress open` 运行器（最好用） | 无官方工具 |
| 网络控制 | route 拦截任意请求 | intercept 同级（浏览器内） | 需代理层（如 BrowserMob） |
| 多标签/多域 | 支持 | 受限（实验性） | 支持 |
| 并行 | xdist 原生 | 官方并行（需记录服务或分片） | Grid/容器 |

## 5. 场景选型结论（有据可依的口味题）

1. **新项目 Web E2E 首选 Playwright**：速度、trace 调试、三核矩阵、多语言绑定
   综合最优（本矩阵 2.7s/轮 且工具链零短板）。
2. **遗留 JS 项目 / 前端团队自维护测试选 Cypress**：运行器体验对前端最友好、
   时间旅行调试、生态插件成熟；接受单域限制与 Electron 内核。
3. **多语言团队 / 存量 WebDriver 资产 / 老 IE 兼容场景选 Selenium**：语言中立、
   生态最深、Grid 成熟；代价是等待策略与取证设施全要自建（lab 23/24 已演示）。

## 6. 复现方式

```bash
ROUNDS=3 ./run_all.sh     # 产出 docs/results.csv
ROUNDS=20 ./run_all.sh    # 20 轮验收场景
cat docs/results.csv
```
