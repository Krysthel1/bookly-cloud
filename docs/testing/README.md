# Estrategia de Pruebas y Resiliencia — BOOKLY

## 1. Pruebas Automatizadas (Backend y Frontend)
- **Backend (Pytest):** `backend/tests/test_bookly_api.py` evalúa salud (`/health`, `/ready`), JWT, RBAC (401/403), auto-aprovisionamiento seguro (solo rol `customer`), CRUD administrativo, validación de stock en carrito, checkout transaccional con cupones, idempotencia, aislamiento entre clientes, devolución única de stock al cancelar, reportes CSV y auditoría.
- **Frontend (Vitest + Testing Library):** `frontend/tests/bookly.test.tsx` evalúa renderizado de `BookCard` en `S/`, carrito, validaciones Zod en `LoginPage`, protección de rutas (`ProtectedRoute`) y `EmptyState`.

## 2. Pruebas de Carga Progresivas con k6 (`tests/load/`)
Escenarios incluidos:
- `tests/load/catalog.js`: Rampa progresiva de **10 → 25 → 50 usuarios concurrentes** sobre catálogo y destacados.
- `tests/load/checkout.js`: Flujo autenticado de carrito/pedidos (**10 → 25 VUs**).
- `tests/load/stress.js`: Prueba de estrés progresiva hasta **100 VUs** (configurable a **200 VUs** con `-e MAX_VUS=200` únicamente en entornos autorizados).

Ejecución local de ejemplo (requiere tener k6 instalado y el backend en ejecución):
```bash
k6 run -e BASE_URL=http://localhost:8000 tests/load/catalog.js
```

## 3. Plan de Pruebas de Resiliencia en AWS
1. **Caída controlada de una instancia EC2:** Terminar 1 instancia del ASG y medir el tiempo de detección del ALB (`unhealthy_threshold=3` x 30s ≈ 90s) y reemplazo automático por el Auto Scaling Group (`min_size=2`).
2. **Distribución de tráfico del ALB:** Verificar respuestas HTTP 200 continuas durante el reemplazo.
3. **Interrupción temporal de PostgreSQL:** Validar que `/ready` responde `503 Service Unavailable` sin tumbar el proceso FastAPI y que las peticiones se recuperan automáticamente mediante `pool_pre_ping=True` al restablecerse la conectividad.

> *Nota:* No se incluyen métricas inventadas de k6 ni de caídas en AWS porque las pruebas deben ejecutarse contra el entorno desplegado autorizado para reportar mediciones reales.
