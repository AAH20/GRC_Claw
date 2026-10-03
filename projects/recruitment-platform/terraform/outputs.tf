# -----------------------------------------------------------------------------
# VPC Outputs
# -----------------------------------------------------------------------------

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_block
}

output "private_subnets" {
  description = "List of private subnet IDs"
  value       = module.vpc.private_subnets
}

output "public_subnets" {
  description = "List of public subnet IDs"
  value       = module.vpc.public_subnets
}

output "database_subnets" {
  description = "List of database subnet IDs"
  value       = module.vpc.database_subnets
}

output "nat_gateway_ids" {
  description = "List of NAT Gateway IDs"
  value       = module.vpc.nat_gateway_ids
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = module.vpc.igw_id
}

# -----------------------------------------------------------------------------
# EKS Outputs
# -----------------------------------------------------------------------------

output "eks_cluster_name" {
  description = "Name of the EKS cluster"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "Endpoint URL of the EKS cluster"
  value       = module.eks.cluster_endpoint
}

output "eks_cluster_certificate_authority_data" {
  description = "Base64 encoded certificate authority data for the EKS cluster"
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
  value       = { for k, v in module.eks.eks_managed_node_groups : k => v.node_group_arn }
}

output "eks_cluster_version" {
  description = "Kubernetes version of the EKS cluster"
  value       = module.eks.cluster_version
}

# -----------------------------------------------------------------------------
# RDS Outputs
# -----------------------------------------------------------------------------

output "rds_instance_endpoint" {
  description = "Connection endpoint for the RDS PostgreSQL instance"
  value       = module.rds.db_instance_endpoint
}

output "rds_instance_address" {
  description = "Hostname of the RDS PostgreSQL instance"
  value       = module.rds.db_instance_address
}

output "rds_instance_port" {
  description = "Port of the RDS PostgreSQL instance"
  value       = module.rds.db_instance_port
}

output "rds_instance_id" {
  description = "ID of the RDS PostgreSQL instance"
  value       = module.rds.db_instance_id
}

output "rds_instance_arn" {
  description = "ARN of the RDS PostgreSQL instance"
  value       = module.rds.db_instance_arn
}

output "rds_subnet_group_id" {
  description = "ID of the RDS subnet group"
  value       = module.rds.db_subnet_group_id
}

output "rds_security_group_id" {
  description = "Security group ID for the RDS instance"
  value       = aws_security_group.rds.id
}

# -----------------------------------------------------------------------------
# ElastiCache Outputs
# -----------------------------------------------------------------------------

output "elasticache_replication_group_id" {
  description = "ID of the ElastiCache replication group"
  value       = module.elasticache.replication_group_id
}

output "elasticache_primary_endpoint" {
  description = "Primary endpoint of the ElastiCache Redis cluster"
  value       = module.elasticache.primary_endpoint_address
}

output "elasticache_reader_endpoint" {
  description = "Reader endpoint of the ElastiCache Redis cluster"
  value       = module.elasticache.reader_endpoint_address
}

output "elasticache_port" {
  description = "Port of the ElastiCache Redis cluster"
  value       = module.elasticache.port
}

output "elasticache_auth_token" {
  description = "Auth token for ElastiCache Redis (sensitive)"
  value       = random_password.redis_auth_token.result
  sensitive   = true
}

output "elasticache_subnet_group_id" {
  description = "ID of the ElastiCache subnet group"
  value       = aws_elasticache_subnet_group.redis.id
}

output "elasticache_security_group_id" {
  description = "Security group ID for ElastiCache"
  value       = aws_security_group.elasticache.id
}

# -----------------------------------------------------------------------------
# S3 Outputs
# -----------------------------------------------------------------------------

output "s3_app_storage_bucket" {
  description = "Name of the application storage S3 bucket"
  value       = aws_s3_bucket.app_storage.id
}

output "s3_app_storage_arn" {
  description = "ARN of the application storage S3 bucket"
  value       = aws_s3_bucket.app_storage.arn
}

output "s3_backups_bucket" {
  description = "Name of the backups S3 bucket"
  value       = aws_s3_bucket.backups.id
}

output "s3_backups_arn" {
  description = "ARN of the backups S3 bucket"
  value       = aws_s3_bucket.backups.arn
}

# -----------------------------------------------------------------------------
# KMS Outputs
# -----------------------------------------------------------------------------

output "kms_key_eks_arn" {
  description = "ARN of the KMS key for EKS secrets encryption"
  value       = aws_kms_key.eks.arn
}

output "kms_key_rds_arn" {
  description = "ARN of the KMS key for RDS encryption"
  value       = aws_kms_key.rds.arn
}

output "kms_key_s3_arn" {
  description = "ARN of the KMS key for S3 encryption"
  value       = aws_kms_key.s3.arn
}

# -----------------------------------------------------------------------------
# IAM Outputs
# -----------------------------------------------------------------------------

output "irsa_role_arns" {
  description = "ARNs of the IAM roles for service accounts"
  value = {
    eks_admin                = module.eks_admin_irsa.iam_role_arn
    cert_manager             = module.cert_manager_irsa.iam_role_arn
    external_dns             = module.external_dns_irsa.iam_role_arn
    aws_load_balancer_controller = module.aws_load_balancer_controller_irsa.iam_role_arn
  }
}

# -----------------------------------------------------------------------------
# Backup Outputs
# -----------------------------------------------------------------------------

output "backup_vault_arn" {
  description = "ARN of the AWS Backup vault"
  value       = aws_backup_vault.main.arn
}

output "backup_plan_id" {
  description = "ID of the AWS Backup plan"
  value       = aws_backup_plan.main.id
}

# -----------------------------------------------------------------------------
# CloudWatch Outputs
# -----------------------------------------------------------------------------

output "cloudwatch_log_group_vpc_flow" {
  description = "Name of the CloudWatch log group for VPC flow logs"
  value       = aws_cloudwatch_log_group.vpc_flow.name
}

output "cloudwatch_log_group_redis_slow" {
  description = "Name of the CloudWatch log group for Redis slow logs"
  value       = aws_cloudwatch_log_group.redis_slow.name
}

# -----------------------------------------------------------------------------
# Common Tags
# -----------------------------------------------------------------------------

output "common_tags" {
  description = "Common tags applied to all resources"
  value       = local.common_tags
}
