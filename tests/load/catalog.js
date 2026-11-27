import http from 'k6/http';
import { check, sleep } from 'k6';

const RAW_URL = (__ENV.BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
const API_BASE = RAW_URL.endsWith('/api/v1') ? RAW_URL : `${RAW_URL}/api/v1`;
const TARGET_VUS = Number(__ENV.TARGET_VUS || 50);

export const options = {
  stages: [
    { duration: '1m', target: TARGET_VUS },
    { duration: '3m', target: TARGET_VUS },
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const resCatalog = http.get(`${API_BASE}/books?page=1&page_size=12`);
  check(resCatalog, {
    'catálogo 200': (r) => r.status === 200,
    'retorna items': (r) => JSON.parse(r.body).items !== undefined,
  });

  const resFeatured = http.get(`${API_BASE}/books/featured`);
  check(resFeatured, {
    'destacados 200': (r) => r.status === 200,
  });

  sleep(1);
}
