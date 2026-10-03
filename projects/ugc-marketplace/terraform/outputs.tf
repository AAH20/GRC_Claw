# =============================================================================
# UGC Marketplace — Output Variables
# =============================================================================

# -----------------------------------------------------------------------------
# VPC / Networking
# -----------------------------------------------------------------------------

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_block
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = module.vpc.private_subnet_ids
}

output "database_subnet_ids" {
  description = "List of database subnet IDs"
  value       = module.vpc.database_subnet_ids
}

output "nat_gateway_ids" {
  description = "List of NAT Gateway IDs"
  value       = module.vpc.nat_gateway_ids
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = module.vpc.internet_gateway_id
}

# -----------------------------------------------------------------------------
# EKS (Kubernetes)
# -----------------------------------------------------------------------------

output "eks_cluster_name" {
  description = "Name of the EKS cluster"
  value       = module.eks.cluster_name
}

output "eks_cluster_arn" {
  description = "ARN of the EKS cluster"
  value       = module.eks.cluster_arn
}

output "eks_cluster_endpoint" {
  description = "Endpoint URL for the EKS cluster API server"
  value       = module.eks.cluster_endpoint
}

output "eks_cluster_certificate_authority_data" {
  description = "Base64-encoded certificate authority data for the EKS cluster"
  value       = module.eks.cluster_certificate_authority_data
}

output "eks_cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = module.eks.cluster_security_group_id
}

output "eks_oidc_provider_arn" {
  description = "ARN of the OIDC provider for the EKS cluster"
  value       = module.eks.oidc_provider_arn
}

output "eks_node_group_arns" {
  description = "ARNs of the EKS managed node groups"
  value       = module.eks.node_group_arns
}

output "eks_node_group_ids" {
  description = "IDs of the EKS managed node groups"
  value       = module.eks.node_group_ids
}

output "eks_alb_dns_name" {
  description = "DNS name of the ALB created by the AWS Load Balancer Controller"
  value       = module.eks.alb_dns_name
}

output "eks_kubeconfig_command" {
  description = "AWS CLI command to update kubeconfig for the EKS cluster"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}

# -----------------------------------------------------------------------------
# RDS (PostgreSQL)
# -----------------------------------------------------------------------------

output "rds_instance_id" {
  description = "ID of the RDS instance"
  value       = module.rds.instance_id
}

output "rds_instance_arn" {
  description = "ARN of the RDS instance"
  value       = module.rds.instance_arn
}

output "rds_instance_endpoint" {
  description = "Connection endpoint for the RDS instance"
  value       = module.rds.instance_endpoint
}

output "rds_instance_address" {
  description = "Hostname of the RDS instance"
  value       = module.rds.instance_address
}

output "rds_instance_port" {
  description = "Port of the RDS instance"
  value       = module.rds.instance_port
}

output "rds_database_name" {
  description = "Name of the default database"
  value       = module.rds.database_name
}

output "rds_master_username" {
  description = "Master username for the RDS instance"
  value       = module.rds.master_username
}

output "rds_security_group_id" {
  description = "Security group ID for the RDS instance"
  value       = module.rds.security_group_id
}

# -----------------------------------------------------------------------------
# ElastiCache (Redis)
# -----------------------------------------------------------------------------

output "elasticache_cluster_id" {
  description = "ID of the ElastiCache cluster"
  value       = module.elasticache.cluster_id
}

output "elasticache_cluster_arn" {
  description = "ARN of the ElastiCache cluster"
  value       = module.elasticache.cluster_arn
}

output "elasticache_primary_endpoint" {
  description = "Primary endpoint for the ElastiCache cluster"
  value       = module.elasticache.primary_endpoint
}

output "elasticache_reader_endpoint" {
  description = "Reader endpoint for the ElastiCache cluster"
  value       = module.elasticache.reader_endpoint
}

output "elasticache_port" {
  description = "Port for the ElastiCache cluster"
  value       = module.elasticache.port
}

output "elasticache_security_group_id" {
  description = "Security group ID for the ElastiCache cluster"
  value       = module.elasticache.security_group_id
}

# -----------------------------------------------------------------------------
# S3 (Storage)
# -----------------------------------------------------------------------------

