# 11 · 设备与仿真矩阵：一套用例，六种世界

> "桌面端没问题"不等于"手机上没问题"。本实验把 pw-store 的响应式与主题
> 放进六组合矩阵（桌面/iPhone/Pixel × 明/暗主题）里跑，一轮 36 个执行；
> 再用 locale、timezone、offline、触屏仿真验证"环境不同，行为不同"。

## Background

设备与环境的差异是真实的产品缺陷来源：375px 视口横向溢出、深色模式下文字看不清、
英文环境出现中文文案、跨时区的日期计算偏了一天。这些问题的共同点是——
开发机（一台 Mac、一个时区、一种语言）永远复现不出来。

仿真是对此的系统解法：浏览器上下文的各项环境参数（视口、UA、语言、时区、
主题偏好、网络连通性）全部可以由测试声明。

Playwright 的 projects 把这些参数打包成模板，一个声明 = 一类环境，
用例零改动地在所有环境各跑一遍。

## What

project（上下文模板）是矩阵的乘数：本实验 3 设备 × 2 主题 = 6 个 project，
`npx playwright test` 自动展开为"用例数 × 6"的执行。

仿真是矩阵里的单项开关：`locale`、`timezoneId`、`colorScheme`、`hasTouch`、
`setOffline` 各管一个维度。

可以把 projects 想成拍照的六组滤镜参数：同一处风景（用例），
每组滤镜拍一张，谁家照片过曝（断言失败）就说明那组参数下有问题。
但和滤镜不同，矩阵里的"参数"是真的——iPhone project 里的浏览器真的具备触摸
事件、真的只有 390px 宽，不是贴图模拟。

![设备 × 主题矩阵与仿真注入](images/matrix.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/playwright/11_pw_matrix/images/matrix.html)
> （或本地打开 [`images/matrix.html`](images/matrix.html)）。
> 下方"仿真选项"节点经 `test.use()` 局部注入——project 定底色，用例可覆盖单项。

## When to Use

| 场景 | 矩阵优先 | 单环境 + 手测 |
|:---|:---|:---|
| 响应式布局回归 | ✅ 视口矩阵自动覆盖 | 每次改版手开模拟器 |
| 主题（明/暗）双支持 | ✅ colorScheme 维度 | 深色模式长期无人看 |
| 多语言产品文案 | ✅ locale 维度 | 切系统语言重启浏览器 |
| 与设备硬件强相关的功能（相机/推送） | ❌ 仿真到不了 | 真机实验室 |
| 性能类断言（帧率/内存） | ⚠️ 环境噪声大 | 受控单环境 |

判断口径：**凡是"浏览器上下文可枚举"的差异，矩阵都是正解**；
到不了的能力（硬件外设、真实弱网）不硬仿，交给真机与网络损伤仪。

## Quick Start

```bash
cd playwright/11_pw_matrix
./matrix.sh          # apply 体检 → observe 六矩阵 + 深色抽查 + 仿真三件套 → clean
```

observe ① 六个 project 全跑，同一套响应式用例 6 组合全绿：

```
=====> [observe] ① 六 project 全跑（3 设备 × 明暗，同一套响应式用例）
  36 passed (7.5s)
```

observe ③ 是仿真三件套（timezone / offline / 触屏各一条 × 6 project）：

```
=====> [observe] ③ 仿真三件套：timezone / offline / 触屏
  18 passed (3.7s)
```

验收方式：矩阵 36 passed。深色 project 的背景亮度断言
（body 计算 `backgroundColor` 的 R 分量 < 64）通过，浅色 project 断言浅色背景，
同一断言逻辑在两种主题下各自成立；en-US 仿真下订单 Tab 文案为 Orders。

## How It Works

**project 是上下文模板的命名。** 每个 project 的 use 里铺开一份设备描述
（`devices['iPhone 13']` 内置视口 390×844、UA、hasTouch 等）加主题覆盖。

用例对 project 无感知——`testInfo.project.name` 只在需要分支逻辑时读取
（本实验的深色断言用它判断当前主题档）。

**深色断言验的是"系统偏好被应用响应"。** pw-store 的样式表带
`@media (prefers-color-scheme: dark)` 段，`colorScheme: 'dark'` 仿真的
就是这条媒体查询的命中条件。

断言读的是 `getComputedStyle` 的实际渲染值而非配置值——
仿真生效 + 应用响应，两层都过才算深色支持成立。

**locale 仿真的落点在应用代码。** 浏览器语言设为 en-US 只改变
`navigator.language`；pw-store 的初始语言逻辑读这个值决定中英文。

这提醒我们：仿真能改变环境，但应用必须"读环境"才有可断言的行为差异——
硬编码中文的应用在 locale 矩阵里只会得到 6 份一样的绿。

**offline 是状态开关而非一次性参数。** `context.setOffline(true)` 随时切换，
恢复也随时——所以本实验的断言是三段式：断网时 fetch 失败 → 恢复后 fetch 成功。

它测的是应用对网络状态的响应路径，比"截图一张离线页面"真实得多。

## Pitfalls & Q&A

**Q：六个 project 全跑，时间成本怎么算？**
本轮 36 执行 7.5 秒（workers=2 并行摊薄）。矩阵的成本是线性乘法，
收益是缺陷覆盖的非线性提升——移动端布局事故基本只有真视口能暴露。
CI 资源紧张时的折中：PR 上跑桌面 + 一个移动 project，夜间全矩阵。

**Q：`test.use({ locale: 'en-US' })` 和 project 里的 locale 什么关系？**
test.use 是用例级覆盖，优先级高于 project 默认值。

想让某条用例额外验证英文环境就用 test.use，不必单开 project；
整个维度都重要时（如主题）才升级成 project 维度。

**Q：深色断言为什么读 R 分量而不做视觉比对？**
视觉基线（lab 06）按 project 分文件后深色也能做，但本实验关心的是
"主题是否生效"这个布尔事实——读计算样式的背景分量更直接、更不易碎。
工具选最贴近断言语义的：值断言优先于像素断言。

**Q：timezone 仿真会影响哪些断言？**
所有依赖本地时间的展示与计算：日期格式、倒计时、"今天"的边界。
pw-store 没有时间展示所以只演示偏移值；真实项目里跨时区团队
（如订单创建时间显示）应把 timezone 矩阵当常规项。

**Q：offline 仿真和 lab 05 的 abort 注入有什么区别？**
`setOffline` 切断上下文的所有网络（物理层），`route.abort` 按模式拦截
（应用层）。前者测"完全离线"的产品行为，后者测"特定接口失败"的降级路径。
两者互补：离线是状态，注入是事件。
