import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const MAX_VUS = Number(__ENV.MAX_VUS || 100);

export const options = {
  stages: [
    { duration: '20s', target: 25 },
    { duration: '30s', target: 50 },
    { duration: '30s', target: MAX_VUS }, // 100 por defecto; usar MAX_VUS=200 solo si el entorno lo permite
    { duration: '20s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const health = http.get(`${BASE_URL}/health`);
  check(health, { 'health ok': (r) => r.status === 200 });

  const catalog = http.get(`${BASE_URL}/api/v1/books?sort=best_sellers&page=1`);
  check(catalog, { 'catalog ok': (r) => r.status === 200 });

  sleep(0.5);
}
