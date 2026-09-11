# 29 · 无障碍与安全基线：axe 扫 WCAG，ZAP 扫 OWASP，全部门禁化

> 上线前总有两类"重要但不紧急"的事：无障碍与安全。axe-core 按 WCAG 规则
> 扫 DOM，ZAP 以攻击者视角扫 HTTP——本篇把两者做成可一键回归的门禁，
> 并真实完成一次"扫出 critical → 修 SUT → 复扫变绿"的闭环。

## 1. 为什么需要它

- 无障碍违例和安全漏洞都是"单点修复成本低、线上事故成本高"的典型。
- 基线扫描的价值在**回归**：今天修掉的，明天不许再犯。

## 2. 总览：双扫描器与产出流

<!-- 图: images/a11y_security.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/labs/29_a11y_security/images/a11y_security.html)
> （或本地打开 [`images/a11y_security.html`](images/a11y_security.html)）。

axe 注入页面规则扫 DOM（critical/serious 必须 = 0）；
ZAP 以 docker 基线模式被动扫 + 爬虫（WARN 清单入 docs，FAIL 才拦）。

## 3. 快速开始

```bash
./a11y_security.sh          # axe 门禁 + ZAP 基线扫描 + 报告落 docs/
open docs/zap_report.html   # 60 PASS / 7 WARN（安全头缺失）
cat docs/axe_before_after.md
```

## 4. 核心概念

### 4.1 axe 闭环：扫出真问题，修到绿（本实验实测）

首扫 SUT 抓到 **critical** 违例 `label`（表单只有 placeholder 无关联 label，
涉及下单页 4 个输入框和登录页 2 个）。修复：补 `aria-label`。
复扫：三页面 critical/serious 全清零。完整前后对比在 `docs/axe_before_after.md`。

### 4.2 门禁断言的度

`impact ∈ {critical, serious}` 必须为空——moderate 及以下进清单不拦提交。
**门禁过严会被人绕过，过宽等于没有**；critical/serious 是社区常用平衡点。

### 4.3 ZAP 基线扫描的退出码语义

`zap-baseline.py -I`：WARN 不影响退出码、FAIL 才非 0——基线扫描定位是
"风险清单生成器"而不是拦截器。本机实测 60 PASS / 7 WARN（安全响应头缺失），
报告 HTML 落 `docs/`。修安全头属于 SUT 加固，进 backlog 而非阻塞本实验。

### 4.4 易错点

- axe 在动态渲染页面要等内容稳定再扫，否则扫了个寂寞；
- ZAP 容器访问宿主机 SUT 依然要用 `host.docker.internal`（lab 24 的坑重现）。

## 5. 关键命令

```python
report = Axe().run(page)                    # axe_playwright_python
violations = [v for v in report.response["violations"] if v["impact"] in ("critical", "serious")]
assert not violations
```

```bash
docker run --rm -v "$PWD/docs:/zap/wrk" -t zaproxy/zap-stable \
  zap-baseline.py -t http://host.docker.internal:8929/ -r zap_report.html -I
```

## 6. 文件结构

```
29_a11y_security/
├── README.md
├── a11y_security.sh             # SUT + 双扫描 + 报告
├── configs/pytest.ini
├── tests/test_a11y.py           # 三页面 axe 门禁
├── docs/
│   ├── axe_before_after.md      # 修复前后对比（实测）
│   └── zap_report.html          # ZAP 基线报告（60 PASS / 7 WARN）
└── images/
```

## 7. 深入要点

- **Q: a11y 自动化能替代人工测试吗？** 不能—— axe 覆盖约 30-40% 的 WCAG
  问题（规则可判定的部分），键盘导航/读屏体验必须人工；自动化管回归。
- **Q: ZAP active scan 和 baseline 的区别？** baseline 被动+爬虫、不打扰业务；
  active scan 会真实攻击（可能写坏数据）——只在隔离环境跑。
- **Q: 怎么防止"清单进 docs 就没人看"？** 清单进 issue tracker 带负责人，
  docs 只留快照；门禁拦新增，存量靠治理。

## 8. 总结

质量版图补上两块基线。下一篇 [30_local_ci](../30_local_ci/README.md)：
终极串联——1-29 全部进一条流水线。
