# 08 · Actions 交互链

## Background

表单填值之外的真实交互——拖拽排序、hover 出菜单、Ctrl+S、画板涂鸦——都靠 W3C Actions
的低级输入事件流。它们没有 DOM 变化可断言，所以要借几何断言（坐标/矩形）和像素断言。

## What

- 靶场新增 `playground.html`：自实现 mouse 事件流的可拖拽件 + hover 二级菜单 + Ctrl+S 便签 + 涂鸦画布（带墨迹像素计数）
- 四条用例：拖入目标区（中心点矩形断言）、hover 菜单点击、Ctrl+S 拦截断言、画布 0 → >500 墨迹像素 → 清空归 0

## When to Use

- 可排序面板、看板拖卡、滑杆微调
- hover 才出现的菜单/气泡
- 签名板、画图类应用（对照 appium/07 手势像素断言的 Web 版）

## Quick Start

```bash
cd selenium/08_actions
./08_actions.sh            # 4 passed
```

实测输出（2026-10-26）：`4 passed in 4.47s`

## How It Works

- `ActionChains(driver)` 把动作串成队列，`perform()` 才执行：
  `click_and_hold(item).move_to_element(zone).release()` 一气呵成
- 像素断言走页面自己的 `getImageData` 计数（同源 canvas 可读），测试只读页面上报的数字，
  避免把截图拉回 Python 算像素

## Pitfalls & Q&A

- **坑：HTML5 原生 drag&drop 事件 ActionChains 驱不动**——`<elem draggable>` 走的是
  HTML5 DnD 协议，W3C Actions 的鼠标事件喂不进去；靶场用 mousedown/mousemove/mouseup
  自实现拖拽就是为可测性让路
- **坑：canvas 初始是"透明"不是"白色"**——像素统计要把 alpha=0 排除，否则首帧就是全图"墨迹"（实测 67200）
- **Q：mac 上 Ctrl+S 会被浏览器抢走吗？** 页面 `preventDefault()` 后不会；mac 用户习惯 Cmd，
  页面监听的是 `ctrlKey || metaKey`，测试用 CTRL 即可命中
