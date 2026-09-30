# 🎭 playwright/：Playwright 进阶 19 实验动手系列（TypeScript 原生栈）

> 把 [docs/playwright.md](../docs/playwright.md) 清单落成的可真实跑通系列：
> TS 原生栈 → 靶场 SUT → 定位/认证/网络/视觉/组件 → 调试/POM/并行/矩阵/报告/flaky
> → 文件/实时/i18n+无障碍/API 混合 → 本地 CI 分片 → 🏁 终极串联。
> 与仓库主系列（labs/ 的 Python 栈 30 实验）**互补**：那边是 pytest-playwright 入门线，这边是 TS 深水区。
> 每个实验 = apply/observe/clean 主演示脚本 + 六段式 README + 交互架构图三件套。
> 全程免费本地跑：`bash playwright/load_resources.sh` 一次备齐 node 依赖与三核浏览器。

进度：**19/19 (100%)** ██████████

## 🚀 快速开始

```bash
bash playwright/load_resources.sh        # node 依赖 + Chromium/Firefox/WebKit 构建
cd playwright/01_pw_ts_stack && ./ts_stack.sh   # 第一个实验
cd playwright/19_pw_final_suite && ./run_suite.sh   # 🏁 全系列回归（163 用例，实测 78s）
```

## 📚 实验总表

| 实验 | 主题 | 一句话产出 | 验收亮点 |
|:---|:---|:---|:---|
| [01](01_pw_ts_stack/README.md) | TS 原生栈 | config 声明式测试工程 | 5 用例 × 3 浏览器全绿；baseURL 改端口零改动 |
| [02](02_pw_sut/README.md) | 靶场 SUT | pw-store 多功能区应用 | 双角色/订单/上传/WS/慢接口/嵌入 8 条冒烟 |
| [03](03_pw_locators_pro/README.md) | 定位深水区 | iframe/Shadow DOM/strict mode | 10 条用例连跑 10 轮全绿 |
| [04](04_pw_auth/README.md) | 认证矩阵 | setup 预登录双角色复用 | 16 执行全绿；伪造 token 模拟会话过期 |
| [05](05_pw_network_pro/README.md) | 网络控制 | HAR 录制回放 + 错误注入 | 杀掉后端离线回放仍全绿（394ms） |
| [06](06_pw_visual/README.md) | 视觉回归 | 基线生命周期全流程 | 变异注入变红 → 还原转绿；阈值双层级实测 |
| [07](07_pw_component/README.md) | 组件测试 | ct-react 挂载真浏览器 | 8 用例 1.0s vs E2E 同量 5.8s 对照 |
| [08](08_pw_debug/README.md) | 调试武器库 | 三病例 trace 解剖 | trace.zip 网络+截图核验；DEBUGGING 手册 |
| [09](09_pw_fixtures_pom/README.md) | fixture+POM | 两层 extend 类型安全 | 新用例 6 行；tests/ 零选择器门禁 |
| [10](10_pw_parallel/README.md) | 并行隔离 | 4 workers 抢一个 SUT | 23 用例零串号；1.83x 实测加速 |
| [11](11_pw_matrix/README.md) | 设备仿真 | 3 设备 × 明暗矩阵 | 36 执行全绿；深色背景/locale 断言 |
| [12](12_pw_reports/README.md) | 报告产物 | HTML/JUnit/trace/视频 | xmllint 验 JUnit；失败标本三产物齐挂 |
| [13](13_pw_flaky/README.md) | flaky 治理 | 注入 flaky 案底制度 | 重试绿标 flaky；5 轮 0 unexpected |
| [14](14_pw_files/README.md) | 文件闭环 | 上传下载字节级验证 | sha256 双重比对；DataTransfer 拖拽注入 |
| [15](15_pw_realtime/README.md) | 实时推送 | WS 帧级断言与闪断注入 | 帧到 UI <1.5s；断连重连徽标红→绿 |
| [16](16_pw_i18n_a11y/README.md) | i18n+无障碍 | locale 矩阵 + axe 门禁 | 双语文案矩阵；axe 抓出并修复对比度缺陷 |
| [17](17_pw_api_ui/README.md) | API+UI 混合 | 分层：API 管事实 UI 管呈现 | API 100 条 182ms；10 条分页验证 |
| [18](18_pw_ci_sharding/README.md) | 本地 CI 分片 | GHA workflow + act 校验 | 容器内 shard 真实执行；4×10 passed |
| [19](19_pw_final_suite/README.md) | 🏁 终极串联 | 一条命令 15 套件 | 163 passed / 0 failed / 78s 门禁通过 |

## 🗺️ 学习路线

```
 阶段一 (01-02)         阶段二 (03-08)           阶段三 (09-13)
 TS 栈 + 靶场     →    定位/认证/网络/视觉/     →   POM/并行/矩阵/报告/flaky
                        组件/调试                    工程化五件套
 ─────────────────────────────────────────────────────────────────
 阶段四 (14-17)                              阶段五 (18-19)
 文件/实时/i18n+a11y/API 混合          →   本地 CI 分片 → 🏁 终极串联
      ↑ 全程共用 02 的靶场 pw-store（端口 90NN 约定）↑
```

## 🖼️ 架构图

每个实验 README 的 What 节内嵌双主题 SVG，交互版 HTML 在各自 `images/` 目录
（本地直接打开可缩放/看动画轨迹）。

## ⚠️ 预期失败诚实标注

- 08 的 `broken.spec.ts` 三条病例**设计为红**（教学素材，脚本显式容忍）
- 12 的 `artifacts.spec.ts` 一条失败标本（验证产物挂载）
- 13 的两条注入 flaky 首跑红、重试绿（报告记 flaky 案底）
- 18 的 act 校验依赖代理与本地镜像（README 记录了完整踩坑链）

## 🧪 本机实测基线（2026-09-30）

| 能力 | 结论 |
|:---|:---|
| @playwright/test 1.62.1 + 三核浏览器 | ✅（npm 直连；浏览器构建直连下载） |
| 终极串联 run_suite.sh | ✅ 163 passed / 0 failed / 78s |
| ct-react 组件测试 | ✅（锁 1.62.1 与 test 同版本） |
| act 容器内分片执行 | ✅（需代理 + --bind + --pull=false，踩坑链见 lab 18） |
