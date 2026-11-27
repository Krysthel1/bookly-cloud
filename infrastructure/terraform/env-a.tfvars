# Entorno A: Económico / Demostración
environment          = "dev"
instance_type        = "t3.small"
asg_min_size         = 1
asg_max_size         = 2
asg_desired_capacity = 1
enable_nat_gateway   = true
nat_gateway_count    = 1
log_retention_days   = 14
monthly_budget_usd   = 75
