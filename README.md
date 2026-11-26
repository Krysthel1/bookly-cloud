# BOOKLY — Librería Digital Full Stack + Supabase + AWS Cloud Computing

**BOOKLY** es un sistema web completo de comercio electrónico de libros diseñado con una arquitectura modular de tres capas:
- **Frontend (Presentación):** React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui, TanStack Query, Zustand, React Hook Form, Zod y Recharts.
- **Backend (Negocio):** Python 3.13, FastAPI, Uvicorn, SQLAlchemy 2.0, Alembic, Pydantic v2, PyJWT (`JWKS` + `HS256`), Pillow y SlowAPI.
- **Base de Datos, Auth y Storage:** Supabase (PostgreSQL gestionado, Supabase Auth, Supabase Storage y Row Level Security).
- **Cloud Computing y DevOps:** Docker, Docker Compose, GitHub Actions (CI/CD vía OIDC), Terraform (AWS VPC, S3 + CloudFront OAC, ALB, EC2 Auto Scaling, ECR, Secrets Manager, CloudWatch) y pruebas de carga k6.

---

## Estructura del Monorepositorio

```text
BOOKLY/
├── frontend/                  # SPA React + TypeScript + Vite + Vitest
├── backend/                   # API REST modular FastAPI + Alembic + Pytest
├── infrastructure/
│   ├── terraform/             # Infraestructura AWS Multi-AZ (VPC 10.0.0.0/16)
│   └── scripts/               # Scripts de validación Terraform
├── supabase/                  # Scripts SQL de Auth Trigger, RLS y Storage
├── tests/load/                # Escenarios k6 (catalog, checkout, stress)
├── docs/                      # Arquitectura, ER, ADRs, Costos, Seguridad e Informe Académico
├── .github/workflows/         # Pipelines CI/CD para Frontend y Backend
└── docker-compose.yml         # Orquestación local (conectado a Supabase)
```

---

## Requisitos Previos

- **Node.js** 20+ (probado con v22.17.1) y **npm** 10+
- **Python** 3.12+ (probado con 3.13.7)
- **Docker** y **Docker Compose** (opcional para ejecución en contenedores)
- Un proyecto en **Supabase** (para base de datos PostgreSQL, Auth y Storage)

---

## 1. Configuración de Supabase (Manual)

1. Crea un proyecto en [Supabase](https://supabase.com/dashboard).
2. Copia `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY` y `SUPABASE_SECRET_KEY`.
3. Obtén tus cadenas PostgreSQL en **Settings → Database**:
   - `DATABASE_URL`: Transaction Pooler (`puerto 6543`, compatible IPv4).
   - `DIRECT_DATABASE_URL`: Direct Connection (`puerto 5432`) para Alembic.
4. Sigue la guía [`supabase/README.md`](supabase/README.md) para aplicar las migraciones y luego ejecutar en el SQL Editor:
   - [`supabase/policies/01_auth_trigger_and_rls.sql`](supabase/policies/01_auth_trigger_and_rls.sql)
   - [`supabase/storage/02_storage_buckets_and_policies.sql`](supabase/storage/02_storage_buckets_and_policies.sql)

---

## 2. Variables de Entorno

### Backend (`backend/.env`)
Copia `backend/.env.example` a `backend/.env`:
```env
APP_NAME=BOOKLY
APP_ENV=development
DATABASE_URL=postgresql://postgres.<REF>:<PASS>@aws-0-<REGION>.pooler.supabase.com:6543/postgres?sslmode=require
DIRECT_DATABASE_URL=postgresql://postgres:<PASS>@db.<REF>.supabase.co:5432/postgres?sslmode=require
SUPABASE_URL=https://<REF>.supabase.co
SUPABASE_PUBLISHABLE_KEY=<tu-publishable-key>
SUPABASE_SECRET_KEY=<tu-secret-key>
CORS_ORIGINS=http://localhost:5173
```

### Frontend (`frontend/.env`)
Copia `frontend/.env.example` a `frontend/.env`:
```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_SUPABASE_URL=https://<REF>.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=<tu-publishable-key>
```
> Nunca expongas `SUPABASE_SECRET_KEY` ni `DATABASE_URL` en el frontend.

---

## 3. Instalación y Ejecución Local

### Backend (FastAPI)
```bash
cd backend
python -m venv .venv
# En Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# En Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt

# 1. Ejecutar migraciones Alembic (23 tablas + roles iniciales)
alembic upgrade head

# 2. Cargar datos iniciales (8 categorías, 18 autores, 8 editoriales, 42 libros, 3 cupones)
python scripts/seed.py

# 3. Crear usuario administrador de forma segura (tras registrarlo en Supabase Auth)
python scripts/create_admin.py --email admin@bookly.pe --name "Administrador BOOKLY"

# 4. Iniciar servidor API
uvicorn app.main:app --reload --port 8000
```

Documentación interactiva Swagger disponible en:
- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

### Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
Accede en `http://localhost:5173`.

---

## 4. Ejecución con Docker

### Modo estándar (conectado a Supabase)
```bash
docker compose up --build
```
- Frontend Nginx: `http://localhost:5173`
- Backend FastAPI: `http://localhost:8000`

### Alternativa aislada para pruebas locales sin conexión a Supabase
```bash
docker compose --profile local-test-db up --build
```
Esto levanta `postgres-test` en el puerto `5433` para pruebas de migración aisladas.

---

## 5. Pruebas Automatizadas y Carga

### Backend
```bash
cd backend
ruff check app tests scripts
pytest -v
```

### Frontend
```bash
cd frontend
npm run lint
npm test
npm run build
```

### Pruebas de carga (k6)
```bash
k6 run -e BASE_URL=http://localhost:8000 tests/load/catalog.js
k6 run -e BASE_URL=http://localhost:8000 tests/load/stress.js
```

---

## 6. Documentación y Cloud Computing

- [Arquitectura Cloud y Lógica](docs/architecture/cloud-architecture.md)
- [Diagramas de Casos de Uso, Secuencia y CI/CD](docs/architecture/system-diagrams.md)
- [Atributos de Calidad y SLAs](docs/architecture/quality-attributes.md)
- [Diagrama Entidad-Relación (23 tablas)](docs/database/er-diagram.md)
- [Decisiones Arquitectónicas (ADR)](docs/adr/README.md)
- [Seguridad y RLS](docs/security/README.md)
- [Monitoreo CloudWatch](docs/monitoring/README.md)
- [Pruebas y Resiliencia](docs/testing/README.md)
- [Estimación de Costos AWS + Supabase](docs/costs/README.md)
- [Informe Académico Completo (5 Capítulos)](docs/INFORME_ACADEMICO.md)

---

## 7. Solución de Errores Frecuentes

- **`server closed the connection unexpectedly` o error con IPv6 en Supabase:** Usa la URL del **Supavisor Transaction Pooler (puerto 6543)** en `DATABASE_URL`; el backend configura automáticamente `NullPool` y desactiva sentencias preparadas persistentes.
- **Error `401 Invalid authentication token`:** Verifica que `SUPABASE_URL` coincida exactamente con el proyecto que emitió el JWT en el frontend.
- **Error `403` al entrar al panel `/admin`:** El registro público solo asigna rol `customer`. Ejecuta `python scripts/create_admin.py --email <correo>` desde el servidor backend.