output "s3_app_bucket_id" {
  description = "ID of the application data S3 bucket"
  value       = module.s3.app_bucket_id
}

output "s3_app_bucket_arn" {
  description = "ARN of the application data S3 bucket"
  value       = module.s3.app_bucket_arn
}

output "s3_app_bucket_domain_name" {
  description = "Domain name of the application data S3 bucket"
  value       = module.s3.app_bucket_domain_name
}

output "s3_media_bucket_id" {
  description = "ID of the media/assets S3 bucket"
  value       = module.s3.media_bucket_id
}

output "s3_media_bucket_arn" {
  description = "ARN of the media/assets S3 bucket"
  value       = module.s3.media_bucket_arn
}

output "s3_media_bucket_domain_name" {
  description = "Domain name of the media/assets S3 bucket"
  value       = module.s3.media_bucket_domain_name
}

output "s3_logs_bucket_id" {
  description = "ID of the logs S3 bucket"
  value       = module.s3.logs_bucket_id
}

output "s3_logs_bucket_arn" {
  description = "ARN of the logs S3 bucket"
  value       = module.s3.logs_bucket_arn
}

# -----------------------------------------------------------------------------
# CloudFront (CDN)
# -----------------------------------------------------------------------------

output "cloudfront_distribution_id" {
  description = "ID of the CloudFront distribution"
  value       = module.cloudfront.distribution_id
}

output "cloudfront_distribution_arn" {
  description = "ARN of the CloudFront distribution"
  value       = module.cloudfront.distribution_arn
}

output "cloudfront_domain_name" {
  description = "Domain name of the CloudFront distribution"
  value       = module.cloudfront.domain_name
}

output "cloudfront_hosted_zone_id" {
  description = "Route 53 hosted zone ID for the CloudFront distribution"
  value       = module.cloudfront.hosted_zone_id
}

output "cloudfront_status" {
  description = "Status of the CloudFront distribution"
  value       = module.cloudfront.status
}

# -----------------------------------------------------------------------------
# Route 53 (DNS)
# -----------------------------------------------------------------------------

output "route53_zone_id" {
  description = "ID of the Route 53 hosted zone"
  value       = var.create_route53_records ? module.route53[0].zone_id : null
}

output "route53_record_fqdns" {
  description = "FQDNs of the Route 53 records"
  value       = var.create_route53_records ? module.route53[0].record_fqdns : null
}

# -----------------------------------------------------------------------------
# Security (KMS)
# -----------------------------------------------------------------------------

output "kms_key_eks_arn" {
  description = "ARN of the KMS key for EKS secrets encryption"
  value       = module.security.eks_kms_key_arn
}

output "kms_key_rds_arn" {
  description = "ARN of the KMS key for RDS encryption"
  value       = module.security.rds_kms_key_arn
}

output "kms_key_elasticache_arn" {
  description = "ARN of the KMS key for ElastiCache encryption"
  value       = module.security.elasticache_kms_key_arn
}

output "kms_key_s3_arn" {
  description = "ARN of the KMS key for S3 encryption"
  value       = module.security.s3_kms_key_arn
}

# -----------------------------------------------------------------------------
# Monitoring
# -----------------------------------------------------------------------------

output "cloudwatch_dashboard_name" {
  description = "Name of the CloudWatch dashboard"
  value       = module.monitoring.dashboard_name
}

output "cloudwatch_dashboard_arn" {
  description = "ARN of the CloudWatch dashboard"
  value       = module.monitoring.dashboard_arn
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic for alarm notifications"
  value       = module.monitoring.sns_topic_arn
}

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------

output "infrastructure_summary" {
  description = "Summary of all provisioned infrastructure"
  value = {
    project_name     = var.project_name
    environment      = var.environment
    aws_region       = var.aws_region
    vpc_id           = module.vpc.vpc_id
    eks_cluster_name = module.eks.cluster_name
    rds_endpoint     = module.rds.instance_endpoint
    elasticache_endpoint = module.elasticache.primary_endpoint
    cloudfront_domain   = module.cloudfront.domain_name
    s3_buckets = {
      app   = module.s3.app_bucket_id
      media = module.s3.media_bucket_id
      logs  = module.s3.logs_bucket_id
    }
  }
}
