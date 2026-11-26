resource "aws_launch_template" "backend" {
  name_prefix   = "${var.project_name}-${var.environment}-lt-"
  image_id      = data.aws_ami.al2023.id
  instance_type = var.instance_type

  iam_instance_profile {
    name = aws_iam_instance_profile.ec2_backend.name
  }

  vpc_security_group_ids = [aws_security_group.backend.id]

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required" # IMDSv2 obligatorio
    http_put_response_hop_limit = 2
  }

  user_data = base64encode(<<-EOF
    #!/bin/bash
    set -euo pipefail
    dnf update -y
    dnf install -y docker jq amazon-cloudwatch-agent
    systemctl enable --now docker

    REGION="${var.aws_region}"
    ECR_REPO="${aws_ecr_repository.backend.repository_url}"
    SECRET_ARN="${aws_secretsmanager_secret.backend_env.arn}"

    aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$(echo $ECR_REPO | cut -d/ -f1)"

    aws secretsmanager get-secret-value --region "$REGION" --secret-id "$SECRET_ARN" --query SecretString --output text \
      | jq -r 'to_entries | .[] | "\(.key)=\(.value)"' > /run/bookly.env
    chmod 600 /run/bookly.env

    docker pull "$ECR_REPO:latest" || true
    docker run -d --name bookly-backend --restart always \
      --env-file /run/bookly.env \
      --log-driver=awslogs \
      --log-opt awslogs-region="$REGION" \
      --log-opt awslogs-group="${aws_cloudwatch_log_group.backend.name}" \
      --log-opt awslogs-create-group=true \
      -p 8000:8000 \
      "$ECR_REPO:latest"
  EOF
  )

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.project_name}-${var.environment}-backend-ec2"
    }
  }
}
