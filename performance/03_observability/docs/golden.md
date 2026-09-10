# 03 · 黄金信号观测报告

- 生成时间：2026-09-08T01:21:55
- 证据口径：压测后 2 分钟窗口的 PromQL 查询值（非截图，可复算）

| 信号 | 实测值 |
|:---|:---|
| shop RPS | =121.152 |
| shorturl RPS | =0.000 |
| shop P95(s) | =4.384 |
| shorturl P95(s) | =10.000 |
| shop 进程CPU(核) | shop=1.062 |
| shorturl 进程CPU(核) | shorturl=0.000 |
| shop RSS(MB) | shop=82.883 |
| shorturl RSS(MB) | shorturl=19.480 |
| PG 事务/s | postgres=0.035; postgres=126.702; postgres=0.696; postgres=0.000; postgres=0.035 |

## 告警触发证据

- HighP95Latency 在压测期间触发：是
- 复核命令：`curl -s 'http://localhost:19090/api/v1/alerts' | python3 -m json.tool`
  压测期间执行可见 state=fireing；SLO=500ms（configs/alerts.yml）

## 联动解读

压同一时刻的四条曲线（流量↑ → 延迟↑ → 进程CPU↑ → RSS 平稳）
在 Grafana『黄金信号 · 双 SUT』面板同屏可见（http://localhost:13000）。
