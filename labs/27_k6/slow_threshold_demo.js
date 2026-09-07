// 阈值门禁的"失败演示"：对 1.5s 慢接口设 p95<500ms → 必然不达标 → 退出码非 0
import http from 'k6/http';

export const options = {
  vus: 2, duration: '5s',
  thresholds: { 'http_req_duration': ['p(95)<500'] },
};

export default function () {
  http.get(`${__ENV.BASE_URL}/api/slow-config`);
}
