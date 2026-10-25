# 07 · JavaScript 执行与懒加载

## Background

execute_script 是 Selenium 的「后门」：能滚动、能注入、能绕过一切——但后门走多了，
真实用户路径就没人测了。本实验练的是分寸：什么时候必须用 JS（懒加载滚动、元素入视口），
什么时候用它反而测了个寂寞（直接改 value 绕过事件）。

## What

- 懒加载全载：滚动到底 → 等卡片增长 → 直至 30 件全部出现且「加载完成」提示可见
- scrollIntoView：把第 25 张卡片带进视口中心，用 getBoundingClientRect 断言在视口内
- **事件陷阱实测**：券码字段走「input 事件 → 状态」同步——
  JS 直改 value 后提交，服务端读到空串；sendKeys 后提交，读到正确券码
- 靶场顺带修了一个真实懒加载缺陷：大屏首屏填不满时用户无路可滚，加载卡死（已加兜底续载）

## When to Use

- 无限滚动/懒加载页面的全量断言
- 需要把视口外元素带入可视区再交互的场景
- 判断「这个字段的事件链路」是否真的被触发

## Quick Start

```bash
cd selenium/07_js_lazyload
./07_js_lazyload.sh            # 3 passed
```

实测输出（2026-10-26，节选）：

```text
JS 直改 value → 服务端读到的券码: ''（空——状态没同步）
sendKeys       → 服务端读到的券码: 'SELENIUM500'（事件已同步）
3 passed in 9.97s
```

## How It Works

- `execute_script("window.scrollTo(0, document.body.scrollHeight)")` 触发滚动事件 → 页面自己拉下一页
- `arguments[0]` 传 WebElement 进脚本；返回值经 JSON 序列化回 Python
- 事件陷阱机理：JS 赋值不触发 `input` 事件 → 走事件同步的字段停留在旧值；
  `sendKeys` 是真实键击，事件链完整

## Pitfalls & Q&A

- **坑：JS 直改 value 当作"填好了"**——依赖事件同步的表单里服务端读不到（本实验实测复现）；
  项目 04 的日期字段用「JS 设值 + 派发 change」正是这个原因：补派事件才完整
- **坑：二次提交读回显**——echo 区已可见，等待立刻返回，读到的是上一轮旧内容；
  解法是页面带提交序号（data-seq），自动化等「新一轮」再读
- **Q：滚动到底了为什么不加载？** 首屏没填满时页面不可滚、scroll 事件不触发——先修站的 UX（兜底续载），再谈自动化
