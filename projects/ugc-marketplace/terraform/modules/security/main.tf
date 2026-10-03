# =============================================================================
# Security Module — Security Groups & KMS Keys
# =============================================================================

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block of the VPC"
  type        = string
}

variable "eks_cluster_security_group_id" {
  description = "Security group ID of the EKS cluster"
  type        = string
  default     = ""
}

variable "rds_engine" {
  description = "RDS engine type"
  type        = string
  default     = "postgres"
}

variable "rds_engine_version" {
  description = "RDS engine version"
  type        = string
  default     = "16.2"
}

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.r6g.large"
}

variable "rds_port" {
  description = "RDS port"
  type        = number
  default     = 5432
}

variable "elasticache_engine" {
  description = "ElastiCache engine type"
  type        = string
  default     = "redis"
}

variable "elasticache_engine_version" {
  description = "ElastiCache engine version"
  type        = string
  default     = "7.1"
}

variable "elasticache_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.r6g.large"
}

variable "elasticache_port" {
  description = "ElastiCache port"
  type        = number
  default     = 6379
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# -----------------------------------------------------------------------------
# KMS Keys
# -----------------------------------------------------------------------------

resource "aws_kms_key" "eks" {
  description             = "KMS key for EKS secrets encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-eks-kms"
  })
}

resource "aws_kms_alias" "eks" {
  name          = "alias/${var.name_prefix}-eks"
  target_key_id = aws_kms_key.eks.key_id
}

resource "aws_kms_key" "rds" {
  description             = "KMS key for RDS encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-rds-kms"
  })
}

resource "aws_kms_alias" "rds" {
  name          = "alias/${var.name_prefix}-rds"
  target_key_id = aws_kms_key.rds.key_id
}

resource "aws_kms_key" "elasticache" {
  description             = "KMS key for ElastiCache encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-elasticache-kms"
  })
}

resource "aws_kms_alias" "elasticache" {
  name          = "alias/${var.name_prefix}-elasticache"
  target_key_id = aws_kms_key.elasticache.key_id
}

resource "aws_kms_key" "s3" {
  description             = "KMS key for S3 encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-s3-kms"
  })
}

resource "aws_kms_alias" "s3" {
  name          = "alias/${var.name_prefix}-s3"
  target_key_id = aws_kms_key.s3.key_id
}

# -----------------------------------------------------------------------------
# Security Groups
# -----------------------------------------------------------------------------

# EKS Node Security Group
resource "aws_security_group" "eks_nodes" {
  name_prefix = "${var.name_prefix}-eks-node-"
  description = "Security group for EKS worker nodes"
  vpc_id      = var.vpc_id

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-eks-node-sg"
  })

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_vpc_security_group_ingress_rule" "eks_nodes_self" {
  security_group_id = aws_security_group.eks_nodes.id
  description       = "Allow nodes to communicate with each other"
  from_port         = 0
  to_port           = 65535
  ip_protocol       = "-1"
  referenced_security_group_id = aws_security_group.eks_nodes.id
}

resource "aws_vpc_security_group_ingress_rule" "eks_nodes_cluster" {
  security_group_id = aws_security_group.eks_nodes.id
  description       = "Allow worker Kubelets and pods to receive communication from the cluster control plane"
  from_port         = 1025
  to_port           = 65535
  ip_protocol       = "tcp"
  referenced_security_group_id = var.eks_cluster_security_group_id
}

resource "aws_vpc_security_group_egress_rule" "eks_nodes_all" {
  security_group_id = aws_security_group.eks_nodes.id
  description       = "Allow all outbound traffic from nodes"
  from_port         = 0
  to_port           = 0
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}

# RDS Security Group
resource "aws_security_group" "rds" {
  name_prefix = "${var.name_prefix}-rds-"
  description = "Security group for RDS PostgreSQL"
  vpc_id      = var.vpc_id

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-rds-sg"
  })

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_vpc_security_group_ingress_rule" "rds_eks" {
  security_group_id = aws_security_group.rds.id
  description       = "Allow EKS nodes to connect to RDS"
  from_port         = var.rds_port
  to_port           = var.rds_port
  ip_protocol       = "tcp"
  referenced_security_group_id = aws_security_group.eks_nodes.id
}

resource "aws_vpc_security_group_ingress_rule" "rds_vpc" {
  security_group_id = aws_security_group.rds.id
  description       = "Allow VPC CIDR to connect to RDS"
  from_port         = var.rds_port
  to_port           = var.rds_port
  ip_protocol       = "tcp"
  cidr_ipv4         = var.vpc_cidr
}

resource "aws_vpc_security_group_egress_rule" "rds_all" {
  security_group_id = aws_security_group.rds.id
  description       = "Allow all outbound traffic from RDS"
  from_port         = 0
  to_port           = 0
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}

# ElastiCache Security Group
resource "aws_security_group" "elasticache" {
  name_prefix = "${var.name_prefix}-elasticache-"
  description = "Security group for ElastiCache Redis"
  vpc_id      = var.vpc_id

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-elasticache-sg"
  })

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_vpc_security_group_ingress_rule" "elasticache_eks" {
  security_group_id = aws_security_group.elasticache.id
  description       = "Allow EKS nodes to connect to ElastiCache"
  from_port         = var.elasticache_port
  to_port           = var.elasticache_port
  ip_protocol       = "tcp"
  referenced_security_group_id = aws_security_group.eks_nodes.id
}

resource "aws_vpc_security_group_ingress_rule" "elasticache_vpc" {
  security_group_id = aws_security_group.elasticache.id
  description       = "Allow VPC CIDR to connect to ElastiCache"
  from_port         = var.elasticache_port
  to_port           = var.elasticache_port
  ip_protocol       = "tcp"
  cidr_ipv4         = var.vpc_cidr
}

resource "aws_vpc_security_group_egress_rule" "elasticache_all" {
  security_group_id = aws_security_group.elasticache.id
  description       = "Allow all outbound traffic from ElastiCache"
  from_port         = 0
  to_port           = 0
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------

output "eks_kms_key_arn" {
  description = "ARN of the EKS KMS key"
  value       = aws_kms_key.eks.arn
}

output "eks_kms_key_id" {
  description = "ID of the EKS KMS key"
  value       = aws_kms_key.eks.key_id
}

output "rds_kms_key_arn" {
  description = "ARN of the RDS KMS key"
  value       = aws_kms_key.rds.arn
}

output "rds_kms_key_id" {
  description = "ID of the RDS KMS key"
  value       = aws_kms_key.rds.key_id
}

output "elasticache_kms_key_arn" {
  description = "ARN of the ElastiCache KMS key"
  value       = aws_kms_key.elasticache.arn
}

output "elasticache_kms_key_id" {
  description = "ID of the ElastiCache KMS key"
  value       = aws_kms_key.elasticache.key_id
}

output "s3_kms_key_arn" {
  description = "ARN of the S3 KMS key"
  value       = aws_kms_key.s3.arn
}

output "s3_kms_key_id" {
  description = "ID of the S3 KMS key"
  value       = aws_kms_key.s3.key_id
}

output "eks_nodes_security_group_id" {
  description = "Security group ID for EKS nodes"
  value       = aws_security_group.eks_nodes.id
}

output "rds_security_group_id" {
  description = "Security group ID for RDS"
  value       = aws_security_group.rds.id
}

output "elasticache_security_group_id" {
  description = "Security group ID for ElastiCache"
  value       = aws_security_group.elasticache.id
}
