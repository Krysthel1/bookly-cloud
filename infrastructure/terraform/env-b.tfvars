# Entorno B: Escalable de Alta Disponibilidad (2 AZ)
environment          = "prod"
instance_type        = "t3.medium"
asg_min_size         = 2
asg_max_size         = 4
asg_desired_capacity = 2
enable_nat_gateway   = true
nat_gateway_count    = 2
log_retention_days   = 30
monthly_budget_usd   = 200
