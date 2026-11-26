# Documentación de la API REST — BOOKLY

FastAPI genera documentación interactiva automática en:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **Esquema OpenAPI JSON:** `http://localhost:8000/openapi.json`

## Resumen de Endpoints (`/api/v1`)

| Módulo | Método y Ruta | Acceso | Descripción |
|---|---|---|---|
| Infraestructura | `GET /health`, `GET /ready` | Público | Liveness y readiness (verifica PostgreSQL) |
| Autenticación / Perfil | `GET /api/v1/auth/me`, `GET/PATCH /api/v1/users/me`, `POST /api/v1/users/me/avatar` | Cliente | Perfil, roles verificados y subida de avatar |
| Direcciones / Notif. | `GET/POST/PATCH/DELETE /api/v1/users/me/addresses`, `GET /api/v1/users/me/notifications` | Cliente | Gestión de direcciones y notificaciones |
| Catálogo | `GET /api/v1/books`, `/featured`, `/best-sellers`, `/new-releases`, `/{id}`, `/{id}/related`, `/{id}/reviews` | Público | Búsqueda, filtros, paginación y reseñas |
| Reseñas | `POST /api/v1/books/{id}/reviews` | Cliente | Publicar o actualizar reseña |
| Categorías / Autores | `GET /api/v1/categories`, `GET /api/v1/authors`, `GET /api/v1/publishers` | Público | Listados y detalle |
| Carrito / Favoritos | `GET/POST/PATCH/DELETE /api/v1/cart*`, `GET/POST/DELETE /api/v1/favorites*` | Cliente | Carrito persistente en PostgreSQL y favoritos |
| Pedidos / Cupones | `POST /api/v1/coupons/validate`, `POST /api/v1/orders/checkout`, `GET /api/v1/orders*`, `POST /api/v1/orders/{id}/cancel` | Cliente | Checkout transaccional idempotente y cancelación |
| Administración | `/api/v1/admin/dashboard`, `/books*`, `/categories*`, `/authors*`, `/inventory*`, `/orders*`, `/users*`, `/coupons*`, `/reports/*`, `/storage/upload`, `/audit-logs` | Admin | Gestión integral, KPIs, CSV y auditoría |
