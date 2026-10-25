# 13 · 依赖 CVE 与密钥扫描：供应链左移双闸

> 依赖里的漏洞和提交进仓库的密钥有一个共同点：都不是你「写」的，却会在你
> 家里爆。本实验用 pip-audit + gitleaks 建两道闸：钉住旧版 requests 的靶场
> 被 pip-audit 报出 CVE-2018-18074 等 38 条已知漏洞（退出码 1）、干净基线
> 零告警；埋了假钥匙的靶场被 gitleaks 报红 2 处、干净对照零告警——一条
> `./scan.sh` 全部复现并留档。

## Background

之前的做法：依赖装完不看（`requirements.txt` 三年不动），密钥写进代码
「先跑通再说」，供应链完全是黑箱。

痛点的核心是**两类资产都是「写一次、活很久」**：一个 2018 年的 requests
漏洞只要版本钉着就一直在；一把提交进 git 的钥匙哪怕后来删掉也留在历史里。
它们在项目 1 的漏斗里位于最右端——生产阶段才炸，代价最高。

本实验把两道闸左移到提交与构建阶段：SCA（Software Composition Analysis，
软件组成分析——把依赖版本对已知漏洞库比对）用 pip-audit，密钥扫描用
gitleaks，四项验收一条命令复现。

## What

供应链左移双闸是两个互补的自动检查：依赖 CVE（Common Vulnerabilities and
Exposures，公开漏洞统一编号——每个已公布的漏洞有一个全球唯一编号）扫描把
依赖版本对漏洞库比对（版本号即护照，漏洞库即观察名单）。

密钥扫描按模式与熵值（字符串随机程度——真密钥近乎随机长串，远高于普通
单词）找提交进代码的凭据（X 光看行李的形状）。

但和海关不同的是，观察名单只覆盖「已公布」的漏洞（零日不归它管），X 光
也只看「形状」——变量名无关的真密钥（项目 12 的埋点 5 同款问题）会漏，
所以两道闸都要定期更新规则库并接受盲区。

工具与四项验收的对应：

| 工具 | 靶场（预期红） | 干净对照（预期绿） |
|:--|:--|:--|
| pip-audit -s osv | requests==2.19.1 → CVE-2018-18074 等，exit 1 | requests==2.33.0 → exit 0 |
| gitleaks（默认规则） | 假钥匙靶场 → 命中 2 处，exit 1 | 环境变量读取 → exit 0 |

![供应链双闸：依赖靶场与密钥靶场各配干净对照，一条命令复现](images/supply_chain.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/shiftleft/13_supply_chain/images/supply_chain.html)
> （或本地打开 [`images/supply_chain.html`](images/supply_chain.html)）。
> 四条验收路径两两配对：每个靶场都有一份同构的干净对照，红绿由退出码说话。

## When to Use

- 例行体检：CI 每周对全量依赖跑 pip-audit，PR 层对增量跑 gitleaks。
- 开源前强制检查：gitleaks 扫**完整 git 历史**（`--no-git` 去掉即扫历史），
  历史里的钥匙也算泄漏。
- 何时不用：离线环境跑 pip-audit 需缓存漏洞库；gitleaks 只看代码不看运行时。

同类方案对比：

| 方案 | 差异 | 什么时候选它 |
|:---|:---|:---|
| pip-audit（本实验） | 即装即用，OSV/PyPI 漏洞库 | Python 仓库例行审计 |
| dependabot/renovate | 直接提升级 PR，治理自动化 | 有升级预算的团队 |
| trivy/grype | 容器镜像层扫描 | 镜像交付物 |

## Quick Start

前置：仓库根 `.venv` 已装 pip-audit（缺则 `pip install pip-audit`）、
gitleaks 在 PATH（缺则 `brew install gitleaks`；apply 步自检并补装）；
pip-audit 查漏洞库需联网。一条命令复现全部四项验收：

```bash
./scan.sh   # apply → observe（①②③④四段）→ clean
```

