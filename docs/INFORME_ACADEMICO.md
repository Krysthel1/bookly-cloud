# Informe Académico — Diseño e Implementación de BOOKLY en Arquitectura Cloud (AWS + Supabase)

---

## Capítulo 1. Planteamiento del problema

### 1.1. Descripción del problema
Las librerías independientes y comercios editoriales regionales enfrentan limitaciones críticas cuando operan con plataformas monolíticas tradicionales acopladas o sitios estáticos sin control transaccional: sobreventa de ejemplares por falta de bloqueo atómico de inventario, exposición de precios manipulables en el navegador, ausencia de trazabilidad histórica de movimientos de stock, cuellos de botella en picos de demanda y falta de separación entre el plano de presentación y la lógica de negocio.

Ante este escenario, **BOOKLY** propone una plataforma de comercio electrónico de libros diseñada bajo arquitectura de tres capas desacoplada, integrando **React + TypeScript** en la capa de presentación, **FastAPI + SQLAlchemy 2.0** en la capa de negocio y **Supabase (PostgreSQL, Auth y Storage)** como plataforma BaaS, preparada para desplegarse en **Amazon Web Services (AWS)** mediante Infraestructura como Código (Terraform).

### 1.2. Objetivo general y objetivos específicos medibles

**Objetivo general:**  
Diseñar, construir y documentar un sistema web Full Stack para la venta de libros (**BOOKLY**) seguro, modular y escalable horizontalmente sobre una arquitectura híbrida AWS + Supabase.

**Objetivos específicos medibles:**
1. **Integridad transaccional y cero sobreventa:** Implementar un flujo de checkout atómico e idempotente en FastAPI + PostgreSQL que garantice 0 % de ventas por encima del stock disponible (`stock >= 0`) y devolución única de inventario ante cancelaciones.
2. **Rendimiento bajo concurrencia:** Alcanzar una latencia **p95 < 500 ms** en consultas principales del catálogo y una **tasa de errores < 1 %** en escenarios progresivos de hasta 100 usuarios concurrentes con k6.
3. **Disponibilidad y tolerancia a fallos:** Diseñar una infraestructura AWS Multi-AZ (2 Zonas de Disponibilidad) con Application Load Balancer y Auto Scaling Group (`min_size = 2`) orientada a un objetivo de disponibilidad del **99,9 %**, **RTO ≤ 60 minutos** y **RPO ≤ 24 horas** (sujeto al plan Supabase Pro).
4. **Seguridad y control de acceso:** Implementar verificación criptográfica de JWT de Supabase Auth (JWKS `RS256`/`ES256` y `HS256`), control de acceso basado en roles (`customer` y `admin`), Row Level Security (RLS) en las 23 tablas y auditoría de operaciones administrativas.

### 1.3. Alcance y restricciones
- **Alcance:** Catálogo con búsqueda y filtros paginados, carrito persistente en PostgreSQL, checkout en 5 etapas con pagos simulados (Tarjeta, Yape, Plin, Contra entrega), portal *Mi Cuenta*, panel administrativo con KPIs y gráficos Recharts, CRUD completo, inventario con kardex de movimientos, reportes exportables en CSV, contenedorización Docker, CI/CD en GitHub Actions y definición Terraform para AWS.
- **Restricciones:** Los pagos son simulados con fines académicos (sin pasarela real ni almacenamiento de tarjetas). Las pruebas de carga y despliegue en AWS no aprovisionan recursos de pago automáticamente sin autorización explícita.

---

## Capítulo 2. Análisis de requisitos y atributos de calidad

### 2.1. Requisitos funcionales
- **Visitante:** Exploración de portada editorial, catálogo paginado, búsqueda por título/autor/ISBN, filtros por categoría/precio/disponibilidad/ofertas, vista de detalle con reseñas y registro/inicio de sesión.
- **Cliente autenticado:** Gestión de perfil, libreta de direcciones, favoritos, carrito persistente en PostgreSQL, validación de cupones, checkout en 5 pasos, seguimiento y cancelación de pedidos, publicación de reseñas y notificaciones.
- **Administrador:** Acceso al dashboard ejecutivo con filtro por rango de fechas, CRUD de libros/categorías/autores/cupones, subida de portadas optimizadas a Supabase Storage, gestión de stock y kardex, transición autorizada de estados de pedidos, consulta de clientes, exportación de reportes CSV y registros de auditoría.

