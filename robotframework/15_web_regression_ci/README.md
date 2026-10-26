# 15 · 🏁 Web 回归套件 + act 本地 CI

## Background

「本地绿、CI 才算数」——回归套件只有在 CI 真跑通才算可交付。act 把 GitHub Actions
workflow 原样跑在本机 Docker 里，与云端同源。本机网络实测 github.com 不通（playwright/18、
labs/30 同款踩坑链），本篇给出**离线 act** 的完整工程化方案。

## What

- 回归套件：业务关键字库（`resources/web_keywords.resource`）+ 3 条用例（主流程×2 + 慢元素防线）
- 失败自动截图（`Run Keyword If Test Failed` 挂 Teardown，通过零附件）
- workflow：**零外部 action + job 级 container 用 selenium/standalone-chrome 镜像**——
  act 离线真跑全绿（Set up → 装依赖 → 起靶场 → 跑套件 → 报告归档 五步全 ✅）
- 本地与 act 容器内跑同一套件，口径一致

## When to Use

- 回归套件进 CI 的标准姿势（本地 act 预演 → 推上去云端同构跑）
- 内网/离线环境的 CI 方案（镜像自带浏览器，全程零外联）

## Quick Start

```bash
cd robotframework/15_web_regression_ci
./15_web_regression_ci.sh            # 本地 3 passed
# act 离线真跑（从仓库根）：
cd ../.. && act -b -W robotframework/15_web_regression_ci/.github/workflows/regression.yml \
    -j regression -P ubuntu-latest=catthehacker/ubuntu:act-latest
```

实测输出（2026-10-27，节选）：

```text
本地：3 tests, 3 passed, 0 failed
act：✅ 环境自检 ✅ 安装依赖 ✅ 起靶场 ✅ 跑回归套件 ✅ 报告归档 → act rc=0
```

## How It Works

- job 级 `container: selenium/standalone-chrome`——镜像自带 google-chrome + chromedriver
  （版本匹配、PATH 直达），Selenium 4 先查 PATH 命中即不走 Selenium Manager 的网络下载
- 零 `uses:`——act 离线跑不能从 github 拉 action 仓库；仓库内容用 `act -b`（bind 挂载）进容器
- 容器里 Chrome 以 root 跑需要 `--no-sandbox --disable-dev-shm-usage`（resource 的 Open Browser 加 options）

## Pitfalls & Q&A

- **坑：actions/checkout 等外部 action 离线拉不到**（dial tcp github 443 timeout）——
  离线 workflow 必须「零 uses: + bind 挂载」；云端跑同一文件时再换回 action 形态
- **坑：Ubuntu 24.04 的 chromium-browser 是 snap 空壳包**——apt 装出来的 chromedriver
  有、浏览器没有（1snap1 wrapper，容器里 snap 不可用）；直接用自带浏览器的 selenium 镜像最稳
- **坑：`working-directory` 相对 act 的挂载根**——从子目录跑 act 会把路径叠加成双写
  （实测 chdir to cwd .../15_web_regression_ci/robotframework/... 失败）；act 永远从仓库根跑
- **Q：为什么不用 hub+node 矩阵跑 CI？** 离线口径下 standalone 单容器足够；矩阵是
  13 号实验的进阶题
