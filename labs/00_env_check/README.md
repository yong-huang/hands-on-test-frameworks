# 00 · 环境体检：一次脚本确认整条测试工具链

> 动手系列的第一课不是写测试，而是**确认你的机器真能跑**。
> 测试工具链横跨 Python / Node / Docker / 浏览器四个世界，任何一个缺位都会让后面的
> 实验卡在"装环境"而不是"学测试"。本实验用一个脚本把 30 个实验的前置全部体检一遍。

## 1. 为什么需要它

- 本系列 30 个实验共享一套环境：一个 venv、Playwright 三核浏览器、k6/act CLI、Docker。
- 与其每个实验各自报错，不如先有一个"体检脚本"——跑到哪个实验缺什么，回来补什么。
- `scripts/load_resources.sh` 是全系列唯一的安装入口，**幂等**（重复执行无害）。

## 2. 快速开始

```bash
# 一键安装（venv + 依赖 + 浏览器 + CLI）
bash scripts/load_resources.sh

# 只体检不安装，看缺什么
bash scripts/load_resources.sh check
```

体检项与对应实验：

| 体检项 | 缺了影响哪些实验 |
|:---|:---|
| Python 3.11+ / venv | 全部 |
| pytest 全家桶（cov/xdist/asyncio/playwright…） | 01-20、25、26、29 |
| Playwright Chromium/Firefox/WebKit | 16-20、28 fallback |
| Node 20+ / npm | 21、22、25 |
| Docker daemon 可用 | 14、24、29、30（act） |
| k6 | 27 |
| act | 30 本地复跑 |
| Chrome / Safari（系统自带） | 23、24 Selenium |

## 3. 预期失败诚实标注

- **Safari 自动化**（lab 23/24）：macOS 默认禁用 `safaridriver`，需要你手动执行一次
  `safaridriver --enable`（要求 sudo + 在"安全性与隐私"里允许）。脚本不会替你做这一步，
  lab 23 会检测并给出指引，Chrome 路径不受影响。
- **Appium**（lab 28）：Xcode + Appium 链路最长，实验内置了 Playwright 移动视口 fallback，
  环境受阻时 fallback 也算完成（清单原文如此）。
- **GitHub Actions**（lab 30）：push 到 GitHub 才有云端流水线；本地用 `act` 复跑。

## 4. 深入要点

- **Q: 测试环境管理最容易踩的坑？** 依赖污染——全局 pip 装一圈后版本互相踩。用 venv 隔离、
  锁定版本、CI 里每次全新安装，是三条基本功。
- **Q: 为什么浏览器自动化要单独管理浏览器二进制？** 浏览器版本 × 驱动版本 × 库版本三方
  匹配问题（Selenium Manager / Playwright 缓存 / Cypress 自带 Electron 都是在解这个问题）。
- **Q: CI 上跑 E2E 要什么前置？** 无头浏览器 + 干净容器 + 稳定端口 + 等待策略，本系列的
  脚本全部按"CI 可跑"标准写：不依赖 GUI、清理不留残。

## 5. 总结

环境就绪后，进入 [01_pytest_basics](../01_pytest_basics/README.md)——从 pytest 运行规则开始。