### 2.2. Requisitos no funcionales
- **Seguridad:** JWT verificado en servidor, RLS en Data API, CORS acotado, rate limiting (`slowapi`), cabeceras HTTP de seguridad y aislamiento de instancias backend en subredes privadas.
- **Mantenibilidad:** Arquitectura monolítica modular por capas (Routers → Services → Repositories/ORM) y tipado estricto en TypeScript y Pydantic v2.
- **Portabilidad:** Empaquetado mediante Docker multietapa (`backend/Dockerfile`, `frontend/Dockerfile`) y `docker-compose.yml`.
- **Usabilidad:** Interfaz en español, precios en soles peruanos (`S/`), modo claro/oscuro, diseño responsive y estados de carga/error/vacío accesibles.

### 2.3. Justificación de los modelos de servicio IaaS, PaaS y BaaS
- **IaaS (Amazon EC2 + VPC):** Control total sobre subredes privadas, Security Groups, Auto Scaling Group, agente de CloudWatch y ejecución de contenedores Docker stateless.
- **PaaS / Servicios Gestionados (CloudFront, S3, ALB, ECR, CloudWatch, GitHub Actions):** Reducción de carga operativa en distribución CDN, balanceo de carga Multi-AZ, escaneo de imágenes y automatización CI/CD sin administrar servidores dedicados para esos roles.
- **BaaS (Supabase Database, Auth, Storage):** Acelera el desarrollo seguro al proveer PostgreSQL gestionado con pooler Supavisor, autenticación OAuth2/JWT estándar y almacenamiento de objetos con políticas de acceso, manteniendo toda la lógica de negocio crítica en FastAPI.

---

## Capítulo 3. Diseño de arquitectura Cloud

### 3.1. Buenas prácticas de arquitectura
Siguiendo el *AWS Well-Architected Framework*:
- **Excelencia operativa:** Infraestructura como Código en `infrastructure/terraform/` y pipelines CI/CD con OIDC (sin llaves IAM permanentes).
- **Seguridad:** Principio de menor privilegio (IAM role para EC2 con acceso exclusivo a ECR Pull, Secrets Manager y CloudWatch), IMDSv2 obligatorio, OAC en S3 y backend en subredes privadas.
- **Fiabilidad:** Distribución en 2 Zonas de Disponibilidad, health checks `/health` y `/ready`, y `Instance Refresh` automático.
- **Eficiencia de rendimiento:** Distribución estática en borde con CloudFront, compresión WebP de imágenes con Pillow y Supavisor Transaction Pooler (`NullPool` en SQLAlchemy).

### 3.2. Diagrama de arquitectura general
Ver diagrama detallado en [`docs/architecture/cloud-architecture.md`](architecture/cloud-architecture.md).

### 3.3. Diseño de red y conectividad
- **VPC:** `10.0.0.0/16` distribuida en 2 AZs.
- **Subredes públicas (`10.0.1.0/24`, `10.0.2.0/24`):** Alojan el Application Load Balancer público y el NAT Gateway con ruta hacia el Internet Gateway.
- **Subredes privadas (`10.0.11.0/24`, `10.0.12.0/24`):** Alojan las instancias EC2 del backend FastAPI sin IP pública.
- **Conectividad externa con Supabase:** Al ser un servicio externo a la VPC de AWS, las instancias privadas salen a través del NAT Gateway hacia Supabase Auth/Storage por **HTTPS (443)** y hacia Supabase PostgreSQL por **TLS (puerto 6543 Supavisor o 5432 directo)**.

### 3.4. Capa de cómputo y almacenamiento
- **Cómputo:** Launch Template con Amazon Linux 2023, Docker, CloudWatch Agent y recuperación de secretos desde AWS Secrets Manager al arranque. Auto Scaling Group (`min=2`, `max=4`) con política Target Tracking al 65 % de CPU.
- **Almacenamiento:** Bucket S3 privado + CloudFront OAC para el bundle React; Amazon ECR para imágenes Docker; Supabase Storage (`book-covers`, `book-images`, `avatars`) y Supabase PostgreSQL (23 tablas normalizadas con Alembic) para datos persistentes. Ningún contenedor almacena estado local.

