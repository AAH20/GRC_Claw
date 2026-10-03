# ─── VPC Outputs ──────────────────────────────────────────────────────────────

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = module.vpc.private_subnet_ids
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

# ─── EKS Outputs ──────────────────────────────────────────────────────────────

output "eks_cluster_name" {
  description = "Name of the EKS cluster"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "Endpoint for the EKS cluster API server"
  value       = module.eks.cluster_endpoint
}

output "eks_cluster_certificate_authority" {
  description = "Base64 encoded certificate authority data"
  value       = module.eks.cluster_certificate_authority
}

output "eks_cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = module.eks.cluster_security_group_id
}

output "eks_node_role_arn" {
  description = "ARN of the IAM role for EKS worker nodes"
  value       = module.eks.node_role_arn
}

# ─── RDS Outputs ──────────────────────────────────────────────────────────────

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

output "rds_instance_id" {
  description = "ID of the RDS instance"
  value       = module.rds.instance_id
}

# ─── ElastiCache Outputs ──────────────────────────────────────────────────────

output "elasticache_cluster_id" {
  description = "ID of the ElastiCache cluster"
  value       = module.elasticache.cluster_id
}

output "elasticache_primary_endpoint" {
  description = "Primary endpoint of the ElastiCache cluster"
  value       = module.elasticache.primary_endpoint
}

output "elasticache_port" {
  description = "Port of the ElastiCache cluster"
  value       = module.elasticache.port
}

# ─── S3 Outputs ───────────────────────────────────────────────────────────────

output "s3_bucket_names" {
  description = "Names of the created S3 buckets"
  value       = module.s3.bucket_names
}

output "s3_bucket_arns" {
  description = "ARNs of the created S3 buckets"
  value       = module.s3.bucket_arns
}
