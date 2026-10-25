# 02 · 八种定位策略实战

## Background

定位器是自动化测试的「地基材料」：页面一改版，烂定位器成片塌方，好定位器岿然不动。
本实验在带病靶场上把 8 种定位策略逐一打实，并产出一张可复核的健壮性打分表，
让「为什么 XPath 只配待在对比实验里」变成有数据的结论。

## What

- 首页元素上逐一验证 7 种策略：id / class name / css / tag name / link text / partial link text / 相对定位器
- XPath 单独一条对比用例（能用但主套件不采用）
- 三层 iframe 内的购买按钮用 ≥6 种策略命中（id / css / xpath / tag name / class name / relative）
- 产物：`reports/locator_scores.csv`（元素 × 策略 × 实测命中数 × 健壮性主观分）

## When to Use

- 新页面写用例前选定位器策略时，拿打分表当参考
- 评审他人用例时，用「XPath 只在对比实验出现」当硬规则

## Quick Start

```bash
cd selenium/02_locators
./02_locators.sh            # apply → observe（跑 4 条用例 + 打印 CSV 头）→ clean
```

实测输出（2026-10-26，节选）：

```text
4 passed in 12.51s
element,strategy,hits,robustness_score
秒杀横幅,id,1,5
商品卡,class_name,10,2
```

## How It Works

- 相对定位器：`locate_with(By.X, "值").below({By.CSS_SELECTOR: "#锚"})`——**锚必须用 `{By: 值}` 字典形式**
- 打分口径（主观分 1-5，改版存活率）：id 5 ＞ relative/css 4 ＞ link 文本 3 ＞ class name 2 ＞ tag name/XPath 1

## Pitfalls & Q&A

- **坑：相对定位器的锚写成元组 `(By.ID, "x")`** → chromedriver 上是神秘崩溃
  `unknown error: call function result missing int 'status'`，geckodriver 上才是直白的
  `Unsupported locator strategy: 0`。字典形式 `{By.ID: "x"}` 三浏览器全通
- **坑：锚元素不可见**（隐藏或零尺寸空 span）同样触发上面的神秘崩溃——相对定位按可见性过滤，锚自己必须可见
- **Q：为什么 iframe 里的按钮也要练定位？** 因为 `find_elements` 只在当前 frame 上下文找——先切对 frame，再谈策略
