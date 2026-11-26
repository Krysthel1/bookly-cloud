import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const AUTH_TOKEN = __ENV.AUTH_TOKEN || '';
const TEST_BOOK_ID = __ENV.TEST_BOOK_ID || '';

export const options = {
  stages: [
    { duration: '15s', target: 10 },
    { duration: '30s', target: 25 },
    { duration: '15s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  if (!AUTH_TOKEN || !TEST_BOOK_ID) {
    // Prueba de endpoint protegido sin token para verificar respuesta rápida 401 si no hay token de pruebas
    const unauth = http.get(`${BASE_URL}/api/v1/orders`);
    check(unauth, { 'rechaza sin auth (401)': (r) => r.status === 401 });
    sleep(1);
    return;
  }

  const headers = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${AUTH_TOKEN}`,
  };

  const addRes = http.post(
    `${BASE_URL}/api/v1/cart/items`,
    JSON.stringify({ book_id: TEST_BOOK_ID, quantity: 1 }),
    { headers },
  );
  check(addRes, { 'agrega al carrito': (r) => r.status === 201 || r.status === 409 });

  sleep(1);
}
