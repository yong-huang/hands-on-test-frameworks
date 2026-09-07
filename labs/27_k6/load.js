// lab 27：k6 场景（smoke / ramping / spike）+ thresholds 质量门禁
// 用法：BASE_URL=http://127.0.0.1:8927 k6 run -e SCENARIO=ramping load.js
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE = __ENV.BASE_URL || 'http://127.0.0.1:8927';

// 三种场景由 SCENARIO 环境变量选择——同一份脚本覆盖三类负载形态
const scenarios = {
  smoke:   { executor: 'constant-vus', vus: 1, duration: '15s' },
  ramping: {
    executor: 'ramping-vus',
    startVUs: 0,
    stages: [
      { duration: '20s', target: 20 },   // 爬升
      { duration: '30s', target: 20 },   // 稳态
      { duration: '10s', target: 0 },    // 收尾
    ],
  },
  spike: {
    executor: 'ramping-arrival-rate',    // 突刺：固定到达率瞬间抬升
    startRate: 5, timeUnit: '1s',
    preAllocatedVUs: 60, maxVUs: 100,
    stages: [
      { duration: '10s', target: 5 },    // 基线
      { duration: '15s', target: 60 },   // 突刺！
      { duration: '10s', target: 5 },    // 回落
    ],
  },
};

export const options = {
  scenarios: { main: scenarios[__ENV.SCENARIO || 'smoke'] },
  // thresholds：不达标 → k6 退出码非 0 → 可直接当 CI 门禁
  thresholds: {
    'http_req_duration{endpoint:fast}': ['p(95)<500'],
    'http_req_failed': ['rate<0.01'],
  },
};

function fastGet(url, name) {
  // tag endpoint:fast —— 阈值只约束快接口（慢接口 1.5s 是 SUT 的已知设计）
  return http.get(url, { tags: { endpoint: 'fast', name } });
}

export default function () {
  const health = fastGet(`${BASE}/api/health`, 'GET /health');
  check(health, { 'health 200': (r) => r.status === 200 });

  const list = fastGet(`${BASE}/api/orders?limit=10`, 'GET /orders 分页');
  check(list, {
    'list 200': (r) => r.status === 200,
    'list 有 total': (r) => Number(r.headers['X-Total-Count']) >= 0,
  });
  sleep(0.2);
}