四段输出与退出码（每段留档 JSON/文本；注意结尾 clean 会删掉 reports/，
想保留留档请分步跑 `./scan.sh apply` 与 `./scan.sh observe`）：

```text
  ⛔ 退出码 1（非零即为红）；CVE 编号样例：CVE-2018-18074 CVE-2018-20060 CVE-2018-25091 CVE-2019-11236
  ✅ 退出码 0，无已知漏洞
  ⛔ 退出码 1（非零即为红）；gitleaks 命中 2 处泄漏
  ✅ 退出码 0，零告警
```

汇总留档（reports/acceptance_summary.txt）：

```text
① CVE 靶场退出码 1（非零即红），CVE 编号样例：CVE-2018-18074 …
② 干净依赖基线退出码 0（应为 0）
③ gitleaks 靶场退出码 1（非零即红），命中 2 处
④ 干净密钥对照退出码 0（应为 0）
```

诚实预期：① 靶场的 38 条漏洞来自 requests 2.19.1 的传递依赖（urllib3 1.23
占大头）——钉一个旧版本带进来的远不止一个包；③ 靶场的红来自 generic-api-key
与 github-pat 两条规则，裸 AKIA 串在 8.30 默认规则下不告警（见 Pitfalls）。

## How It Works

**pip-audit 的两个开关缺一不可**：`-s osv` 换 OSV 漏洞库（默认 PyPI 源只报
PYSEC 编号），`--aliases on` 把 CVE 别名列出来——「具体 CVE 编号」即此组合。
退出码内建：有漏洞即 1，干净即 0，门禁直接可用。

**gitleaks 的形状匹配**：`--no-git` 扫文件而非 git 历史（去掉即扫历史）；
默认规则含 github-pat（`ghp_` + 36 位字符）、generic-api-key（key/token 命名
加高熵字面量赋值）等数百条。

`--redact` 让报告里的密钥值打码——留档文件本身不泄漏。

**干净与脏是同构对照**：requirements 只差一个版本号，密钥代码只差「字面量
vs 环境变量」——对照组证明退出码差异全部来自被检内容，不是工具抖动。

```bash
# ① 靶场红：报 CVE 且退出码非零
"$BIN/pip-audit" -r fixtures/requirements_vuln.txt -s osv --aliases on
# ③ 靶场红：默认规则命中 2 处
gitleaks detect --no-git --source secrets --report-format json --report-path "$OUT/gitleaks.json" --redact
```

## Pitfalls & Q&A

常见故障与解法：

- **`$vcode` 紧跟全角字符时 bash 报 unbound variable**：bash 3.2 把紧跟
  `$var` 的多字节字节流并进变量名解析。所有 `$var` 一律写成 `${var}`——
  本实验两种写法各出现过一次，只有带花括号的能跑。
- **多轮补丁会把脚本字节改脏**：孤儿引号（`tr '\n' ' ''` 里的第三个 `'`）
  吞掉后续整行，报错行号还指不到真相。补丁匹配不上就整文件重写，别做
  第 N 次手术。
- **gitleaks 默认规则不告警裸 AKIA**：8.30 的默认规则集对 AWS 文档示例
  形态无告警（且官方示例密钥在白名单）。靶场用「实测会命中」的形态
  （ghp_ 令牌、secret 赋值行），AKIA 行保留作盲区教学。

Q&A：

- **CVE 与 PYSEC 编号什么关系？** 同一漏洞的不同编号体系：默认 PyPI 源报
  PYSEC，OSV 源加 `--aliases on` 会把 CVE 别名列出来——都是具体编号，
  追溯时以 CVE 为准。
- **干净基线会过期吗？** 会：本实验选钉时 requests 2.32.4 就已有 2026 年
  新 CVE（CVE-2026-25645），2.33.0 才是真零点。基线红了先升级钉子，
  确需豁免就走文档化豁免流程。
- **和项目 11/12 什么关系？** 三道门禁分域：11 管代码风格与类型、12 管
  代码漏洞模式、13 管供应链（依赖与凭据）；14 的 pre-commit 链把它们串
  成本地秒级组合拳。
