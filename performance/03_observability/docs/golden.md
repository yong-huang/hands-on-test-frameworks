# 03 · 黄金信号观测报告

- 生成时间：2026-10-25T19:16:34
- 证据口径：压测后 2 分钟窗口的 PromQL 查询值（非截图，可复算）

| 信号 | 实测值 |
|:---|:---|
| shop RPS | =283.825 |
| shorturl RPS | =0.000 |
| shop P95(s) | =0.010 |
| shorturl P95(s) | =0.098 |
| shop 进程CPU(核) | shop=0.145 |
| shorturl 进程CPU(核) | shorturl=0.000 |
| shop RSS(MB) | shop=51.980 |
| shorturl RSS(MB) | shorturl=16.273 |
| PG 事务/s | postgres=0.035; postgres=263.100; postgres=0.696; postgres=0.000; postgres=0.035 |

## 告警触发证据

- HighP95Latency 在压测期间触发：是
- 复核命令：`curl -s 'http://localhost:19090/api/v1/alerts' | python3 -m json.tool`
  压测期间执行可见 state=fireing；SLO=500ms（configs/alerts.yml）

## 联动解读

压同一时刻的四条曲线（流量↑ → 延迟↑ → 进程CPU↑ → RSS 平稳）
在 Grafana『黄金信号 · 双 SUT』面板同屏可见（http://localhost:13000）。
