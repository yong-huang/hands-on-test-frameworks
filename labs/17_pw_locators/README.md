# 17 · 定位器与等待哲学：竞态、延迟渲染与"10 连跑不红"

> E2E 最贵的不是执行时间，是 flaky——同一套代码时绿时红。
> 治 flaky 的哲学只有一句：**永远断言结果，不断言时刻**。本篇用 SUT 的
> 慢加载页（1.5s 接口 / 2s 延迟列表 / 1s 竞态按钮）训练稳定写法，并连跑 10 次验稳。

## 1. 为什么需要它

- "睡 3 秒总够了吧"——不够的时候叫事故，够的时候叫浪费。
- 本实验实测：给足固定 sleep 的写法每条用例白等 3s；expect 只等实际需要的时长。

## 2. 总览：一次点击背后的等待博弈

<!-- 图: images/pw_locators.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/labs/17_pw_locators/images/pw_locators.html)
> （或本地打开 [`images/pw_locators.html`](images/pw_locators.html)）。

点击后 UI 分三个阶段变化：disabled → 处理中 → 完成。反模式断言"立刻该看到完成"，
稳定写法断言"最终会完成"，把时长交给 expect 的重试循环。

## 3. 快速开始

```bash
./pw_locators.sh                              # 全流程，含 10 连跑
STABILITY_RUNS=30 ./pw_locators.sh observe    # 想跑更多次
```

实测：① 稳定写法 5 条全绿；② 反模式用例当场必挂；③ 连跑 10 次全绿。

## 4. 核心概念

### 4.1 稳定写法三原则

1. **断言终态**：`expect(race_box).to_have_text("…✅")` 而不是"点完立刻查"。
2. **给已知慢 UI 显式超时**：SUT 的延迟列表要 2s，本实验给 15s——
   超时不是赌来的，是按"基线 × 10 倍余量"定的（机器高负载下 5s 默认值实测会抖）。
3. **role 定位优先**：语义定位不怕 CSS 类名重构。

### 4.2 反模式清单（本实验全部真实演示）

| 反模式 | 后果 | 对策 |
|:---|:---|:---|
| `time.sleep(0.5)` 后立即断言 | 慢机器必挂（② 步复现） | expect 自动重试 |
| `sleep(3)` 给足再断言 | 每条白等 3s | expect 只等实际时长 |
| `is_visible()` / `count()` 断言 | 不等待，立即返回 | `to_be_visible()` / `to_have_count()` |
| 断言中间态（"处理中…"） | 竞态时红时绿 | 只断言终态 |

### 4.3 稳定性的度量方式

"稳定"不是感觉，是**连跑 N 次全绿**。脚本 ③ 步默认 10 次、每次输出独立结果行；
接入 CI 后用重跑统计（flaky 率 = 重跑成功率）持续监控。

### 4.4 易错点

- expect 的默认 5s 超时对"已知慢"的场景要显式放大，而不是全局调大——
  全局调大等于给所有失败买 30 秒的延迟。
- 网络空闲（`networkidle`）是诊断工具不是断言工具；断言仍以 UI 终态为准。

## 5. 关键字段

```python
expect(loc).to_have_text("终态文案", timeout=15_000)  # 文本等变
expect(loc).to_have_count(3, timeout=15_000)          # 数量等到
page.wait_for_function("...")                          # 复杂条件的逃生舱
```

## 6. 文件结构

```
17_pw_locators/
├── README.md
├── pw_locators.sh             # 含 10 连跑稳定性证明
├── configs/pytest.ini
├── tests/
│   ├── test_waits.py          # 5 条稳定写法（延迟/竞态/慢接口/role/回归）
│   └── test_antipattern.py    # 两版反模式（必挂版 + 浪费版）
└── images/
```

## 7. 面试要点

- **Q: 怎么系统性治 flaky？** 消灭固定 sleep、断言终态、显式超时、隔离数据、
  连跑度量——本实验五件事就是清单。
- **Q: expect 重试的机制？** 定位器解析 + 条件检查的轮询循环，DOM 变化即触发，
  直到超时；失败报告带每轮快照。
- **Q: 什么时候允许 sleep？** 几乎从不；演示动画、第三方风控弹窗等"无 UI 钩子"
  场景才考虑，且要注释原因。

## 8. 总结

稳定 E2E 的肌肉记忆养成。下一篇 [18_pw_pom](../18_pw_pom/README.md)：
把定位器收口进页面对象，让新用例的成本降到 10 行。
