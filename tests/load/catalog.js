import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export const options = {
  stages: [
    { duration: '20s', target: 10 },
    { duration: '30s', target: 25 },
    { duration: '30s', target: 50 },
    { duration: '20s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const resCatalog = http.get(`${BASE_URL}/api/v1/books?page=1&page_size=12`);
  check(resCatalog, {
    'catálogo 200': (r) => r.status === 200,
    'retorna items': (r) => JSON.parse(r.body).items !== undefined,
  });

  const resFeatured = http.get(`${BASE_URL}/api/v1/books/featured`);
  check(resFeatured, {
    'destacados 200': (r) => r.status === 200,
  });

  sleep(1);
}
