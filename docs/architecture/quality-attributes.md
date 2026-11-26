# Atributos de Calidad y Objetivos de Servicio (BOOKLY)

| Atributo | Objetivo Planteado | Mecanismo en BOOKLY | Garantía Real del Proveedor / Limitación |
|---|---|---|---|
| **Disponibilidad** | **99.9 %** | ALB Multi-AZ + ASG (`min=2`) + health checks `/health` | AWS EC2/ALB Multi-AZ soporta 99.99 %; **Supabase Free no incluye SLA** y pausa proyectos inactivos (7 días). Para cumplir 99.9 % real se requiere **Supabase Pro**. |
| **Latencia p95** | **< 500 ms** en consultas principales | Índices en `books(title, isbn, slug)`, paginación SQL, Supavisor Pooler (`6543`) y caché JWKS | Medible mediante k6 (`tests/load/catalog.js`) y `TargetResponseTime` p95 en CloudWatch. Depende de la proximidad geográfica entre AWS (`us-east-1`) y la región Supabase. |
| **Tasa de errores** | **< 1 %** | Validación Pydantic, transacciones ACID, idempotencia y manejo centralizado de errores | Monitoreado en CloudWatch (`HTTPCode_Target_5XX_Count`) y umbrales `http_req_failed < 0.01` en k6. |
| **Escalabilidad horizontal** | Automática (2 a 4 instancias) | Backend 100 % stateless + ASG Target Tracking CPU 65 % | Limitada por el máximo de conexiones del plan Supabase (`Supavisor` mitiga el agotamiento de conexiones). |
| **RTO** | **60 minutos** | IaC con Terraform + imágenes inmutables en ECR + Instance Refresh | Reconstrucción completa automatizable en < 20 min mediante `terraform apply`. |
| **RPO** | **24 horas** | Backups automáticos diarios de PostgreSQL en Supabase | Supabase Free **no** ofrece backups automáticos garantizados ni PITR; el RPO de 24 h exige **Supabase Pro** (backups diarios) o respaldo externo programado `pg_dump`. |
