# 20 · 多浏览器与失败留痕：三核回归 + 自动取证

> "在我机器上是好的"不是结论，"在三个内核上都是绿的"才是。本篇把同一套冒烟
> 跑在 Chromium / Firefox / WebKit 上，并配置**失败自动取证**——失败即得
> 截图、视频、trace 三件套，复现成本从"人肉调试一小时"降到"打开 trace"。

## 1. 为什么需要它

- 浏览器差异真实存在：CSS 引擎、JS 时序、fetch 行为各有脾气。
- CI 失败没有留痕 = 让值班同学盲猜。留痕是测试套件对维护者的基本礼貌。

## 2. 总览：三核矩阵与取证管线的产物流

<!-- 图: images/pw_quality.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/labs/20_pw_quality/images/pw_quality.html)
> （或本地打开 [`images/pw_quality.html`](images/pw_quality.html)）。

一套用例 × 三个内核 = 矩阵执行；任一失败 → test-results/ 下生成
screenshot + video + trace 三件产物，按用例名归档。

## 3. 快速开始

```bash
./pw_quality.sh    # ① 三核回归 ② 人为失败取证 ③ 产物清单
```

实测：三核冒烟 9/9 全绿（3 用例 × 3 内核）；故意失败用例产出
`test-failed-1.png` + `video.webm` + `trace.zip`。

```bash
../../.venv/bin/python -m playwright show-trace test-results/*/trace.zip   # 回放
```

## 4. 核心概念

### 4.1 矩阵执行的两种姿势

pytest-playwright 的 `--browser` 可重复传参（本实验脚本用法）；也可用
`pytest --browser-channel` 走系统安装的浏览器。产物目录按"用例名+内核"分桶。

### 4.2 WebKit 兼容性记录（诚实记录）

本 SUT 上 WebKit 无需特殊处理即可全绿——但保留了两处差异意识：
- banner 的 fetch 时序在 WebKit 略不同，断言一律 `expect` 等待（而非假设时序）；
- 若真遇到引擎特有 bug，正确姿势是 `pytest.mark.skipif(browser=="webkit")` 并
  附 issue 链接，而不是改断言迁就。

### 4.3 失败取证三件套

| 产物 | 命令参数 | 用途 |
|:---|:---|:---|
| 截图 | `--screenshot only-on-failure` | 失败瞬间的画面 |
| 视频 | `--video retain-on-failure` | 失败前的操作回放 |
| trace | `--tracing retain-on-failure` | DOM/网络/控制台时间旅行 |

`retain-on-failure` / `only-on-failure` 语义：成功即删、失败才留——
CI 磁盘友好，本地聚焦。

### 4.4 易错点

- 取证参数是 pytest-playwright 的 CLI 参数，不是 playwright.config（那是
  Node 版 Playwright 的配置位）——Python 线的等价物放 pytest 插件/ini。
- 留痕目录 `test-results/` 要进 .gitignore，但 CI 里要作为 artifact 上传（lab 30）。

## 5. 关键命令

```bash
pytest --browser chromium --browser firefox --browser webkit
pytest --screenshot only-on-failure --video retain-on-failure --tracing retain-on-failure
playwright show-trace test-results/<case>/trace.zip
```

## 6. 文件结构

```
20_pw_quality/
├── README.md
├── pw_quality.sh              # 三核回归 + 留痕演示
├── configs/pytest.ini
├── tests/
│   ├── test_smoke_multi.py    # 三核冒烟（3 条）
│   └── test_deliberate_break.py  # 留痕演示的"靶子"用例
├── test-results/              # 取证产物（运行后生成）
└── images/
```

## 7. 面试要点

- **Q: 三核矩阵的成本怎么控制？** 冒烟进矩阵、全量回归挑核；PR 跑 Chromium、
  夜间跑满矩阵；利用 `pytest-xdist` 把矩阵并行化。
- **Q: 视觉回归和本篇的截图有什么区别？** 失败截图是"留证据"，视觉回归是
  "断像素"（基线 diff，如 Percy/lostpixel）——后者需要基线管理策略。
- **Q: trace 和 video 二选一？** trace 信息密度远高于 video；video 给
  非工程师看过程，trace 给工程师定位问题——两者都要但只在失败时留。

## 8. 总结

Playwright 全家桶毕业：定位、等待、POM、拦截、多核、留痕。
下一篇进入阶段五：[21_cypress_basics](../21_cypress_basics/README.md)——
Cypress 来了，同一 SUT 的三国杀开始。
