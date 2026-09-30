# 06 · 视觉回归流水线：让"看起来变了"变成一条红用例

> 功能断言管"对不对"，视觉断言管"长没长歪"。本实验给 pw-store 建四条像素基线
> （登录页整页、订单页遮住动态区、表单元素级、慢加载表格终态），走完整生命周期：
> 生成基线 → 比对全绿 → 注入一条 CSS 变异看红 → 还原转绿 → 基线随代码入库。

## Background

功能断言的盲区在样式：一个 `margin` 写错、一个颜色改偏、响应式布局在窄屏下塌了——
DOM 结构没变、文本没变，所有 `expect` 都绿，但用户看到的页面已经不对了。
人工肉眼回归（改完样式挨个页面点一遍）慢且漏。

视觉回归（把"应然的像素"存成基线图，每次运行拿当前截图与基线逐像素比对）把
样式验收自动化。

Playwright 内置这套能力：`toHaveScreenshot` 断言 + 基线文件管理 +
diff 三联图（期望/实际/差异高亮）一体，不需要外挂第三方服务。

## What

视觉断言的执行模型：`expect(page).toHaveScreenshot('login-page.png')` 先截图，
再与 `tests/visual.spec.ts-snapshots/` 下的基线文件比对（文件名自动带上
project 与平台后缀），差异超过阈值即失败。

可以把基线图想成产品的"证件照"：每次运行给页面重新拍一张，与档案照比对。
比对有两层阈值——像素级的颜色距离（默认 0.2，抗锯齿的微色差不算不同）
和整图级的差异占比（本工程设 2%），两层都过才算"长得一样"。

但和证件照不同，比对的是布局与配色而非全部细节——动态数据区可以用
`mask` 遮住，让断言只盯结构。

![视觉基线生命周期：生成、比对、变红、更新入库](images/visual.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/playwright/06_pw_visual/images/visual.html)
> （或本地打开 [`images/visual.html`](images/visual.html)）。
> 图上两条虚线是两个回环：基线缺失时首跑自动写入；diff 确认为预期改动后更新基线再次复验。

## When to Use

| 场景 | 视觉回归 | 功能断言 |
|:---|:---|:---|
| 样式改动是否破坏页面结构 | ✅ 主战场 | ❌ DOM 没变就发现不了 |
| 组件库/设计系统升级的回归 | ✅ 一次跑全量基线 | 只能抽样人查 |
| 数据渲染是否正确（列表内容） | ⚠️ 需 mask 数据区，绕远 | ✅ 直接断言文本 |
| 交互逻辑（点击后发生了什么） | ❌ 管不了 | ✅ 主战场 |

判断口径：**视觉回归是功能断言的补充层**，管"长什么样"，不管"做什么"。
两者在同一套用例里共存，截图断言通常加在流程末尾。

## Quick Start

```bash
cd playwright/06_pw_visual
./visual.sh          # apply 体检 → observe 基线/比对/变异/还原 → clean
```

observe ① 检查基线目录，为空则 `--update-snapshots` 生成四张基线 png 并提示入库：

```
>>> 基线已生成：
login-page-chromium-darwin.png   orders-page-chromium-darwin.png
order-form-chromium-darwin.png   slow-table-chromium-darwin.png
>>> git 状态（基线 png 应作为入库文件出现）：
?? tests/visual.spec.ts-snapshots/
```

observe ③ 是核心演示——脚本往页面注入一条"改背景色"的 CSS 再跑比对：

```
=====> [observe] ③ 变异演示：注入一条改背景色的 CSS → 预期变红
>>> 变异被抓住（预期红）：
    Error: expect(page).toHaveScreenshot(expected) failed
  2 failed
>>> diff/actual/expected 三联图见 test-results/*-diff.png
```

随后 observe ④ 还原页面复跑，回到全绿。验收方式：`visual.sh all` 全流程走通
（绿 → 红 → 绿），基线 png 出现在 git status 里，clean 后基线目录原封不动。

## How It Works

**基线是入库资产，不是运行产物。** `tests/visual.spec.ts-snapshots/` 里的 png 随代码
提交，`clean` 特意不碰它。

改样式的工作流：先改代码 → 跑测试看 diff 三联图 → 确认改动符合设计 →
`--update-snapshots` 刷新基线 → 基线与代码同一个 commit 提交。
评审者能在 diff 里直接看到视觉变化，这是视觉回归最值钱的副作用。

**mask 让断言盯结构不盯数据。** 订单页里订单状态由服务端定时器持续演进、
连接徽标文本依赖建连时机——这些区域用 `mask: [locator]` 打上马赛克，
比对时被遮住。原则：**会随时间/数据变化的区域一律 mask**，否则基线永远在误报。

**截图时机决定稳定性。** 慢加载表格的截图断言放在 `toHaveCount(3)` 之后——
先等终态再截，spinner 永远不会入镜。

config 里的 `animations: 'disabled'` 冻结动画、`caret: 'hide'` 藏起输入光标，
消掉另外两个截图随机源。

**阈值有两层，缺一层都会误判。** 本实验实测：给页面加 2px 的整体位移，
比对照样全绿——位移在稀疏页面上只挪动边缘像素，差异占比不足 2%。

把背景色从 #f6f8fa 改成 #e8e8e8（每通道只差 13）也抓不住——差距低于
像素颜色距离阈值 0.2。换成大面积深色变异立刻满堂红。

**阈值是"感知相似度"的工程化表达，不是精确度承诺**——选阈值要拿真实变异校准，
不能拍脑袋。

## Pitfalls & Q&A

**Q：为什么只跑 chromium 一个 project？跨浏览器基线怎么办？**
基线数量 = 用例数 × 浏览器数 × 平台数，三浏览器起步就是 12 张基线，
且 WebKit 与 Chromium 的字体渲染必然有系统性差异。

本实验先单浏览器把流水线跑稳；扩矩阵时基线按 project 后缀自动分文件，
门槛只是仓库体积与维护意愿。

**Q：截图断言失败但看不出哪里变了？**
打开 HTML 报告（`npx playwright show-report`）或 `test-results/` 下的
`*-diff.png`：三联图把期望、实际、差异高亮（红黄色块）并排放在一起，
红色区域就是变化点。整页截图的 diff 通常一眼能定位到具体区块。

**Q：CI 上跑视觉用例和本机结果不一致？**
字体渲染随操作系统与字体版本变化。基线带平台后缀（`-darwin`）就是为了
把"谁生成的基线"钉死。

跨平台团队的做法是用 Docker 固定渲染环境，
或只在同一类 runner 上生成与比对基线。

**Q：为什么变异演示选"改背景色"而不是"挪 2px"？**
本实验第一版真用过 2px 位移——比对全绿，变异根本没被抓住（见 How It Works
的阈值分析）。这个"失败"保留成了教学内容：**阈值能不能抓住你的变异，
要在自己的页面上实测**。

能稳定抓住大面积换色后，如果想抓更细的位移，
把 `maxDiffPixelRatio` 调小并重校基线即可。

**Q：元素级截图和整页截图怎么选？**
盯组件用元素级（`expect(locator).toHaveScreenshot()`），一张基线一个组件，
页面其他区域的改动不会误伤；整页截图适合"门户页/落地页"这类整体布局验收。
本实验四条基线两种都有，diff 出问题时元素级的定位成本明显更低。
