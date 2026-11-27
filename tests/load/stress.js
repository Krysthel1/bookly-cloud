import http from 'k6/http';
import { check, sleep } from 'k6';

const RAW_URL = (__ENV.BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
const API_BASE = RAW_URL.endsWith('/api/v1') ? RAW_URL : `${RAW_URL}/api/v1`;
const ROOT_BASE = RAW_URL.endsWith('/api/v1') ? RAW_URL.slice(0, -7) : RAW_URL;
const MAX_VUS = Number(__ENV.MAX_VUS || 100);

export const options = {
  stages: [
    { duration: '1m', target: 25 },
    { duration: '2m', target: 50 },
    { duration: '3m', target: MAX_VUS }, // 100 base; 200 con MAX_VUS=200 si las cuotas lo permiten
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const health = http.get(`${ROOT_BASE}/health`);
  check(health, { 'health ok': (r) => r.status === 200 });

  const catalog = http.get(`${API_BASE}/books?sort=best_sellers&page=1`);
  check(catalog, { 'catalog ok': (r) => r.status === 200 });

  sleep(0.5);
}
