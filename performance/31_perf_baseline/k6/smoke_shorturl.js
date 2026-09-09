import http from 'k6/http';
import { check, sleep } from 'k6';

// 基线冒烟：5 VU × 30s，跳转:创建 ≈ 9:1（真实短链服务读远多于写）
export const options = {
  vus: Number(__ENV.VUS || 5),
  duration: __ENV.DUR || '30s',
  summaryTrendStats: ['avg', 'med', 'p(90)', 'p(95)', 'p(99)'],
  throw: false,
};

const BASE = __ENV.BASE || 'http://localhost:19332';

export default function () {
  // 读：短码跳转（follow:false——301 本身就是业务成功，别跟去 example.com）
  const code = 's' + String(1 + (__ITER % 5000)).padStart(5, '0');
  const redir = http.get(`${BASE}/${code}`, { redirects: 0, tags: { name: 'redirect' } });
  check(redir, { 'redirect 301': (r) => r.status === 301 });

  // 写：约 1/10 概率创建短链
  if (__ITER % 10 === 0) {
    const created = http.post(
      `${BASE}/api/shorten`,
      JSON.stringify({ url: `https://example.com/new/${__VU}/${__ITER}` }),
      { headers: { 'Content-Type': 'application/json' }, tags: { name: 'shorten' } },
    );
    check(created, { 'shorten 201': (r) => r.status === 201 });
  }
  sleep(0.2);
}
