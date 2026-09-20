# 13 · flaky 检测与隔离平台：让红色重新有信用

> 「重跑就过了」——这句话说出口的瞬间，CI 的红色已经一文不值。flaky 治理是大规模
> 自动化的生死线，本实验把治理做成四步闭环：**同 commit 10 轮重跑检测（结果不一致
> 即 flaky）→ 自动 quarantine（失败不挡主干但每次亮灯）→ 门禁联动（flaky 率喂给
> 项目 3）→ 修复后摘牌恢复全量监视**。实测：植入的随机失败与顺序依赖两个 flaky
> 10 轮内全部检出、稳定对照零误报；隔离后主干 3 连绿；摘牌瞬间恢复阻断。
> 清单第 13/28 项，必考中的必考。

## 1. 为什么需要它

- flaky 的定义（面试必背）：被测对象与测试条件不变，结果时过时不过；
- 危害链条：flaky → 习惯性重跑 → 假绿/真红不分 → 质量信号全面失真；
- 治理不是「找到它」而是**闭环**：检测→隔离→有人修→摘牌，缺任何一步都会退化成
  「隔离区垃圾场」。

## 2. 总览：核心机制一图看懂

![flaky 治理闭环](images/flaky_platform.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/architect/13_flaky_platform/images/flaky_platform.html)
> （或本地打开 [`images/flaky_platform.html`](images/flaky_platform.html)）。

心智模型一句话：**quarantine 是医院不是坟墓**——进去要亮灯（每次运行显示
QUARANTINED）、要有人跟（摘牌流程留痕）、能出来（修复后 --remove 恢复全量监视）。

## 3. 快速开始

```bash
cd architect/13_flaky_platform
./flaky_platform.sh apply     # 清空隔离区（植入的 flaky 用例常驻，注释即声明）
./flaky_platform.sh observe   # 10 轮检测 → 自动隔离 → 门禁联动 → 3 连绿 → 摘牌
./flaky_platform.sh clean
```

实测输出（节选）：

```
① 10 轮检测：flaky 率 40.0%（5 条中 2 条）
   ❗ test_random_flake：6/10 过（随机失败形态）
   ❗ test_order_dependent_victim：1/10 过（共享状态残留形态）
   ➡️ 双双自动入隔离区；3 条稳定对照零误报 ✅
③ 门禁联动：3 过 / 2 隔离 / 0 阻断 → 裁决 PASS（亮灯不挡路）
④ 主干连续 3 次 PASS ✅
⑤ 摘牌 test_random_flake 后重跑门禁：❌ BLOCKING（恢复全量监视）
```

## 4. 核心概念

### 4.1 检测的判据与成本
判据来自定义本身：同输入不同输出 = flaky。10 轮是统计与成本的折中——检出概率
1-(1-p)^10，40% 失败率的用例 10 轮内检出率 99.4%。成本是 10 倍执行，所以检测只跑
夜间层（项目 10 tier3），主干层只消费隔离清单。

### 4.2 植入的两种经典形态
随机失败（`random()<0.4` 断言失败）与共享状态残留（首轮通过但写脏文件，之后每轮
因残留必挂——「单独跑绿、连跑红」的经典）。两种在实测里分别呈现 6/10 与 1/10 的
通过率，检测器对两种形态一视同仁。

### 4.3 门禁的三态裁决
passed / QUARANTINED / BLOCKING——quarantined 失败不算 blocking，**但必须在报告里
亮灯**：隔离不是消失。flaky 率同时写入 flaky.json，项目 3 门禁的那条
`flaky_rate ≤ 2%` 规则自此有了数据源。

## 5. 关键设计

| 设计 | 为什么 | 坑 |
|:---|:---|:---|
| 植入用例常驻 tests/ | 检测器的对照组 + 永久的回归验证 | 注释声明「植入」，别让后人困惑 |
| junit file=None 用 classname 兜底 | 某些插件注入的用例没有 file 属性 | 不兜底会出现 `None::test_x` 幽灵条目 |
| 摘牌要 pattern 显式指定 | 摘牌 = 恢复阻断，必须是有意识的动作 | 自动摘牌等于没有隔离 |
| flaky.json 固定路径 | 跨项目数据契约（03 门禁直接读） | 契约字段（flaky_rate_pct）改动要同步两侧 |

## 6. 文件结构

```
architect/13_flaky_platform/
├── README.md
├── flaky_platform.sh              # apply → observe(检测/隔离/联动/摘牌) → clean
├── flaky_platform.py              # detect/gate/remove 三命令（约 170 行）
├── tests/
│   ├── test_stable.py             # 3 条稳定对照（零误报的证据）
│   ├── test_planted_flaky_a.py    # 植入：随机失败
│   └── test_planted_flaky_b.py    # 植入：共享状态残留
└── images/                        # 图三件套
```

## 7. 深入要点

**Q1：失败后自动重试是不是 flaky 治理？** 不是，是掩盖。重试把信号延迟而不是消除，
还引入「第二次执行环境已变」的新偏差。重试只该用于已知外部抖动的场景（网络闪断），
且要计数上报——重试率本身就是 flaky 率的代理指标。

**Q2：检测出 flaky 之后的责任归属？** quarantine 只是止血。规范做法：隔离时自动建单、
标注疑似根因分类（等待/竞态/数据/环境/依赖——apifox 十大根因清单）、限期修复；
超期未修的 flaky 进周报上会。工具只保证「不丢不瞒」，推进靠人。

**Q3：为什么 quarantine 后主干还能 PASS？这是不是自欺？** PASS 的语义变了：主干
回答「变更有没有引入新问题」，隔离区回答「已知的 flaky 修好了没」。两个问题分开
回答，信号反而更干净——前提是隔离区数量受控（flaky 率门禁 2% 就是总量闸门）。

**Q4：flaky 率的分母是什么？** 本实验 = flaky 用例数 / 总用例数（存量口径）。
另一个口径是「主干误报率 = flaky 引发的红 / 总红次数」（事件口径）——后者更能反映
开发者痛感，两者都该看。度量口径之争要先于数值之争（呼应项目 23）。

**Q5：顺序依赖的 flaky 怎么根治？** 三板斧：数据库/文件级隔离（项目 7 的命名空间
+ 生命周期）、进程级随机化（pytest-randomly 让顺序依赖无处藏身）、显式依赖声明
（pytest-dependency）。本实验的植入形态就是 labs/09 并行污染的教学续集。

## 8. 总结

两个植入 flaky 全检出、隔离后主干 3 连绿、摘牌瞬间恢复阻断——治理闭环的每一步
都有可验收的证据。当红色重新有信用，前面所有项目的绿才有意义。下一篇是清单项目 14
「失败聚类与根因归并」：一次提交挂 200 条用例时，怎么先修一个根因消掉 150 条红。
