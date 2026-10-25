// k6 压测脚本：100 VUs 打 BFF 的 /checkout（下游已 mock 化）
// 用法：k6 run --summary-export reports/summary_<tier>.json k6_checkout.js
import http from 'k6/http';

export const options = {
  vus: 100,
  duration: '15s',
};

export default function () {
  const res = http.post('http://127.0.0.1:9804/checkout',
    JSON.stringify({ order_id: `ORD-K6-${__VU}-${__ITER}`, amount: 42 }),
    { headers: { 'Content-Type': 'application/json' } });
  // 零错答断言交给脚本对 summary 的检查；这里不主动 fail 以保留原始分布
  if (res.status !== 200) {
    console.error(`unexpected status ${res.status}`);
  }
}
