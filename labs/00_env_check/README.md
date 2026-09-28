# 00 · 环境体检：一次脚本确认整条测试工具链

> 测试工具链横跨 Python、Node、Docker、浏览器四个世界，缺哪一环，实验都会卡在"装环境"
> 而不是"学测试"。本实验用一个幂等脚本把 30 个实验的前置依赖一次体检完：读完本篇你能跑通
> 环境体检，看懂每项检查对应哪些实验，并在缺项时知道去哪补。

## Background

没有体检脚本时，新手通常按教程逐条敲安装命令：装 Python、`pip install` 一串包、
`npm install`、下载浏览器。每一步当时都"成功"，但没有人验证整体可用——第一次真正跑测试
才发现 `ModuleNotFoundError`，回头补装，再跑再报下一个缺失。

痛点在于测试工具链的跨度：Python 生态（pytest 及插件）、Node 生态（Cypress）、Docker（把应用连同依赖打包成可随时启停的"容器"的工具；testcontainers、act）、浏览器二进制（Playwright、Selenium）。

任何一环缺位，故障都延迟到具体实验里才暴露，而报错信息只说"缺模块 / 连不上 / 找不到浏览器"，不说"你缺的是哪项环境"。再加上机器之间的差异（macOS 还是 Linux、Docker 是否在运行），"在我机器上能跑"成为常态。


本系列的解法是把 30 个实验的依赖收敛到一个入口脚本 `scripts/load_resources.sh`：
先体检后安装、缺哪个补哪个、重复执行无害。学习路径的第一课不是写测试，而是让环境可验证。

## What

环境体检脚本是一种**幂等的依赖探测工具**。幂等（idempotent，指重复执行结果不变、
不会把已经配好的环境改坏）在这里意味着：脚本能跑第二遍、第三遍，缺什么补什么，全齐了就只报告不动手。

可以把体检脚本想象成电脑开机自检（POST，开机时逐项硬件自检的流程）：逐项点亮，
哪项不亮先修哪项。但和开机自检不同的是，它有两种模式——`check` 只诊断、不动环境；
默认模式诊断后自动补缺。

体检覆盖五类依赖，每类都标注缺失时影响哪些实验（见 Quick Start 的体检项表）。

## When to Use

典型场景：

- 新机器或新同事第一次 clone 本仓库：跑完体检就知道还缺什么，不用等实验报错。
- 升级系统、换分支或长期没跑之后：怀疑环境漂移（环境偏离可用状态）时，30 秒定位是哪一环。
- 某个实验报 `command not found` 之前：先回来体检补齐，而不是照着报错盲目安装。

何时不用：已经明确是单一工具的问题时，直接对该工具执行 `--version` 更快；CI（持续集成，提交后自动跑检查的服务）
环境里每次都是全新容器，不存在"漂移"，直接安装即可（安装脚本仍然用于装依赖）。

同类方式对比：

| 方式 | 差异 | 什么时候选它 |
|:---|:---|:---|
| 手工逐个 `--version` | 精确但要自己记住清单 | 排查单个工具 |
| `pip check` | 只查 Python 包之间的依赖冲突 | 怀疑 pip 环境损坏 |
| 本脚本 | 覆盖四个世界 + 映射到实验编号 | 系列学习开始前、环境漂移排查 |

## Quick Start

前置条件：macOS 或 Linux（Windows 建议在 WSL2 里使用，WSL2 是 Windows 内置的 Linux 子系统）；
首次安装需要网络可达 PyPI 与 npm。

```bash
# 只体检不安装，看缺什么
bash scripts/load_resources.sh check

# 一键安装（venv + 依赖 + 浏览器 + CLI）
bash scripts/load_resources.sh
```

`check` 模式的真实输出（2026-09-28 实测，节选）：

```
=====> [check] 环境体检
  ✅ python3 Python 3.13.9
  ✅ node v22.23.2
  ⚠️  docker 不可用（lab 14/24/29/30 的 act 受阻，README 已标注）
  ✅ .venv 就绪（Python 3.13.9）
  ✅ k6 k6 v2.2.0 (commit/devel, go1.26.5, darwin/arm64)
  ✅ act act version 0.2.89
```

诚实预期：这台机器上 Docker daemon（Docker 的常驻后台服务，所有 docker 命令实际由它执行）没有启动，所以 docker 一项是警告而不是绿色——
这是脚本按实况报告，不是输出示例。体检项与受影响实验的对应关系：

