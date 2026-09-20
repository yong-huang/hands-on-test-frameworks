# 22 · 安全左移门禁：SCA + SAST + DAST 三层拦在流水线上

> 安全不必是专家专属——三层扫描把最常见的风险拦在流水线上：**SCA 拦已知漏洞依赖**
>（CVE 库比对）、**SAST 拦危险代码模式**、**轻量 DAST 拦部署层低级失误**。实测：
> 基线 PASS；植入 requests==2.19.0 后门禁 FAIL 并点名 5 条 CVE；DAST 还揪出一个
> 真实发现——SUT 的 /admin.html 未登录即可访问。清单第 22/28 项。

## 1. 为什么需要它

- Log4Shell 式事故的共性：漏洞公布时没人知道自家依赖中招——SCA 把「CVE 公布」自动
  变成「工单产生」；
- 安全扫描的价值在**汇入门禁**：单独跑的扫描器只是报表，接上退出码才是防线；
- 三层的分工与局限要讲清楚（面试考体系不考工具名）。

## 2. 总览：核心机制一图看懂

![安全左移门禁](images/security_gate.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/architect/22_security_gate/images/security_gate.html)
> （或本地打开 [`images/security_gate.html`](images/security_gate.html)）。

心智模型一句话：**三个扫描器并行、一份门禁裁决**——SCA/SAST 有红线必拦；轻量 DAST
发现默认警告不拦（部署层问题由发布 checklist 兜底），阈值可加严。

## 3. 快速开始

```bash
cd architect/22_security_gate
./security_gate.sh apply     # 装 pip-audit/bandit + 起 SUT
./security_gate.sh observe   # 基线 PASS → 植入 CVE 依赖 → FAIL 点名 → DAST 发现
./security_gate.sh clean
```

实测输出（节选）：

```
① 基线：裁决 ✅ PASS
   L2 SAST：高危 0 项 / 中危 2 项
   L3 DAST：⚠️ /admin.html 未登录即可访问（HTTP 200，无鉴权跳转）——真实发现
② 植入 requests==2.19.0 后：裁决 ❌ FAIL（退出码 1）
   - requests: CVE-2018-18074（修复 2.20.0）
   - requests: CVE-2023-32681（修复 2.31.0）
   - requests: CVE-2024-35195 / CVE-2024-47081 / CVE-2026-25645 …
```

## 4. 核心概念

### 4.1 三层各自看得见什么
SCA 看依赖清单（pip-audit 对 CVE/GHSA 库）；SAST 看代码模式（bandit 规则：eval/
弱随机/硬编码密码）；轻量 DAST 看**运行中的真实行为**（安全响应头、未鉴权页面、
目录列表）——本实验 DAST 抓到的 /admin.html 裸奔就是前两层永远看不见的部署层问题。

### 4.2 拦截分级
SCA 有 CVE → 必拦（红线）；SAST 高危 → 必拦，中危记账；DAST 发现 → 警告+工单。
分级响应是安全门禁能活下去的关键——一把尺子量所有发现，两周后就会被整体豁免。

### 4.3 扫描器崩溃 ≠ 无漏洞
pip-audit 崩溃/断网时，fail-safe 语义必须是 **FAIL（SCANNER-FAILED）**而不是 PASS——
「扫不了」按「无问题」处理是安全门禁最危险的反模式。

## 5. 关键设计

| 设计 | 为什么 | 坑 |
|:---|:---|:---|
| 依赖清单精确 pin | pip-audit --no-deps 只接受精确版本（`>=` 范围直接报错） | 扫描对象版本漂移会让结果失真 |
| CVE 去重（别名取 CVE- 前缀） | GHSA/CVE 双编号同漏洞会刷屏 | 重复告警加速告警疲劳 |
| DAST 默认不拦 | 部署层问题归属发布流程 | 若接拦，需要豁免流程配套（项目 24） |
| 扫描器崩溃=FAIL | 扫不了 ≠ 没问题 | try/except 吞异常返回 PASS 是最危险的反模式 |

## 6. 文件结构

```
architect/22_security_gate/
├── README.md
├── security_gate.sh           # apply(装工具+起SUT) → observe(基线/植入CVE) → clean
├── secgate.py                 # 三层扫描 + 汇总裁决（约 140 行）
├── configs/requirements_scan.txt  # 精确 pin 的扫描对象
└── images/                    # 图三件套
```

## 7. 深入要点

**Q1：SAST/DAST/SCA 之外还有什么？** IaC 扫描（terraform/k8s manifest 的错误配置）、
密钥扫描（git 历史里的 API key，gitleaks）、容器镜像扫描（trivy，本实验 16 的镜像
可直接接）。安全左移是谱系，选型按风险排序接入，不必一次全上。

**Q2：误报太多怎么办？** 三步：基线管理（存量问题登记豁免，只对新增量零容忍）、
规则分级（高危拦/中危记账/低危忽略）、定期回收豁免（「临时豁免」要有过期时间）。
豁免流程与项目 24 的覆盖率豁免状态机同构。

**Q3：DAST 会不会把测试环境打挂？** 会——所以生产级 DAST 要限速、白名单路径、
避开数据写接口。本实验的轻量 DAST 只做只读探测（GET + 响应头检查），这是「轻量」
的全部含义：够拦低级失误，不做攻击模拟。

**Q4：为什么 SAST 对 SUT 只报了 2 个中危？** SUT 代码量小且干净——这恰是左移的
证明：安全问题在代码评审阶段就该被拦，SAST 是兜底而非主力。中危项（如 assert 用
于业务判断）要人工 triage 而不是自动拦。

**Q5：安全门禁和项目 3 质量门禁什么关系？** 同一个引擎（项目 3 的规则模型）不同
数据源：安全扫描结果作为 adapter 接入即可复用裁决与报告——本实验独立跑是为了
演示三层扫描器本身；平台化合并是自然演进。

## 8. 总结

基线 PASS、植入 CVE 五条点名 FAIL、DAST 揪出 admin 裸奔——安全从「专家的专项」
变成「流水线的常规关卡」。至此非功能四件套（性能/混沌/安全/度量入口）齐三缺一，
下一篇是清单项目 23「质量度量体系与看板」：把前面所有项目的产物变成六个可抽查的
指标——你们团队质量怎么度量，终于有一页纸的答案。
