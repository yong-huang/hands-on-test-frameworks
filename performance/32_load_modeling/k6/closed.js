import http from 'k6/http';
import { check, sleep } from 'k6';

// 封闭模型：VU 数量固定，收到响应后才发下一个请求（自节流）。
// VUS 由环境变量注入：VUS=10/50/100 各跑一轮，观察吞吐与 P95 随并发的变化
export const options = {
  vus: Number(__ENV.VUS || 10),
  duration: __ENV.DUR || '40s',
  summaryTrendStats: ['avg', 'med', 'p(90)', 'p(95)', 'p(99)'],
  throw: false,
};

const BASE = __ENV.BASE || 'http://localhost:19331';

export default function () {
  const list = http.get(`${BASE}/api/products?limit=50`, { tags: { name: 'list' } });
  check(list, { 'list 200': (r) => r.status === 200 });

  const pid = 1 + (__ITER % 200);
  const detail = http.get(`${BASE}/api/products/${pid}`, { tags: { name: 'detail' } });
  check(detail, { 'detail 200': (r) => r.status === 200 });

  if (__ITER % 2 === 0) {
    http.post(`${BASE}/api/orders`,
      JSON.stringify({ user_id: __VU, product_id: pid, qty: 1 }),
      { headers: { 'Content-Type': 'application/json' }, tags: { name: 'order' } });
  }
  sleep(0.1);
}
