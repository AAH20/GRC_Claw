# -----------------------------------------------------------------------------
# General
# -----------------------------------------------------------------------------

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "recruitment-platform"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*$", var.project_name))
    error_message = "Project name must start with a lowercase letter and contain only lowercase letters, numbers, and hyphens."
  }
}

variable "environment" {
  description = "Deployment environment (development, staging, production)"
  type        = string
  default     = "development"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production."
  }
}

variable "aws_region" {
  description = "AWS region for resource deployment"
  type        = string
  default     = "us-east-1"
}

variable "owner" {
  description = "Team or individual responsible for the infrastructure"
  type        = string
  default     = "platform-team"
}

variable "cost_center" {
  description = "Cost center for billing purposes"
  type        = string
  default     = "engineering"
}

# -----------------------------------------------------------------------------
# VPC
# -----------------------------------------------------------------------------

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid CIDR block."
  }
}

variable "az_count" {
  description = "Number of Availability Zones to use"
  type        = number
  default     = 3

  validation {
    condition     = var.az_count >= 2 && var.az_count <= 6
    error_message = "AZ count must be between 2 and 6."
  }
}

# -----------------------------------------------------------------------------
# EKS
# -----------------------------------------------------------------------------

variable "kubernetes_version" {
  description = "Kubernetes version for the EKS cluster"
  type        = string
  default     = "1.28"
}

variable "eks_public_access" {
  description = "Enable public access to the EKS API server endpoint"
  type        = bool
  default     = false
}

variable "eks_node_instance_types" {
  description = "Instance types for the general EKS managed node group"
  type        = list(string)
  default     = ["m6i.large"]
}

variable "eks_node_min_size" {
  description = "Minimum number of nodes in the general node group"
  type        = number
  default     = 2
}

variable "eks_node_max_size" {
  description = "Maximum number of nodes in the general node group"
  type        = number
  default     = 5
}

variable "eks_node_desired_size" {
  description = "Desired number of nodes in the general node group"
  type        = number
  default     = 3
}

variable "eks_spot_instance_types" {
  description = "Instance types for the spot EKS managed node group"
  type        = list(string)
  default     = ["m6i.large", "m5.large", "m5a.large"]
}

variable "eks_spot_min_size" {
  description = "Minimum number of nodes in the spot node group"
  type        = number
  default     = 0
}

variable "eks_spot_max_size" {
  description = "Maximum number of nodes in the spot node group"
  type        = number
  default     = 10
}

variable "eks_spot_desired_size" {
  description = "Desired number of nodes in the spot node group"
  type        = number
  default     = 2
}

# -----------------------------------------------------------------------------
# RDS
# -----------------------------------------------------------------------------

variable "rds_engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "15.4"
}

variable "rds_instance_class" {
  description = "Instance class for the RDS PostgreSQL instance"
  type        = string
  default     = "db.t3.medium"
}

variable "rds_allocated_storage" {
  description = "Allocated storage for RDS in GB"
  type        = number
  default     = 100
}

variable "rds_max_allocated_storage" {
  description = "Maximum allocated storage for RDS autoscaling in GB"
  type        = number
  default     = 500
}

variable "rds_database_name" {
  description = "Name of the default database to create"
  type        = string
  default     = "recruitment_platform"
}

variable "rds_username" {
  description = "Master username for the RDS instance"
  type        = string
  default     = "recruitment_admin"
}

variable "rds_backup_retention" {
  description = "Number of days to retain RDS backups"
  type        = number
  default     = 30

  validation {
    condition     = var.rds_backup_retention >= 7 && var.rds_backup_retention <= 35
    error_message = "RDS backup retention must be between 7 and 35 days."
  }
}

# -----------------------------------------------------------------------------
# ElastiCache
# -----------------------------------------------------------------------------

variable "elasticache_engine_version" {
  description = "Redis engine version"
  type        = string
  default     = "7.0"
}

variable "elasticache_node_type" {
  description = "Node type for ElastiCache Redis"
  type        = string
  default     = "cache.t3.medium"
}

variable "elasticache_num_cache_clusters" {
  description = "Number of cache clusters in the replication group"
  type        = number
  default     = 2

  validation {
    condition     = var.elasticache_num_cache_clusters >= 1 && var.elasticache_num_cache_clusters <= 6
    error_message = "Number of cache clusters must be between 1 and 6."
  }
}

# -----------------------------------------------------------------------------
# S3
# -----------------------------------------------------------------------------

variable "backup_retention_days" {
  description = "Number of days to retain backups in the backup S3 bucket"
  type        = number
  default     = 90

  validation {
    condition     = var.backup_retention_days > 0
    error_message = "Backup retention days must be greater than 0."
  }
}