| 体检项 | 缺了影响哪些实验 |
|:---|:---|
| Python 3.11+ / venv | 全部 |
| pytest 全家桶（cov/xdist/asyncio/playwright…） | 01-20、25、26、29 |
| Playwright Chromium/Firefox/WebKit | 16-20、28 fallback |
| Node 20+ / npm | 21、22、25 |
| Docker daemon 可用 | 14、24、29、30（act） |
| k6（负载测试 CLI） | 27 |
| act（本地复跑 GitHub Actions 的 CLI） | 30 本地复跑 |
| Chrome / Safari（系统自带） | 23、24 Selenium |

诚实预期（这些坑脚本不会替你解决）：

- **Safari 自动化**（lab 23/24）：macOS 默认禁用 `safaridriver`（Safari 的官方自动化驱动），
  需要手动执行一次 `safaridriver --enable`（要求 sudo + 在"安全性与隐私"里允许）。
  脚本不会替你做这一步，lab 23 会检测并给出指引，Chrome 路径不受影响。
- **Appium**（lab 28）：Xcode + Appium 链路最长，实验内置了 Playwright 移动视口 fallback，
  环境受阻时 fallback 也算完成。
- **GitHub Actions**（lab 30）：push 到 GitHub 才有云端流水线；本地用 `act` 复跑。

## How It Works

脚本的幂等来自"先探测、后安装"的结构：每一类依赖先做一个廉价的可用性检查，
只有检查失败才执行安装动作。安装 venv（Python 的虚拟环境——把一个项目的依赖装进独立目录，
不污染全局）的判定逻辑：

```bash
if [ ! -x "$PY" ]; then
    python3 -m venv "$VENV"
    "$VENV/bin/pip" install --quiet --upgrade pip
fi
# 只在缺包时装（幂等）
if ! "$PY" -c "import pytest, httpx, fastapi, playwright, hypothesis, syrupy, locust, selenium" 2>/dev/null; then
    "$VENV/bin/pip" install --quiet \
        pytest pytest-cov pytest-xdist pytest-asyncio pytest-playwright pytest-html \
        hypothesis syrupy time-machine freezegun httpx requests \
        fastapi "uvicorn[standard]" locust selenium \
        "testcontainers[postgres]" pact-python psycopg2-binary axe-playwright-python
fi
```

为什么用 `import` 探测而不是比对已安装包的版本清单：一条 `import` 语句同时验证了"包已安装"和"包能正常加载"两件事，且不会因为版本号变化而触发反复重装。

浏览器二进制同理——Playwright 的缓存目录（`~/Library/Caches/ms-playwright`）里缺哪个内核才补装哪个，三个内核互不牵连。


输出里的警告行也值得注意：`⚠️ docker 不可用` 后面直接跟了受影响的实验号
（lab 14/24/29/30）。体检的价值不只是"缺什么"，而是"缺什么"与"影响谁"同时给出——
你可以据此决定是现在补装，还是先跳过受影响的实验。

每个实验的脚本都会 source（在脚本里加载执行另一个脚本的内容）这个入口文件，
因此 venv 的激活也是幂等的：虚拟环境存在就把它的 `bin` 目录前置到 `PATH`，不存在就跳过。

## Pitfalls & Q&A

踩坑清单：

- **Safari 路径报 safaridriver 无法启动**。原因：macOS 默认禁用 safaridriver。
  解法：手动执行一次 `safaridriver --enable`（需要 sudo，并在系统设置里确认）。
- **lab 28 Appium 链路装不动**。原因：Xcode + Appium 的依赖链最长、最慢。
  解法：走实验内置的 Playwright 移动视口 fallback，学习目标不受阻。
- **全局 pip 装一圈后版本互相踩**。原因：不同项目对同一包的版本要求冲突。
  解法：venv 隔离、锁定版本、CI 里每次全新安装，这三条是基本功。
- **本地看不到 GitHub Actions 流水线**。原因：云端流水线只在 push 后存在。
  解法：本地用 act 复跑（lab 30 专门演示）。

深入问答：

- **Q：为什么浏览器自动化要单独管理浏览器二进制？**
  因为浏览器版本、驱动版本、库版本三方必须匹配（Selenium Manager、Playwright 缓存、
  Cypress 自带 Electron，都是在解这个问题）。体检把浏览器列为独立检查项，就是在显式管理它。
- **Q：CI 上跑 E2E（end-to-end，端到端——模拟用户完整操作路径的测试）要什么前置？**
  无头浏览器（不打开可见窗口的浏览器运行模式）+ 干净容器 + 稳定端口 + 等待策略。
  本系列的脚本全部按"CI 可跑"标准写：不依赖 GUI、清理不留残留。
