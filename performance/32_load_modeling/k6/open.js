import http from 'k6/http';
import { check } from 'k6';

// 开放模型：到达率固定，请求彼此独立，不等上一条响应（贴近真实流量）。
// RATE 由环境变量注入：RATE=50/150/300 各跑一轮。
// 关键：SUT 变慢时请求只会在网络/服务器排队，压测机不会自动少发——
// 这正是它和封闭模型 P95 出现差异的根源（Coordinated Omission 的反面教材位）。
export const options = {
  scenarios: {
    arrivals: {
      executor: 'constant-arrival-rate',
      rate: Number(__ENV.RATE || 50),   // 每秒多少次迭代
      timeUnit: '1s',
      duration: __ENV.DUR || '40s',
      preAllocatedVUs: Number(__ENV.VUPOOL || 300),
      maxVUs: 600,
    },
  },
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
}
