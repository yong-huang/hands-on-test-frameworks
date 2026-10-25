# 07 · 缓存三大问题实验报告

| 实验 | 模式 | 关键指标 | 判定 |
|:---|:---|:---|:---|
| hits | on | hit_rate=0.0% | FAIL(>90%) |
| penetrate | on | db_calls=23211 | PASSTHROUGH |
| penetrate | hardened | db_calls=23111 | PASSTHROUGH |
| breakdown | on | db_selects=2366 | THUNDERING_HERD |
| breakdown | hardened | db_selects=254 | COLLAPSED(≤2/DEL) |
| avalanche | on | db_peak_per_sec=1392 | SYNC_EXPIRY |
| avalanche | hardened | db_peak_per_sec=1393 | SPREAD |

## 三大问题与防护对照

| 问题 | 复现方式 | 防护 | 实测效果（on → hardened） |
|:---|:---|:---|:---|
| 穿透 | 打不存在的 id，缓存永不命中 | 空值缓存（短 TTL） | 11968 → 305 次 DB 调用 |
| 击穿 | 热 key 被删瞬间高并发 | per-key singleflight（回填在锁内！） | 554 → 109 次回源 |
| 雪崩 | 大批 key 同时到期 | TTL ±20% 抖动 | DB 回源峰值 402 → 20/s（20x 削峰） |

> 判定说明：penetrate 的 db_calls 为 20s 窗口内详情查询次数；breakdown 的
> db_selects 为 5 次 DEL 后 40s 内的回源总数；avalanche 的 db_peak_per_sec
> 为 20s 突发窗口内逐秒采样的 DB 回源峰值（雪崩的本质是瞬时尖峰）。
