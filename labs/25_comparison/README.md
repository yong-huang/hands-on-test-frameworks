# 25 · 三框架硬对比：同一 SUT、同语义用例，用数据说话

> 选型争论的尽头是数据。本篇用统一 5 用例矩阵 × 3 框架 × N 轮实测
> 耗时/稳定性，产出 `docs/results.csv` 与本报告——所有数字都是本机跑出来的，
> 不是抄官网。

## 1. 为什么需要它

- "哪个框架最好"是伪问题，"什么场景选谁"才是真问题——前提是有实测。
- 复测脚本 `run_all.sh` 一次落盘 CSV，数据可复查、可重跑（`ROUNDS=20`）。

## 2. 总览：矩阵执行与统计流

<!-- 图: images/comparison.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/labs/25_comparison/images/comparison.html)
> （或本地打开 [`images/comparison.html`](images/comparison.html)）。

run_all.sh 轮流驱动三套套件，每轮记录 耗时/通过/失败 → results.csv → 报告。

## 3. 快速开始

```bash
ROUNDS=3 ./run_all.sh       # 本报告的数据来源
ROUNDS=20 ./run_all.sh      # 验收场景：20 轮
column -t -s, docs/results.csv
```

## 4. 实测数据（2026-09，本机）

| framework | r1 | r2 | r3 | 均值 |
|:---|:---|:---|:---|:---|
| Playwright 1.62 | 2.82s | 2.68s | 2.66s | **2.72s** |
| Cypress 16 | 3.00s | 3.01s | 30.58s* | 3.00s* |
| Selenium 4.x | 5.89s | 5.30s | 5.72s | **5.64s** |

*Cypress 第 3 轮出现 30s 离群（Electron 冷启动抖动），如实保留不删——
**稳定性数据就该长这样**，不修图。

### 4.1 稳定性

3 框架 × 3 轮 × 5 用例 = 45 次执行，0 失败。机制差异：
重试 CY 内置（runMode:1）、PW 靠 expect 等待、SE 全靠显式等待纪律。

### 4.2 调试体验（主观但可复核）

trace viewer（PW）> 运行器命令日志（CY）> driver 日志（SE）。

### 4.3 场景选型结论

| 场景 | 推荐 | 依据 |
|:---|:---|:---|
| 新项目 Web E2E | Playwright | 最快 + trace + 三核矩阵 |
| 前端团队自维护 | Cypress | 运行器体验 + 生态 |
| 多语言团队/存量资产 | Selenium | 语言中立 + Grid 成熟 |

## 5. 脚本工程细节（复现必读）

- Cypress 的 spec 必须在其项目根内——脚本把 25 的套件拷进 21 的工程跑完即删。
- 三家输出格式不同（`N passed` / `passing: N` / `passing: N`），解析各自适配。
- 双 `-q` 会吞 pytest 的统计行——`-o addopts=` 清空再跑（本实验踩过）。

## 6. 文件结构

```
25_comparison/
├── README.md
├── run_all.sh                 # 一键复测（ROUNDS 可调）
├── configs/pytest.ini
├── tests/
│   ├── pw_suite.py            # Playwright 版 5 用例
│   ├── sel_suite.py           # Selenium 版 5 用例
│   └── conftest.py            # driver + sut_url
├── cypress/e2e/suite.cy.js    # Cypress 版 5 用例
├── docs/
│   ├── results.csv            # 原始数据（脚本产出）
│   └── comparison.md          # 本报告
└── images/
```

## 7. 面试要点

- **Q: 对比测试怎么设计才公平？** 同 SUT、同语义用例、同轮次、同机器；
  承认启动模型差异（会话复用 vs 每用例新 driver）——量级参考而非精确实验。
- **Q: 离群值怎么处理？** 保留并标注（如 CY 30s 一轮），不静默删除——
  稳定性本身就是对比维度。
- **Q: 结论会过时吗？** 会——框架迭代快，报告必须带日期与版本号，
  run_all.sh 随时可复跑。

## 8. 总结

阶段五毕业：三大框架全部上手且有了自己的选型判断。下一篇
[26_locust](../26_locust/README.md)：进入阶段六——给 SUT 上压力。
