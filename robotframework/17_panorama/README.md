# 17 · 🏁 全景串联（Web + API + RPA 三合一）

## Background

收官：把三个面向的能力拼成一条流水线——**RPA 读 Excel（数据入口）→ API 批量建单
（造数最快路径）→ Web 逐笔支付（真实用户行为）→ API 复核 + 结果写回 Excel（留痕出口）**
→ rebot 合并三段出统一总报告。「学会」的最终形态是「可编排的交付物」。

## What

- 三段 .robot + 一条 sh 编排：
  - 段一（RPA+API）：xlsx 读单 10 行（2 非法捕获跳过）→ API 建单 8 笔 → 订单清单落盘 JSON
  - 段二（Web）：orders.html 逐笔查询并点击支付（读段一清单）
  - 段三（API）：终态复核全部 paid → 结果工作表写回 orders_result.xlsx
- rebot 合并三段 output.xml；总账校验「merged 总数 = 分段之和、fail=0」

## When to Use

- 批量业务的全景验收（Excel 导入 → 系统处理 → 结果回执）
- 多段流水线的 CI 编排样板（段间用文件清单衔接，失败可从任意段重跑）

## Quick Start

```bash
cd robotframework/17_panorama
./17_panorama.sh            # 五步闭环 ✅
```

实测输出（2026-10-27，节选）：

```text
总报告：3 条全绿；Excel 10 行 → 建单 8 笔 → 复核一致
✅ 全景串联：Excel → API → Web → 回写 → 合并 五步闭环
```

## How It Works

- 段间衔接用**文件契约**（order_ids.json）：段间无内存共享，任何一段可独立重跑
- 路径纪律：跨段产物统一放 reports/（${CURDIR}/reports/...），与 --outputdir 解耦
- 总账校验：merged 统计 = 分段统计之和（rebot 合并不增不减）

## Pitfalls & Q&A

- **坑：${OUTPUT_DIR} 是 robot 的 --outputdir**——三段各用独立 outputdir（seg1/seg2/seg3），
  ${OUTPUT_DIR} 随之漂移；跨段共享产物必须钉死绝对路径（${CURDIR}/reports/...）
- **Q：为什么不用一个 .robot 三个 Test Case？** 分段是为了「失败定位到段 + 可单段重跑」；
  合并报告保留分段视图，这恰是 CI 编排的常态
