# ─── General ──────────────────────────────────────────────────────────────────

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "gated-communities"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "owner" {
  description = "Team or individual owning these resources"
  type        = string
  default     = "platform-team"
}

# ─── VPC ──────────────────────────────────────────────────────────────────────

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

# ─── EKS ──────────────────────────────────────────────────────────────────────

variable "eks_cluster_version" {
  description = "Kubernetes version for the EKS cluster"
  type        = string
  default     = "1.29"
}

variable "eks_node_instance_types" {
  description = "Instance types for EKS worker nodes"
  type        = list(string)
  default     = ["t3.large"]
}

variable "eks_node_desired_size" {
  description = "Desired number of worker nodes"
  type        = number
  default     = 2
}

variable "eks_node_min_size" {
  description = "Minimum number of worker nodes"
  type        = number
  default     = 1
}

variable "eks_node_max_size" {
  description = "Maximum number of worker nodes"
  type        = number
  default     = 5
}

# ─── RDS ──────────────────────────────────────────────────────────────────────

variable "rds_engine" {
  description = "Database engine"
  type        = string
  default     = "postgres"
}

variable "rds_engine_version" {
  description = "Database engine version"
  type        = string
  default     = "16.3"
}

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "rds_allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 100
}

variable "rds_db_name" {
  description = "Name of the default database"
  type        = string
  default     = "gated_communities"
}

variable "rds_username" {
  description = "Master username for the database"
  type        = string
  default     = "gc_admin"
}

variable "rds_password" {
  description = "Master password for the database"
  type        = string
  sensitive   = true
}

# ─── ElastiCache ──────────────────────────────────────────────────────────────

variable "elasticache_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "elasticache_num_nodes" {
  description = "Number of cache nodes"
  type        = number
  default     = 2
}
