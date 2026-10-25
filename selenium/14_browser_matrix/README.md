# 14 · 多浏览器兼容矩阵

## Background

「在 Chrome 上能跑」不等于「能跑」：Safari 没有无头模式、Fire fox 键入行为不同、
原生的 click 在 Safari 后台窗口里根本不产生事件。矩阵测试的意义是把「哪些地方不一样」
从玄学变成清单。

## What

- 冒烟用例（表单回读）+ 标题一致性用例，跑遍 **Chrome / Firefox / Safari** 三浏览器
- 产物：[COMPAT_NOTES.md](COMPAT_NOTES.md)——5 条本机实测差异（无头能力/相对定位器锚写法/
  newWindow 返回值/日期段位/Safari 前台点击），每条带应对策略

## When to Use

- 发版前跨浏览器回归（矩阵 = 用例 × 浏览器，套一套就是）
- 新用例上线前先在矩阵上过一遍，把浏览器特定坑写进 COMPAT_NOTES

## Quick Start

```bash
cd selenium/14_browser_matrix
./14_browser_matrix.sh            # 6 passed（Safari 有头会弹窗）
```

实测输出（2026-10-26，节选）：

```text
[firefox] 冒烟通过
[safari] 冒烟通过
6 passed in 6.43s
```

## How It Works

- 矩阵夹具：`@pytest.fixture(params=BROWSERS)` × `make_driver(name)`，Safari 分支强制有头
- Safari 分支的点击走 JS click 兜底——矩阵验证的是**表单逻辑跨浏览器一致**，不是点击机制本身

## Pitfalls & Q&A

- **坑：Safari 非前台时原生 click 不产生 click 事件**；实测「激活前台再点」反而 120s 阻塞——
  Safari 分支统一 JS click 兜底（差异清单 #5）
- **坑：safaridriver 是单会话配对**——上次卡死的会话不清掉，新会话直接
  `SessionNotCreated: already paired`；`pkill -f safaridriver` 后重试（差异清单 #6 已补）
- **Q：为什么不用 Grid 跑矩阵？** Grid 的 node-chrome 无 arm64 镜像（见项目 13）；本机三浏览器
  本地矩阵已覆盖教学目标，容器化矩阵留作 Grid 线的进阶
