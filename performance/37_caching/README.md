# 37 · 缓存三大问题：穿透、击穿、雪崩，逐一复现逐一设防

> 靶场里的 Redis 弹药上膛了。给 shop 的详情接口装上 Cache-Aside（三档开关：
> `off` / `on` 裸缓存 / `hardened` 全防护），然后把三大问题**当实验做**——
> 每个问题都先在裸缓存上复现出数字，再切 hardened 档看防护生效。
> 最终成绩：命中率 97.6%、穿透 DB 调用 11968→305、击穿回源 554→109、
> 雪崩 DB 峰值 402→20/s（**20 倍削峰**）。

## 1. 为什么需要它

- 缓存是性能工程里唯一"不加硬件就能数量级提速"的手段，但它自带三种崩溃模式；
- 这三种模式的区别全在**失效的拓扑**：穿透是"查的东西不存在"，击穿是"一个
  热 key 失效"，雪崩是"一批 key 同时失效"——复现方法因此完全不同；
- 单飞（singleflight）有个经典陷阱：**回源后回填必须发生在锁内**，
  否则等锁者 double-check 时缓存还是空的，防护形同虚设（本实验真踩）。

## 2. 总览：三档开关，四组实验

<!-- 图: images/caching.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/performance/37_caching/images/caching.html)
> （或本地打开 [`images/caching.html`](images/caching.html)）。

k6 按实验切换打靶姿势（热点只读 / 不存在 id / 单 key 集火 / 预热后等过期），
shop 的 `CACHE_MODE` 在 on/hardened 间重建切换，DB 回源次数用
pg_stat_statements 差值逐秒取证。

## 3. 快速开始

```bash
./caching.sh all     # 七轮实验（on/hardened 交叉）→ docs/caching.md
./caching.sh clean   # 恢复 off 对照态
```

## 4. 核心概念

### 4.1 实测结果（本机数据，全部可复算）

| 实验 | on（裸缓存） | hardened（全防护） | 防护手段 |
|:---|:---|:---|:---|
| 命中率（热点只读 20VU×30s） | **97.6%** PASS | — | Cache-Aside 本身 |
| 穿透（20VU 打不存在 id） | 11,968 次 DB 调用全穿 | **305 次**，BLOCKED | 空值缓存（短 TTL） |
| 击穿（50VU 集火 + 5 次 DEL） | 554 次回源，雷鸣般群 | **109 次**，合并回源 | per-key singleflight |
| 雪崩（100 key 同批过期） | DB 峰值 **402/s** | **20/s**（20x 削峰） | TTL ±20% 抖动 |

### 4.2 三大问题的失效拓扑（一张表分清）

| | 失效的是什么 | 典型场景 | 防护 |
|:---|:---|:---|:---|
| 穿透 | 数据在缓存**和** DB 里都不存在 | 恶意扫描不存在的 id | 空值缓存 / 布隆过滤器 |
| 击穿 | **一个热 key** 到期 | 秒杀商品详情过期 | singleflight / 逻辑过期 |
| 雪崩 | **一大批 key** 同时到期 | 同批预置、同一时刻写入 | TTL 抖动 / 多级缓存 |

### 4.3 singleflight 的锁内回填（本实验真踩）

第一版防护：等锁 → double-check → 回源 → 释放锁 → **回填**。结果 hardened
反而更糟（DB 峰值 202/s > 裸缓存的 90/s）：等锁者在锁释放后 double-check，
但此刻前一个请求还没来得及回填，照样打 DB——锁只带来了串行化，没带来合并。
修复：**回源与回填都放进临界区**，等锁者 double-check 时必然命中。
写完并发防护代码，必须用击穿实验验证，眼睛看着数字降下来。

### 4.4 易错点

- **`redis.setex` 的单位是秒**——传成 `ttl*1000` 就是缓存 18 小时，
  永不过期，雪崩实验直接哑火（本实验踩过：三轮没信号才抓到）；
- **读写混合会拉低命中率**：下单写路径主动 DEL 缓存（Cache-Aside 的正确
  行为），命中率实验必须用只读场景，否则 97.6% 会变成 58%；
- **雪崩测的是瞬时峰值不是总量**：总量上 on/hardened 差不多（都会回源一遍），
  逐秒采样才能看出 402 vs 20 的削峰。

## 5. 关键参数

```python
# Cache-Aside 读路径（hardened 档）
cached, found = cache_get(key)          # miss 计数
with key_lock(key):                     # singleflight：同 key 并发合并
    cached, found = cache_get(key)      # double-check
    if not found:
        row = _load_product(pid)        # 回源
        cache_put(key, ..., CACHE_TTL)  # 回填（锁内！TTL ±20% 抖动）
```

## 6. 文件结构

```
37_caching/
├── README.md
├── caching.sh             # prereq/hits/penetrate/breakdown/avalanche/report/clean
├── gen_cache_report.py    # results 行 → docs/caching.md
├── reports/               # caching_results.txt + 各实验 JSON/样本（验收物）
├── docs/caching.md        # 实验报告
└── images/                # 图三件套
```

缓存层本体在 `../31_perf_baseline/shop/app/main.py`（CACHE_MODE 三档），
这是完整系统型清单的设计：靶场代码随实验生长。

## 7. 面试要点

- **Q: 穿透/击穿/雪崩的区别与对策？** 见 4.2 的失效拓扑表——记住三者的
  区别在"失效的东西是什么"，对策自然推出。
- **Q: singleflight 为什么要 double-check？** 等锁期间前一个请求可能已完成
  回填；不 double-check 会重复回源。且回填必须在锁内，否则 double-check
  形同虚设。
- **Q: 缓存与 DB 的一致性怎么保证？** 本实验用 Cache-Aside + 写路径删缓存：
  先更 DB 再删缓存，容忍短暂不一致；强一致要上订阅 binlog 的失效管道，
  或干脆接受 TTL 窗口内的旧读。
- **Q: 热点 key 还有别的防击穿手段吗？** 逻辑过期（不删、异步刷新）、
  永不过期 + 主动更新、多副本 key 打散——都是"把合并做进读路径"的变体。

## 8. 总结

四种姿势的施压换来四个干净的数字：97.6%、305、109、20/s。更重要的是
把 singleflight 的锁内回填这个陷阱亲手踩了一遍——**并发防护代码没有经过
击穿实验验证之前，都不能算写完**。下一篇项目 8「并发模型与容量调参」，
把 uvicorn workers 与连接池当矩阵变量，找靶场的最优工作点。
