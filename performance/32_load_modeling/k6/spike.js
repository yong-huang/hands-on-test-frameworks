import http from 'k6/http';
import { check } from 'k6';
// 尖峰场景：30/s 平稳 30s → 20s 内冲到 400/s 维持 15s → 落回 30/s 再跑 30s。
// 验收点：突刺期间延迟/错误率出现可复现的尖峰（对照平稳期读数）
export const options = {
  scenarios: {
    spike: {
      executor: 'ramping-arrival-rate',
      stages: [
        { target: 30, duration: '30s' },
        { target: 400, duration: '35s' },
        { target: 30, duration: '30s' },
      ],
      preAllocatedVUs: 300,
      maxVUs: 800,
    },
  },
  summaryTrendStats: ['avg', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
  throw: false,
};

const BASE = __ENV.BASE || 'http://localhost:19331';

export default function () {
  const pid = 1 + (__ITER % 200);
  const detail = http.get(`${BASE}/api/products/${pid}`, { tags: { name: 'detail' } });
  check(detail, { 'detail 200': (r) => r.status === 200 });
}
