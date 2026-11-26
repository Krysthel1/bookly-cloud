# Observabilidad y Monitoreo — BOOKLY

## 1. Logs Estructurados en Backend
El middleware `ObservabilityMiddleware` (`backend/app/middlewares/security.py`) emite una traza JSON por cada solicitud HTTP hacia `stdout`, lista para ser recolectada por el driver `awslogs` de Docker hacia **Amazon CloudWatch Logs** (`/bookly/<env>/backend`):

```json
{
  "event": "http_request",
  "request_id": "uuid",
  "method": "GET",
  "path": "/api/v1/books",
  "status_code": 200,
  "latency_ms": 14.32,
  "client_ip": "10.0.1.24"
}
```

## 2. Métricas y Alarmas en Amazon CloudWatch (`infrastructure/terraform/monitoring.tf`)
- **EC2 / Auto Scaling:** `CPUUtilization` promedio del ASG (política de escalamiento al 65 % y alarma crítica > 80 %).
- **Memoria:** Recolectada mediante `amazon-cloudwatch-agent` con rol `CloudWatchAgentServerPolicy`.
- **Application Load Balancer:** `TargetResponseTime` (p95), `RequestCount`, `HTTPCode_Target_5XX_Count` (alarma > 10/min) y `UnHealthyHostCount` (alarma > 0).
- **Notificaciones:** Tópico SNS (`bookly-<env>-alerts`) con suscripción por correo opcional.
