output "vpc_id" {
  value = aws_vpc.main.id
}

output "frontend_s3_bucket" {
  value = aws_s3_bucket.frontend.bucket
}

output "cloudfront_domain_name" {
  value = aws_cloudfront_distribution.frontend.domain_name
}

output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.frontend.id
}

output "ecr_repository_url" {
  value = aws_ecr_repository.backend.repository_url
}

output "alb_dns_name" {
  value = aws_lb.backend.dns_name
}

output "autoscaling_group_name" {
  value = aws_autoscaling_group.backend.name
}

output "cloudwatch_log_group" {
  value = aws_cloudwatch_log_group.backend.name
}
