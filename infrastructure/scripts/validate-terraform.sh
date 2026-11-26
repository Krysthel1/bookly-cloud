#!/usr/bin/env bash
# Script de verificación previa al despliegue en AWS (NO ejecuta apply sin autorización)
set -euo pipefail

cd "$(dirname "$0")/../terraform"
terraform init -backend=false
terraform validate
echo "[OK] Configuración Terraform validada sin crear recursos de pago."
