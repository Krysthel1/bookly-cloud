variable "aws_region" {
  description = "Región AWS de despliegue"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Nombre del proyecto"
  type        = string
  default     = "bookly"
}

variable "environment" {
  description = "Entorno de despliegue (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "bucket_suffix" {
  description = "Sufijo único global para el bucket S3 del frontend"
  type        = string
  default     = "pe-2026"
}

variable "vpc_cidr" {
  description = "Bloque CIDR principal de la VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "instance_type" {
  description = "Tipo de instancia EC2 para el backend FastAPI"
  type        = string
  default     = "t3.small"
}

variable "asg_min_size" {
  description = "Número mínimo de instancias EC2"
  type        = number
  default     = 2
}

variable "asg_max_size" {
  description = "Número máximo de instancias EC2"
  type        = number
  default     = 4
}

variable "asg_desired_capacity" {
  description = "Capacidad deseada inicial del Auto Scaling Group"
  type        = number
  default     = 2
}

variable "enable_nat_gateway" {
  description = "Habilitar NAT Gateway para salida a internet de subredes privadas hacia Supabase"
  type        = bool
  default     = true
}

variable "nat_gateway_count" {
  description = "Cantidad de NAT Gateways (1 para entorno económico A, 2 para alta disponibilidad B)"
  type        = number
  default     = 2
}

variable "log_retention_days" {
  description = "Retención en días para CloudWatch Logs (14 entorno económico, 30 HA)"
  type        = number
  default     = 30
}

variable "monthly_budget_usd" {
  description = "Presupuesto mensual en USD para alertas AWS Budgets"
  type        = number
  default     = 200
}

variable "alarm_email" {
  description = "Correo opcional para notificaciones CloudWatch/SNS"
  type        = string
  default     = ""
}
