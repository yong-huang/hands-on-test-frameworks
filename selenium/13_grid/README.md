# 13 · Grid 分布式并行

## Background

单机串行跑 UI 回归，20 条用例 38 秒；套件到 500 条就是 15 分钟起步——并行是唯一的解。
Selenium Grid 把「用例」与「浏览器」解耦：用例只管把意图发给 hub，浏览器在 node 里排队领活。
pytest-xdist 负责把用例切成 N 份并发投递。

## What

- Grid 环境：`docker-compose.yml` 起 **standalone-chrome**（单容器版 Grid，`SE_NODE_MAX_SESSIONS=4` 承载 4 路并行）
- 20 条参数化首页用例经 `webdriver.Remote` 打向 Grid
- `.sh` 实测对照：串行 38s vs `pytest -n 4` 并行 11s → **提速 71%**（验收线 ≥60%）
- Grid 控制台：`http://127.0.0.1:4444/ui` 可见会话分配

## When to Use

- 套件时长超过团队等待忍耐阈值（一般 10 分钟）时的第一优化
- 需要浏览器版本/平台矩阵时的基础设施底座

## Quick Start

```bash
cd selenium/13_grid
./13_grid.sh            # apply（靶场+Grid）→ observe（串/并对照）→ clean（compose down）
```

实测输出（2026-10-26，节选）：

```text
串行墙钟：38s
并行墙钟：11s
提速 71%（验收线 ≥60%）
```

## How It Works

- Remote driver：`webdriver.Remote(GRID_URL, options)` 与本地 driver 用法完全一致——切换成本低
- xdist 起 N 个 worker 进程，各自建 Remote 会话；Grid 的会话槽位上限决定并行上限
- 提速比 ≈ min(并行度, 会话槽位) 的线性收益减去会话创建开销

## Pitfalls & Q&A

- **坑：`selenium/node-chrome:4.27.0` 无 linux/arm64 manifest**（实测 no matching manifest）——
  Apple Silicon 用本机已有的 arm64 原生 `standalone-chrome` 镜像，调大 `SE_NODE_MAX_SESSIONS` 替代多 node
- **坑：双 127.0.0.1**——Grid 容器里的 Chrome 访问 `127.0.0.1:8946` 打到的是容器自己；
  浏览器侧必须用 `host.docker.internal`（靶场 server 相应绑 0.0.0.0），测试进程侧仍用 127.0.0.1 连 hub
- **坑：被强杀的 pytest 留下僵尸会话占槽**——`SE_NODE_SESSION_TIMEOUT=120` 兜底自动回收
- **Q：xdist 和 Grid 什么关系？** xdist 管并发投递，Grid 管浏览器供给；没有 Grid 时 xdist 也能起本地浏览器，只是资源竞争在一台机器上
