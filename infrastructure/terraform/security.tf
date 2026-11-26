# Security Group del Application Load Balancer (público)
resource "aws_security_group" "alb" {
  name        = "${var.project_name}-${var.environment}-alb-sg"
  description = "Permite tráfico HTTP/HTTPS hacia el Application Load Balancer"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP desde internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS desde internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Security Group de las instancias backend (privado, solo acepta tráfico del ALB)
resource "aws_security_group" "backend" {
  name        = "${var.project_name}-${var.environment}-backend-sg"
  description = "Permite puerto 8000 únicamente desde el ALB y salida TLS/HTTPS hacia Supabase y ECR"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Tráfico FastAPI desde el ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  # Salida hacia servicio externo Supabase (HTTPS 443, Supavisor Pooler 6543, Direct TLS 5432) y ECR/CloudWatch
  egress {
    description = "Salida TLS hacia servicios externos (Supabase, ECR, CloudWatch)"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Salida PostgreSQL TLS hacia Supabase Transaction Pooler"
    from_port   = 6543
    to_port     = 6543
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Salida PostgreSQL TLS directa hacia Supabase"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Contenedor de secretos en AWS Secrets Manager (poblar valores fuera de Terraform o vía consola/CLI)
resource "aws_secretsmanager_secret" "backend_env" {
  name        = "${var.project_name}/${var.environment}/backend-secrets"
  description = "Variables sensibles del backend BOOKLY (DATABASE_URL, SUPABASE_SECRET_KEY, etc.)"
}

# Rol IAM con privilegios mínimos para instancias EC2
resource "aws_iam_role" "ec2_backend" {
  name = "${var.project_name}-${var.environment}-ec2-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action    = "sts:AssumeRole"
        Effect    = "Allow"
        Principal = { Service = "ec2.amazonaws.com" }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.ec2_backend.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy_attachment" "cloudwatch_agent" {
  role       = aws_iam_role.ec2_backend.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

resource "aws_iam_role_policy_attachment" "ecr_readonly" {
  role       = aws_iam_role.ec2_backend.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_role_policy" "read_secrets" {
  name = "${var.project_name}-${var.environment}-read-secrets"
  role = aws_iam_role.ec2_backend.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = [aws_secretsmanager_secret.backend_env.arn]
      }
    ]
  })
}

resource "aws_iam_instance_profile" "ec2_backend" {
  name = "${var.project_name}-${var.environment}-ec2-profile"
  role = aws_iam_role.ec2_backend.name
}
