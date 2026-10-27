# 29 · 无障碍与安全基线：axe 扫 WCAG，ZAP 扫 OWASP，全部门禁化

> 上线前总有两类"重要但不紧急"的事：无障碍与安全。axe-core 按 WCAG 规则
> 扫 DOM，ZAP 以攻击者视角扫 HTTP——本实验把两者做成可一键回归的门禁，
> 并真实完成一次"扫出 critical → 修 SUT → 复扫变绿"的闭环。
> 读完本篇你能配置 a11y（accessibility 的缩写，指无障碍）门禁、读懂 ZAP
> 基线报告的退出码语义，
> 并理解两者的度怎么拿。

## Background

无障碍违例和安全漏洞是同一类问题：**单点修复成本低、线上事故成本高**——
一个缺 label 的输入框，屏幕阅读器用户整张表单填不了；一个缺失的安全响应头，
是整类中间人攻击的入口。它们还都容易被推迟："先上线，下个迭代补"——
没有自动回归，"下个迭代"永远不来。

基线扫描的价值在**回归**：今天修掉的，明天不许再犯。把扫描器接上门禁
（critical 违例 = 0，否则退出码非 0），"该做的事"就从备忘录变成了流水线闸门。

两个扫描器各管一层：axe-core 注入页面按 WCAG（Web 内容无障碍指南，
无障碍的国际标准）规则扫 DOM；ZAP（OWASP Zed Attack Proxy）以攻击者视角
扫 HTTP 层——被动收集 + 爬虫覆盖，产出风险清单。

## What

axe 是嵌入页面的无障碍规则引擎：在真实 DOM 上跑几十条 WCAG 规则，每条违例带影响等级（critical/serious/moderate/minor）与修复建议。

ZAP baseline 是安全基线扫描：被动代理 + 爬虫摸站，按 OWASP 规则（开放全球应用安全项目维护的十大风险清单）找配置类问题，WARN 进清单、FAIL 才拦。


可以把 axe 想成建筑的消防验收清单：逐条检查"安全出口标识挂了没"
（可判定的规则项），挂错就红牌。但和消防验收不同的是，它只覆盖
可规则判定的部分（约 30-40% 的 WCAG 问题）——键盘顺不顺手、读屏体验
好不好，必须人工测；自动化管回归，人工管体验。

ZAP baseline 则像物业的定期巡检：记录隐患出清单（WARN），真有危险品（FAIL）才报警。但和物业巡检不同的是，巡检清单可以慢慢修，ZAP 的 FAIL 会当场拉闸拦下发——WARN 进清单治理，FAIL 必须立即处理。

本机实测 60 PASS / 7 WARN（安全响应头缺失）——修安全头属于 SUT 加固，进 backlog 而非阻塞本实验。


## When to Use

典型场景：

- 组件/页面合并前的 a11y 门禁：critical/serious 违例为空才允许合入。
- 上线前的安全基线：ZAP baseline 报告归档，WARN 清单带负责人进 tracker。
- 无障碍整改闭环：首扫抓违例 → 修 → 复扫验证——本实验完整跑了一遍。

何时不用：active scan（ZAP 的主动攻击模式，可能写坏业务数据）绝不在
共享环境跑，只在隔离环境；规则无法判定的体验类问题（对比度边界、
读屏顺序）自动化给不了结论，安排人工评审。

## Quick Start

前置条件：labs/16 的 Playwright 浏览器就绪；ZAP 部分需要 Docker
（本机 Docker 未启动，ZAP 段以实验作者的实测报告为准——`docs/zap_report.html`
为历史实测产物）。

```bash
cd labs/29_a11y_security
./a11y_security.sh          # axe 门禁 + ZAP 基线扫描 + 报告落 docs/
open docs/zap_report.html   # 60 PASS / 7 WARN（安全头缺失）
cat docs/axe_before_after.md
```

axe 门禁用例的真实输出（2026-09-28 实测）：

```
...                                                                      [100%]
3 passed in 0.57s
```

修复前后对比（`docs/axe_before_after.md`，实验作者实测）：

