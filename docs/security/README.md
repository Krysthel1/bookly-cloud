# Documentación de Seguridad — BOOKLY

## 1. Autenticación y Gestión de Identidad
- **Proveedor:** Supabase Auth (GoTrue).
- **Credenciales:** Las contraseñas jamás se almacenan en tablas de la aplicación ni se envían al backend FastAPI; el frontend usa `@supabase/supabase-js` directamente.
- **Verificación de Tokens en FastAPI:** `app/security/jwt.py` valida cada `Authorization: Bearer <ACCESS_TOKEN>` verificando firma asimétrica vía JWKS (`/auth/v1/.well-known/jwks.json`, `RS256`/`ES256`) o `HS256` heredado (`SUPABASE_JWT_SECRET`), además de expiración (`exp`), audiencia (`authenticated`) e emisor (`<SUPABASE_URL>/auth/v1`).
- **Principio de Confianza Cero en el Cliente:** FastAPI extrae el UUID (`sub`) únicamente del token verificado e ignora `user_id`, precios o roles enviados desde el navegador. No se usa `user_metadata` editable para decisiones de autorización.

## 2. Autorización Basada en Roles (RBAC)
- El registro público asigna exclusivamente el rol `customer` (vía trigger SQL `handle_new_user()` y respaldo idempotente en `get_current_user`).
- La asignación del rol `admin` solo puede ejecutarse desde el servidor mediante `backend/scripts/create_admin.py` y deja registro en `audit_logs`.
- Todos los endpoints `/api/v1/admin/*` exigen `Depends(require_admin)`.
- Todos los recursos del cliente (`orders`, `addresses`, `notifications`, `cart`, `favorites`) validan pertenencia (`user_id == current_user.id`).

## 3. Base de Datos, RLS y Protección de Secretos
- Row Level Security (RLS) habilitado en las 23 tablas (`supabase/policies/01_auth_trigger_and_rls.sql`).
- Tablas críticas (`orders`, `order_items`, `payments`, `inventory_movements`, `coupons`, `coupon_usages`, `audit_logs`, `roles`, `user_roles`, `carts`, `cart_items`) bloqueadas para acceso directo por la Data API de Supabase, forzando que toda lógica transaccional pase por FastAPI.
- `SUPABASE_SECRET_KEY` y `DATABASE_URL` residen únicamente en backend (o AWS Secrets Manager) y nunca se exponen en `frontend/.env`.
- Protección contra SQL Injection mediante SQLAlchemy ORM parametrizado; CORS restringido por `CORS_ORIGINS`; rate limiting con `slowapi`.
