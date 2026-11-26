# Configuración Manual de Supabase para BOOKLY

Sigue estos pasos en orden para conectar un proyecto real de Supabase:

1. **Crear proyecto en Supabase** (`https://supabase.com/dashboard`):
   - Anota tu `Project URL` (`SUPABASE_URL`), `Publishable key` (`SUPABASE_PUBLISHABLE_KEY`), y `Secret key` (`SUPABASE_SECRET_KEY`).
   - En **Settings -> Database -> Connection string**:
     - Copia la URL del **Transaction Pooler (puerto 6543)** como `DATABASE_URL` en `backend/.env`.
     - Copia la URL **Direct Connection (puerto 5432)** (o Session Pooler si tu red es IPv4-only) como `DIRECT_DATABASE_URL` en `backend/.env`.

2. **Ejecutar migraciones Alembic desde el backend**:
   ```bash
   cd backend
   alembic upgrade head
   python scripts/seed.py
   ```

3. **Aplicar Trigger de Auth, RLS y Buckets en Supabase SQL Editor**:
   - Ejecuta `supabase/policies/01_auth_trigger_and_rls.sql`.
   - Ejecuta `supabase/storage/02_storage_buckets_and_policies.sql`.

4. **Configurar Supabase Auth**:
   - En **Authentication -> URL Configuration**, agrega `http://localhost:5173` como Site URL y `http://localhost:5173/auth/callback` y `http://localhost:5173/restablecer-contrasena` como Redirect URLs.
   - Habilita confirmación de correo electrónico según tu entorno.

5. **Crear usuario administrador de forma segura**:
   - Registra el usuario administrador normalmente en Supabase Auth (o en la app).
   - Ejecuta en el servidor:
     ```bash
     python scripts/create_admin.py --email admin@bookly.pe --name "Administrador BOOKLY"
     ```
