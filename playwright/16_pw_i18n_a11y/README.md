# 16 · i18n 与无障碍：locale 矩阵、axe 扫描与纯键盘流程

> 有一部分用户永远不用鼠标，还有一部分用户看到的不是中文。本实验用 locale 仿真
> 跑双语文案矩阵，用 axe-core 扫描三页无障碍违规（critical/serious 门禁为零），
> 再用纯键盘（Tab + Enter，全程不碰鼠标）走完登录与下单。

## Background

国际化（i18n）与无障碍（a11y，accessibility）常被当作"上线前顺手做"的事，
但它们恰好是回归测试最擅长的两类问题：i18n 的缺陷是"某个 key 没翻译"，
机械、可枚举；a11y 的缺陷是"对比度差半档、按钮没有可访问名"，规则化、可扫描。

两者都适合做成自动门禁，而不是靠 code review 肉眼把关。

axe-core（Deque 公司开源的无障碍规则引擎）把 WCAG（Web Content Accessibility
Guidelines，WCAG，W3C 的无障碍指南）里可程序化的条款变成了 100+ 条规则，
注入页面扫描后给出违规清单与修复建议。

## What

本实验有两条互补的通路：locale 通路（浏览器语言 → 应用字典 → 界面文案）
与无障碍通路（渲染结果 → 无障碍树 → axe 规则判定）。前者测"说得对不对"，
后者测"能不能被辅助技术使用"。

可以把无障碍树想成页面的"口述版"：读屏软件念给用户听的正是它
（按钮叫什么、输入框配什么标签）。axe 扫描的就是这棵树加计算样式——
所以 axe 抓到的问题（比如对比度不足）是"读屏与低视力用户真实体验到的问题"，
不是形式主义检查。

![i18n 与无障碍的双通路：locale 到文案，渲染到无障碍树再到 axe](images/i18na11y.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/playwright/16_pw_i18n_a11y/images/i18na11y.html)
> （或本地打开 [`images/i18na11y.html`](images/i18na11y.html)）。
> 上排是 locale 通路，下排是无障碍通路；两条通路都在渲染页交汇。

## When to Use

| 检查 | 自动化程度 | 本实验做法 |
|:---|:---|:---|
| key 级文案缺失（双语矩阵） | ✅ 全自动 | locale 仿真 × 文案断言 |
| 对比度 / ARIA / 表单标签 | ✅ axe 规则扫描 | critical/serious 门禁 |
| 纯键盘可达性（焦点顺序） | ✅ keyboard API 逐步断言 | 登录 + 下单全键盘走完 |
| 读屏软件的实际朗读效果 | ⚠️ 无障碍树是代理指标 | 拿 NVDA/VoiceOver 抽查 |
| 文案是否"通顺得体" | ❌ 语义判断 | 人工评审 |

判断口径：**自动化管规则违规与机械矩阵，人管语义与体验**。
axe 的 moderate/minor 违规进 backlog 分级处理，critical/serious 当阻塞门禁。

## Quick Start

```bash
cd playwright/16_pw_i18n_a11y
./i18n_a11y.sh          # apply 体检 → observe 文案矩阵 + axe 扫描 + 键盘流程 → clean
```

observe ① 双语文案矩阵（中英各 2-3 条，含一次手动语言切换）：

```
  ✓  6 中文环境（zh-CN） › 登录页与导航使用中文文案
  ✓  8 英文环境（en-US） › 登录页与导航使用英文文案
  ✓ 10 英文环境（en-US） › 手动切换语言：en 初始环境 toggle 后整页换中文
```

observe ② axe 三页扫描 + 纯键盘流程。axe 的输出会打印**全部**违规细节
（含 moderate），只对 critical/serious 判红：

```
[axe:登录页] moderate region: 某些页面区域未用 landmark 包裹 (3 处)
  ✓  1 axe 扫描：登录页 critical/serious = 0
  ✓  4 纯键盘：Tab 走完登录 + 下单表单并提交成功
  10 passed (2.3s)
```

验收方式：三页 axe 扫描 critical/serious = 0；纯键盘用例全程无鼠标完成登录与下单；
焦点可见性断言通过。

变异实验：把 styles.css 里登录提示文字改回 #8b949e（对比度 3.1:1），
axe 扫描立刻变红——这是本实验真实抓到并修复过的缺陷。

## How It Works

**locale 仿真的断言对象是"渲染出的文案"。** `test.use({ locale })` 改变
`navigator.language`，pw-store 的初始语言逻辑读它选中文字典。

断言落到具体按钮/标签的可见文本（`登录 pw-store` vs `Sign in to pw-store`）。
每个 key 中英各断言一次，漏翻的 key 会在另一半矩阵里现出原形。

**axe 扫描的是"计算后的真实状态"。** AxeBuilder 注入 axe-core 脚本，
遍历 DOM 与无障碍树，用计算样式（不是 CSS 源码）判定对比度、可见性、
焦点可达性。

运行时动态生成的 UI 一样被覆盖——扫描时机放在页面加载完成后、
动态内容稳定后即可。

**门禁分级：critical/serious 红线，moderate 记账。** axe 给每个违规标 impact。
本实验的门禁只对 critical 与 serious 判零——登录提示文字对比度 3.1:1
被标 serious，当场加深到 4.7:1 修复。

moderate 的 landmark 类建议打印在案进 backlog。
一刀切全部为零会让门禁被低危噪声淹没，反而失去信号。

**纯键盘流程同时验证三件事。** Tab 的焦点顺序（DOM 顺序合理）、
可操作性（Enter 提交表单有效）、可达性终点（提交真的成功）。
`toBeFocused()` 逐步断言焦点落点，比"最后成功提交"单一断言多出
"中间哪一步焦点丢了"的定位能力。

## Pitfalls & Q&A

**Q：axe 报了 moderate 的 landmark 违规，为什么不当场修？**
landmark（region/main/nav 等语义分区）缺失影响的是读屏用户的导航效率，
属于渐进增强——修复成本与收益要排期权衡。

门禁分级的原则与 flaky 案底（lab 13）一致：红线收紧、灰线记账。
全部归零的理想态靠迭代逼近。

**Q：为什么切换语言的用例会写反方向？**
本实验实测踩过：en-US 初始环境下点 toggle，断言却写"切到英文"——
初始已是英文，切完是中文。locale 类用例的每个断言都要先问
"此刻环境是什么、切之前是什么"，双向切换最好成对书写互相印证。

**Q：axe 会不会误报？**
规则引擎有误报率（约 5-10%，多在 ARIA 用法类）。处理方式：
确认误报后用 `AxeBuilder.disableRules(['rule-id'])` 显式豁免并注释原因——
豁免要逐条留痕，不能整类关闭。本实验三页零豁免，违规都是真问题。

**Q：纯键盘用例里为什么有一处 click？**
`order-title.click()` 是"把焦点放到起点"的编排动作，不是被测交互——
键盘可达性断言的是从焦点出发的 Tab 链，起点需要确定性。

真实的纯键盘用户会一路 Tab 到这里（前面有导航按钮），那是另一条
更长的用例；两条都有价值，本实验取短平快的一条。

**Q：axe 扫描要挂在流水线哪个位置？**
与冒烟套件同级：每次 PR 全量跑三页扫描（本实验总量约 1 秒）。
它太便宜了，不值得做抽样或夜间档——无障碍回归的修复成本
随问题存续时间增长，门禁越早越省。