### 3.5. Decisiones arquitectónicas ADR
Documentadas individualmente (ADR-001 a ADR-008) en [`docs/adr/README.md`](adr/README.md).

---

## Capítulo 4. Observabilidad, pruebas y optimización de costos

### 4.1. Monitoreo y registros
- **CloudWatch Logs:** Ingesta de logs JSON estructurados (`request_id`, `method`, `path`, `status_code`, `latency_ms`) desde el contenedor FastAPI.
- **CloudWatch Dashboard y Alarmas:** Panel unificado con CPU del ASG, `TargetResponseTime` p95 y `RequestCount` del ALB; alarmas SNS ante CPU > 80 %, errores HTTP 5xx > 10/min y `UnHealthyHostCount > 0`.

### 4.2. Pruebas de carga y resiliencia
- **Pruebas automatizadas ejecutadas localmente:**
  - Backend Pytest (`4 passed`): verifica `/health`, `/ready`, verificación JWT, RBAC 401/403, catálogo, CRUD admin, carrito, checkout transaccional idempotente, aislamiento entre clientes y devolución única de stock al cancelar.
  - Frontend Vitest (`5 passed`) + ESLint + compilación TypeScript/Vite: verifica `BookCard` en soles, carrito, validaciones Zod, `ProtectedRoute` y estados vacíos.
- **Pruebas de carga y resiliencia diseñadas:** Scripts k6 progresivos (10, 25, 50, 100 y hasta 200 VUs en `tests/load/`) y plan de caída controlada de EC2 y desconexión temporal de base de datos en [`docs/testing/README.md`](testing/README.md).

### 4.3. Estimación y optimización de costos
Comparativa detallada en [`docs/costs/README.md`](costs/README.md):
- **Entorno Económico de Demostración:** ~\$29 – \$67 USD/mes (omitiendo NAT Gateway redundante o usando Supabase Free/Pro según estabilidad requerida).
- **Entorno Escalable Alta Disponibilidad:** ~\$136 – \$190 USD/mes (2x `t3.small` Multi-AZ, ALB, NAT Gateway, S3+CloudFront, CloudWatch y Supabase Pro).

---

## Capítulo 5. Conclusiones

### 5.1. Conclusiones
1. La arquitectura de tres capas desacoplada (React + FastAPI + Supabase) permitió concentrar todas las reglas críticas de negocio (precios, descuentos, stock atómico, idempotencia y auditoría) en el servidor FastAPI, evitando manipulaciones desde el cliente.
2. El modelo relacional de 23 tablas gestionado exclusivamente con Alembic asegura integridad referencial, trazabilidad de inventario y compatibilidad con Supabase Auth y RLS.
3. La definición de infraestructura mediante Terraform y contenedores Docker stateless habilita el escalamiento horizontal automático en AWS sin pérdida de sesiones ni archivos.

### 5.2. Lecciones aprendidas y trabajo futuro
- **Lecciones aprendidas:** La compatibilidad entre SQLAlchemy y el Transaction Pooler de Supabase (Supavisor puerto 6543) requiere `NullPool` y desactivar sentencias preparadas en runtime, reservando la conexión directa (`5432`) para migraciones DDL con Alembic. Asimismo, se evidenció la diferencia crítica entre objetivos de diseño (`99.9 %` / `RPO 24h`) y las garantías reales de los planes gratuitos vs. comerciales del proveedor BaaS.
- **Trabajo futuro:** Incorporar pasarela de pagos real (Culqi/MercadoPago), webhooks de estado, pruebas E2E con Playwright en CI, caché distribuida con Amazon ElastiCache (Redis) para lecturas masivas del catálogo y despliegue multi-entorno automatizado con Terraform Workspaces.

### 5.3. Referencias
- Amazon Web Services. *AWS Well-Architected Framework*. https://docs.aws.amazon.com/wellarchitected/
- FastAPI Documentation. https://fastapi.tiangolo.com/
- SQLAlchemy 2.0 Documentation. https://docs.sqlalchemy.org/
- Supabase Documentation (Auth JWT / JWKS, Supavisor Connection Pooling, Storage, RLS). https://supabase.com/docs
- HashiCorp Terraform AWS Provider Documentation. https://registry.terraform.io/providers/hashicorp/aws/latest/docs
- Grafana k6 Load Testing Documentation. https://grafana.com/docs/k6/
