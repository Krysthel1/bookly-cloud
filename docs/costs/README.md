# Estimación y Optimización de Costos Mensuales (AWS + Supabase)

> **Nota de rigor:** Ningún servicio productivo se asume 100 % gratuito de forma indefinida; los valores corresponden a tarifas públicas referenciales de AWS (`us-east-1`) y Supabase para contraste técnico-económico.

## Escenario 1: Entorno Económico de Desarrollo y Demostración

Diseñado para validación académica y tráfico bajo (~50 GB transferencia/mes).

| Servicio | Especificación | Costo Mensual Estimado (USD) |
|---|---|---|
| **Amazon S3 + CloudFront** | 1 GB almacenamiento, < 20 GB salida (capa gratuita inicial o tráfico bajo) | \$1.00 – \$3.00 |
| **Amazon EC2 (1–2 instancias)** | 1x `t3.micro` (o `t3.small` bajo demanda ~\$15.18) en subred pública temporal o sin NAT Gateway para demo | \$8.00 – \$16.00 |
| **Application Load Balancer** | 1 ALB (~16.20 fijo + LCU mínimas) | \$18.00 |
| **NAT Gateway** | *Omitido en modo demo* (instancias con IP pública restringida por SG) o 1 NAT (~32.40 + tráfico) | \$0.00 (sin NAT) / \$35.00 (con NAT) |
| **Amazon ECR + CloudWatch** | < 2 GB imágenes + logs 14 días + 3 alarmas | \$2.00 – \$5.00 |
| **Supabase (Plan Free / Pro)** | Free (\$0, con pausa por inactividad y sin SLA) o Pro (\$25/mes recomendado para demo estable) | \$0.00 – \$25.00 |
| **Total Estimado Entorno Económico** | | **~\$29.00 – \$67.00 / mes** |

---

## Escenario 2: Entorno Escalable de Alta Disponibilidad (Producción)

Alineado con la arquitectura Terraform completa en 2 Zonas de Disponibilidad:

| Servicio | Especificación | Costo Mensual Estimado (USD) |
|---|---|---|
| **Amazon S3 + CloudFront (OAC)** | 5 GB almacenamiento + 100 GB transferencia + invalidaciones | \$10.00 |
| **Amazon EC2 (Auto Scaling Group)** | 2x `t3.small` continuas (Multi-AZ) + picos hasta 4 instancias | \$35.00 – \$55.00 |
| **Application Load Balancer** | 1 ALB Multi-AZ + LCUs moderadas | \$22.00 |
| **NAT Gateway (1 o 2 AZs)** | 1 NAT Gateway (\$32.40 base + \$0.045/GB) o 2 NAT para HA estricta (\$64.80+) | \$36.00 – \$70.00 |
| **Amazon ECR + Secrets Manager + CloudWatch** | ECR escaneo, 1 secreto (\$0.40), logs, dashboard y alarmas | \$8.00 |
| **Supabase Pro** | 8 GB DB, 100 GB Storage, 100k MAU Auth, backups diarios, sin pausa automática | \$25.00 |
| **Total Estimado Alta Disponibilidad** | | **~\$136.00 – \$190.00 / mes** |

## Estrategias de Optimización Aplicadas
1. **Frontend estático en S3 + CloudFront:** evita instancias EC2 sirviendo archivos estáticos y aprovecha caché CDN.
2. **Supavisor Transaction Pooler:** permite escalar instancias FastAPI sin contratar instancias RDS Multi-AZ costosas (ahorro frente a RDS PostgreSQL Multi-AZ > \$60–\$120/mes).
3. **NAT Gateway único vs Multi-AZ:** en desarrollo/pruebas se usa 1 NAT Gateway (o variable `enable_nat_gateway = false`), reservando NAT redundante por AZ únicamente para producción crítica.
4. **Retención acotada en CloudWatch Logs:** 14 días para evitar acumulación indefinida de almacenamiento de logs.
