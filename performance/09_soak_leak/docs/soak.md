# 09 · 浸泡测试与泄漏定位报告

- **泄漏注入（heap）**：RSS 19→22MB（Δ+2），goroutines 38→9（Δ-29）——单调上升，泄漏实锤
- **修复后（LEAK_MODE=off）**：RSS 14→19MB（Δ+5），goroutines 38→39（Δ+1）——尾部平台化，平稳

## heap 差分 top（正值 = 新增分配嫌疑犯）

```
File: shorturl
Type: alloc_space
Time: 2026-09-09 00:58:01 CST
Showing nodes accounting for 1199.93MB, 25.15% of 4771.17MB total
Dropped 56 nodes (cum <= 23.86MB)
      flat  flat%   sum%        cum   cum%
 1151.92MB 24.14% 24.14%  1151.92MB 24.14%  main.maybeLeak
   11.50MB  0.24% 24.38%    11.50MB  0.24%  github.com/prometheus/client_golang/prometheus/promhttp.labels
    9.50MB   0.2% 24.58%     9.50MB   0.2%  net/textproto.MIMEHeader.Set (inline)
       9MB  0.19% 24.77%        9MB  0.19%  net/textproto.readMIMEHeader
       8MB  0.17% 24.94%        8MB  0.17%  net/http.Header.Clone (inline)
    4.50MB 0.094% 25.03%       22MB  0.46%  net/http.(*conn).readRequest
       3MB 0.063% 25.10%       14MB  0.29%  net/http.readRequest
    1.50MB 0.031% 25.13%    21.01MB  0.44%  net/http.Redirect
       1MB 0.021% 25.15%        7MB  0.15%  github.com/prometheus/client_golang/prometheus/promhttp.newDelegator
         0     0% 25.15%        8MB  0.17%  github.com/prometheus/client_golang/prometheus/promhttp.(*responseWriterDelegator).WriteHeader
         0     0% 25.15%  1185.92MB 24.86%  github.com/prometheus/client_golang/prometheus/promhttp.InstrumentHandlerCounter.func1
         0     
```

## 判读

- 泄漏版（heap 模式）RSS 单调上升且不回落——短压测看不见，时间揭发；
- goroutine 模式看 go_goroutines 单调上升（每请求孵一个永不返回的 goroutine）；
- 修复版同配方曲线平稳即验收通过。
