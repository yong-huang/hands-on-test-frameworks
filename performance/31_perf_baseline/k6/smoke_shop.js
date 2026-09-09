import http from 'k6/http';
import { check, sleep } from 'k6';

// 基线冒烟：5 VU × 30s，读写混合约 2:1（浏览/详情 : 下单）
// 目标不是压垮，而是拿到可复现的"优化前基线"
export const options = {
  vus: 5,
  duration: '30s',
  summaryTrendStats: ['avg', 'med', 'p(90)', 'p(95)', 'p(99)'],
  thresholds: {
    // 基线阶段只记录不设门禁：哪怕全失败也要出报告
  },
  throw: false,
};

const BASE = __ENV.BASE || 'http://localhost:19331';

export default function () {
  // 浏览列表（50 条/页，会触发每行一次的库存查询）
  const list = http.get(`${BASE}/api/products?limit=50`, { tags: { name: 'list' } });
  check(list, { 'list 200': (r) => r.status === 200 });

  // 看详情（附推荐打分）
  const pid = 1 + (__ITER % 200);
  const detail = http.get(`${BASE}/api/products/${pid}`, { tags: { name: 'detail' } });
  check(detail, { 'detail 200': (r) => r.status === 200 });

  // 每 2 轮下一次单（写比例 1/3）
  if (__ITER % 2 === 0) {
    const order = http.post(
      `${BASE}/api/orders`,
      JSON.stringify({ user_id: __VU, product_id: pid, qty: 1 }),
      { headers: { 'Content-Type': 'application/json' }, tags: { name: 'order' } },
    );
    check(order, { 'order 201': (r) => r.status === 201 });
  }
  sleep(0.2);
}