- **修复前**：首扫 SUT 抓到 **critical** 违例 `label`——表单只有 placeholder
  无关联 label，涉及下单页 4 个输入框和登录页 2 个。
- **修复动作**：SUT 侧补 `aria-label`（6 个输入框）。
- **修复后**：三页面 critical/serious 全清零。

诚实预期：当前代码里 axe 门禁 3 条用例全绿（修复已完成）；
要复现"修复前红"，把 SUT 静态页的 `aria-label` 摘掉再跑即可
（`docs/axe_before_after.md` 里有复现命令）。ZAP 基线的 WARN 清单
（7 条安全响应头缺失）是已知 backlog，不是拦截项。

关键命令（这段在做什么：axe 门禁断言 + ZAP 基线扫描的入口）：

```python
report = Axe().run(page)                    # axe_playwright_python
violations = [v for v in report.response["violations"] if v["impact"] in ("critical", "serious")]
assert not violations
```

```bash
docker run --rm -v "$PWD/docs:/zap/wrk" -t zaproxy/zap-stable \
  zap-baseline.py -t http://host.docker.internal:8929/ -r zap_report.html -I
```

## How It Works

**axe 门禁的度**：`impact ∈ {critical, serious}` 必须为空——moderate 及以下进清单不拦提交。**门禁过严会被人绕过，过宽等于没有**；critical/serious是社区常用的平衡点。

断言之前要等内容稳定（动态渲染页面先 `expect` 等终态再扫，否则扫描落空——lab 17 的原则直接复用）。


**ZAP 的退出码语义**：`zap-baseline.py -I` 参数下 WARN 不影响退出码、
FAIL 才非 0——基线扫描的定位是"风险清单生成器"而不是拦截器。
容器访问宿主机 SUT 依然要用 `host.docker.internal`（lab 24 的坑重现）。

**闭环的完整链路**：首扫（红，抓到 6 处 critical `label` 违例）→
修复（SUT 静态页补 `aria-label`）→ 复扫（绿，三页面清零）→
前后对比落 `docs/`。**扫出真问题并修掉**是这个实验区别于"跑一下扫描器"
的关键——扫描器的价值在驱动修复，不在产出一堆没人看的报告。

**清单的治理**：WARN 清单进 issue tracker 带负责人，docs 只留快照；
门禁拦新增，存量靠治理——防止"清单进 docs 就没人看"。

## Pitfalls & Q&A

踩坑清单：

- **动态页面扫描落空**（内容还没渲染就扫完了）。现象：违例数比人工检查少得多。
  原因：异步内容还没渲染扫描就跑完了。解法：先等终态再扫。
- **门禁全等级拦截**。现象：moderate 违例天天红，团队开始跳过门禁。
  解法：只拦 critical/serious，其余进清单治理。
- **ZAP 打生产或共享环境**。现象：active scan 写坏数据。
  解法：baseline（被动+爬虫）用于日常；active 只在隔离环境。
- **ZAP 容器连不上 SUT**。现象：扫描目标不可达。
  解法：`host.docker.internal`（lab 24 同款坑）。**且 SUT 必须绑 0.0.0.0**——标准 Docker
  下 host-gateway 是网桥网关 IP，绑 127.0.0.1 的服务不接受来自网关的连接（本机 OrbStack
  会穿透 localhost 所以测不出，CI 实测必红，2026-10-27 踩坑）；另把 ZAP 输出落文件显式
  判定，别用 grep 掩码式管道——它会把镜像拉取失败静默成一行 "exit code 1"。

深入问答：

- **Q：a11y 自动化能替代人工测试吗？** 不能——axe 覆盖约 30-40% 的 WCAG
  问题（规则可判定的部分），键盘导航/读屏体验必须人工；自动化管回归。
- **Q：ZAP active scan 和 baseline 的区别？** baseline 被动+爬虫、不打扰业务；
  active scan 会真实攻击（可能写坏数据）——只在隔离环境跑。
- **Q：怎么防止"清单进 docs 就没人看"？** 清单进 issue tracker 带负责人，
  docs 只留快照；门禁拦新增，存量靠治理。
