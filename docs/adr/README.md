# Architecture Decision Records (ADR) — BOOKLY

## ADR-001: Elección de React + TypeScript + Vite
- **Contexto:** Se requiere una SPA rápida, tipada y con ecosistema maduro para formularios complejos, estado y gráficas administrativas.
- **Decisión:** React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui, Zustand, TanStack Query, React Hook Form + Zod y Recharts.
- **Consecuencia:** Alta productividad, validación compartida en UI y excelente rendimiento para distribución estática vía S3 + CloudFront.

## ADR-002: Elección de FastAPI + Python
- **Contexto:** Toda la lógica transaccional, precios, stock, reportes y autorización debe ejecutarse en un backend independiente con documentación OpenAPI automática.
- **Decisión:** FastAPI 0.115 + Pydantic v2 + SQLAlchemy 2.0 + Alembic.
- **Consecuencia:** Validación estricta de esquemas, generación nativa de `/docs` Swagger y separación clara por módulos.

## ADR-003: Elección de Supabase (Database + Auth + Storage)
- **Contexto:** Se necesita PostgreSQL gestionado, autenticación estándar JWT y almacenamiento de objetos sin mantener servidores de archivos en contenedores.
- **Decisión:** Usar Supabase como plataforma BaaS complementaria al backend FastAPI.
- **Consecuencia:** Reducción de carga operativa, verificación de tokens vía JWKS y almacenamiento desacoplado de portadas y avatares.

## ADR-004: Elección de PostgreSQL
- **Contexto:** Un e-commerce de libros exige integridad referencial, transacciones ACID, restricciones CHECK (`stock >= 0`) y consistencia financiera.
- **Decisión:** PostgreSQL 16+ gestionado en Supabase con tipos `NUMERIC(10, 2)` y `UUID`.
- **Consecuencia:** Garantía transaccional contra sobreventa y trazabilidad exacta de movimientos de inventario.

## ADR-005: Elección de Docker y Docker Compose
- **Contexto:** Necesidad de paridad entre entorno local, CI/CD y despliegue en EC2.
- **Decisión:** Compilación multietapa (`python:3.13-slim` y `nginx:1.27-alpine`) sin estado persistente en contenedores.
- **Consecuencia:** Contenedores ligeros, reproducibles y listos para escalar horizontalmente.

## ADR-006: Elección de AWS (S3, CloudFront, ALB, EC2, ASG, ECR, CloudWatch)
- **Contexto:** Proyecto de Cloud Computing con requisitos de red VPC en dos zonas de disponibilidad, aislamiento de cómputo en subredes privadas y observabilidad centralizada.
- **Decisión:** Combinación de servicios administrados (S3/CloudFront/ECR/CloudWatch/Secrets Manager) y cómputo elástico (EC2 + ALB + ASG).
- **Consecuencia:** Arquitectura resiliente, verificable con Terraform y con clara separación de responsabilidades entre IaaS, PaaS y BaaS.

## ADR-007: Arquitectura Monolítica Modular
- **Contexto:** Evitar la complejidad prematura de microservicios distribuidos manteniendo cohesión y orden.
- **Decisión:** Monolito modular dividido por dominios (`catalog`, `cart`, `orders`, `inventory`, `users`, `admin`, `audit`).
- **Consecuencia:** Despliegue simple en un contenedor único por instancia y transacciones ACID locales sin sagas distribuidas.

## ADR-008: Modelo de Escalabilidad Horizontal Stateless
- **Contexto:** Soportar incrementos de concurrencia (50–200 usuarios simultáneos) sin pérdida de sesiones ni archivos.
- **Decisión:** Contenedores backend completamente stateless detrás de ALB + Auto Scaling Group (Target Tracking CPU 65%), con sesiones JWT y estado persistido en Supabase PostgreSQL/Storage.
- **Consecuencia:** Posibilidad de agregar o reemplazar instancias EC2 automáticamente ante fallos o picos de demanda.
