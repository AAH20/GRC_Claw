# =============================================================================
# UGC Marketplace — Input Variables
# =============================================================================

# -----------------------------------------------------------------------------
# General
# -----------------------------------------------------------------------------

variable "project_name" {
  description = "Name of the project, used as a prefix for all resources"
  type        = string
  default     = "ugc-marketplace"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*$", var.project_name))
    error_message = "Project name must start with a lowercase letter and contain only lowercase letters, numbers, and hyphens."
  }
}

variable "environment" {
  description = "Deployment environment (e.g., dev, staging, prod)"
  type        = string
  default     = "prod"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "aws_region" {
  description = "AWS region for primary resource deployment"
  type        = string
  default     = "us-east-1"
}

variable "owner" {
  description = "Team or individual responsible for this infrastructure"
  type        = string
  default     = "platform-team"
}

variable "cost_center" {
  description = "Cost center for billing and chargeback purposes"
  type        = string
  default     = "engineering"
}

# -----------------------------------------------------------------------------
# VPC / Networking
# -----------------------------------------------------------------------------

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block."
  }
}

variable "availability_zone_count" {
  description = "Number of availability zones to use (1-3)"
  type        = number
  default     = 3

  validation {
    condition     = var.availability_zone_count >= 1 && var.availability_zone_count <= 3
    error_message = "Availability zone count must be between 1 and 3."
  }
}

variable "enable_nat_gateway" {
  description = "Whether to create NAT Gateways for private subnet internet access"
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "Whether to use a single NAT Gateway (cost-saving for non-prod)"
  type        = bool
  default     = false
}

variable "enable_vpc_flow_logs" {
  description = "Whether to enable VPC Flow Logs"
  type        = bool
  default     = true
}

variable "flow_logs_retention_days" {
  description = "Number of days to retain VPC Flow Logs in CloudWatch"
  type        = number
  default     = 30
}

# -----------------------------------------------------------------------------
# EKS (Kubernetes)
# -----------------------------------------------------------------------------

variable "eks_cluster_version" {
  description = "Kubernetes version for the EKS cluster"
  type        = string
  default     = "1.29"
}

variable "eks_cluster_endpoint_private_access" {
  description = "Whether the EKS cluster endpoint is accessible from within the VPC"
  type        = bool
  default     = true
}

variable "eks_cluster_endpoint_public_access" {
  description = "Whether the EKS cluster endpoint is accessible from the internet"
  type        = bool
  default     = false
}

variable "eks_cluster_endpoint_public_access_cidrs" {
  description = "CIDR blocks allowed to access the EKS public endpoint"
  type        = list(string)
  default     = []
}

variable "eks_cluster_enabled_log_types" {
  description = "List of EKS cluster log types to enable"
  type        = list(string)
  default     = ["api", "audit", "authenticator", "controllerManager", "scheduler"]
}

variable "eks_node_groups" {
  description = "Map of EKS managed node group configurations"
  type = map(object({
    name           = string
    instance_types = list(string)
    capacity_type  = string
    disk_size      = number
    min_size       = number
    max_size       = number
    desired_size   = number
    labels         = map(string)
    taints = list(object({
      key    = string
      value  = string
      effect = string
    }))
  }))

  default = {
    general = {
      name           = "general"
      instance_types = ["m6i.large"]
      capacity_type  = "ON_DEMAND"
      disk_size      = 50
      min_size       = 2
      max_size       = 6
      desired_size   = 3
      labels = {
        workload = "general"
      }
      taints = []
    }
    compute = {
      name           = "compute"
      instance_types = ["c6i.xlarge"]
      capacity_type  = "ON_DEMAND"
      disk_size      = 50
      min_size       = 1
      max_size       = 4
      desired_size   = 2
      labels = {
        workload = "compute"
      }
      taints = []
    }
  }
}

# -----------------------------------------------------------------------------
# RDS (PostgreSQL)
# -----------------------------------------------------------------------------

variable "rds_engine" {
  description = "Database engine for RDS"
  type        = string
  default     = "postgres"
}

variable "rds_engine_version" {
  description = "Database engine version"
  type        = string
  default     = "16.2"
}

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.r6g.large"
}

variable "rds_port" {
  description = "Port for the RDS instance"
  type        = number
  default     = 5432
}

variable "rds_database_name" {
  description = "Name of the default database to create"
  type        = string
  default     = "ugc_marketplace"
}

variable "rds_master_username" {
  description = "Master username for the RDS instance"
  type        = string
  default     = "ugc_admin"
}

variable "rds_master_password" {
  description = "Master password for the RDS instance (use a secrets manager in production)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "rds_allocated_storage" {
  description = "Initial allocated storage in GB"
  type        = number
  default     = 100
}

variable "rds_max_allocated_storage" {
  description = "Maximum allocated storage for autoscaling in GB"
  type        = number
  default     = 500
}

variable "rds_storage_type" {
  description = "Storage type for RDS"
  type        = string
  default     = "gp3"
}

variable "rds_storage_encrypted" {
  description = "Whether to encrypt RDS storage"
  type        = bool
  default     = true
}

variable "rds_multi_az" {
  description = "Whether to create a Multi-AZ RDS deployment"
  type        = bool
  default     = true
}

variable "rds_backup_retention_period" {
  description = "Number of days to retain automated backups"
  type        = number
  default     = 30
}

variable "rds_backup_window" {
  description = "Preferred backup window (UTC)"
  type        = string
  default     = "03:00-04:00"
}

variable "rds_maintenance_window" {
  description = "Preferred maintenance window (UTC)"
  type        = string
  default     = "sun:04:00-sun:05:00"
}

variable "rds_deletion_protection" {
  description = "Whether to enable deletion protection"
  type        = bool
  default     = true
}

variable "rds_skip_final_snapshot" {
  description = "Whether to skip the final snapshot on deletion"
  type        = bool
  default     = false
}

variable "rds_final_snapshot_identifier" {
  description = "Identifier for the final snapshot on deletion"
  type        = string
  default     = null
}

variable "rds_performance_insights_enabled" {
  description = "Whether to enable Performance Insights"
  type        = bool
  default     = true
}

# -----------------------------------------------------------------------------
# ElastiCache (Redis)
# -----------------------------------------------------------------------------

variable "elasticache_engine" {
  description = "Engine for ElastiCache"
  type        = string
  default     = "redis"
}

variable "elasticache_engine_version" {
  description = "Engine version for ElastiCache"
  type        = string
  default     = "7.1"
}

variable "elasticache_node_type" {
  description = "Node type for ElastiCache"
  type        = string
  default     = "cache.r6g.large"
}

variable "elasticache_port" {
  description = "Port for ElastiCache"
  type        = number
  default     = 6379
}

variable "elasticache_num_cache_nodes" {
  description = "Number of cache nodes in the cluster"
  type        = number
  default     = 2
}

variable "elasticache_automatic_failover_enabled" {
  description = "Whether to enable automatic failover"
  type        = bool
  default     = true
}

variable "elasticache_multi_az_enabled" {
  description = "Whether to enable Multi-AZ for ElastiCache"
  type        = bool
  default     = true
}

variable "elasticache_at_rest_encryption_enabled" {
  description = "Whether to enable at-rest encryption"
  type        = bool
  default     = true
}

variable "elasticache_transit_encryption_enabled" {
  description = "Whether to enable transit encryption"
  type        = bool
  default     = true
}

variable "elasticache_snapshot_retention_limit" {
  description = "Number of days to retain automatic snapshots"
  type        = number
  default     = 7
}

variable "elasticache_snapshot_window" {
  description = "Preferred snapshot window (UTC)"
  type        = string
  default     = "05:00-06:00"
}

variable "elasticache_maintenance_window" {
  description = "Preferred maintenance window (UTC)"
  type        = string
  default     = "sun:06:00-sun:07:00"
}

# -----------------------------------------------------------------------------
# S3 (Storage)
# -----------------------------------------------------------------------------

variable "s3_create_app_bucket" {
  description = "Whether to create the application data bucket"
  type        = bool
  default     = true
}

variable "s3_app_bucket_versioning" {
  description = "Whether to enable versioning on the app bucket"
  type        = bool
  default     = true
}

variable "s3_app_bucket_lifecycle_rules" {
  description = "Lifecycle rules for the app bucket"
  type = list(object({
    id      = string
    enabled = bool
    prefix  = string
    transitions = list(object({
      days          = number
      storage_class = string
    }))
    expiration = object({
      days = number
    })
  }))
  default = []
}

variable "s3_app_bucket_cors_rules" {
  description = "CORS rules for the app bucket"
  type = list(object({
    allowed_headers = list(string)
    allowed_methods = list(string)
    allowed_origins = list(string)
    expose_headers  = list(string)
    max_age_seconds = number
  }))
  default = []
}

variable "s3_create_media_bucket" {
  description = "Whether to create the media/assets bucket"
  type        = bool
  default     = true
}

variable "s3_media_bucket_versioning" {
  description = "Whether to enable versioning on the media bucket"
  type        = bool
  default     = true
}

variable "s3_media_bucket_cors_rules" {
  description = "CORS rules for the media bucket"
  type = list(object({
    allowed_headers = list(string)
    allowed_methods = list(string)
    allowed_origins = list(string)
    expose_headers  = list(string)
    max_age_seconds = number
  }))
  default = [{
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }]
}

variable "s3_create_logs_bucket" {
  description = "Whether to create the logs bucket"
  type        = bool
  default     = true
}

variable "s3_logs_bucket_lifecycle_rules" {
  description = "Lifecycle rules for the logs bucket"
  type = list(object({
    id      = string
    enabled = bool
    prefix  = string
    transitions = list(object({
      days          = number
      storage_class = string
    }))
    expiration = object({
      days = number
    })
  }))
  default = [{
    id      = "archive-old-logs"
    enabled = true
    prefix  = ""
    transitions = [
      {
        days          = 30
        storage_class = "STANDARD_IA"
      },
      {
        days          = 90
        storage_class = "GLACIER"
      }
    ]
    expiration = {
      days = 365
    }
  }]
}

variable "s3_block_public_acls" {
  description = "Whether to block public ACLs on S3 buckets"
  type        = bool
  default     = true
}

variable "s3_block_public_policy" {
  description = "Whether to block public policies on S3 buckets"
  type        = bool
  default     = true
}

variable "s3_ignore_public_acls" {
  description = "Whether to ignore public ACLs on S3 buckets"
  type        = bool
  default     = true
}

variable "s3_restrict_public_buckets" {
  description = "Whether to restrict public bucket access"
  type        = bool
  default     = true
}

# -----------------------------------------------------------------------------
# CloudFront (CDN)
# -----------------------------------------------------------------------------

variable "cloudfront_create_alb_origin" {
  description = "Whether to create an ALB origin for CloudFront"
  type        = bool
  default     = true
}

variable "cloudfront_default_cache_ttl" {
  description = "Default TTL for CloudFront cache behavior (seconds)"
  type        = number
  default     = 86400
}

variable "cloudfront_default_cache_max_ttl" {
  description = "Maximum TTL for CloudFront cache behavior (seconds)"
  type        = number
  default     = 31536000
}

variable "cloudfront_default_cache_compress" {
  description = "Whether to compress content at CloudFront"
  type        = bool
  default     = true
}

variable "cloudfront_ordered_cache_behaviors" {
  description = "Ordered cache behaviors for CloudFront"
  type = list(object({
    path_pattern           = string
    target_origin_id       = string
    viewer_protocol_policy = string
    allowed_methods        = list(string)
    cached_methods         = list(string)
    compress               = bool
    ttl                    = number
    max_ttl                = number
  }))
  default = []
}

variable "cloudfront_acm_certificate_arn" {
  description = "ARN of the ACM certificate for CloudFront"
  type        = string
  default     = ""
}

variable "cloudfront_aliases" {
  description = "List of domain aliases for CloudFront"
  type        = list(string)
  default     = []
}

variable "cloudfront_enable_logging" {
  description = "Whether to enable CloudFront access logging"
  type        = bool
  default     = true
}

variable "cloudfront_create_waf" {
  description = "Whether to create a WAF WebACL for CloudFront"
  type        = bool
  default     = true
}

variable "cloudfront_waf_web_acl_arn" {
  description = "ARN of an existing WAF WebACL (if not creating one)"
  type        = string
  default     = ""
}

# -----------------------------------------------------------------------------
# Route 53 (DNS)
# -----------------------------------------------------------------------------

variable "create_route53_records" {
  description = "Whether to create Route 53 DNS records"
  type        = bool
  default     = true
}

variable "create_route53_zone" {
  description = "Whether to create a new Route 53 hosted zone"
  type        = bool
  default     = false
}

variable "domain_name" {
  description = "Primary domain name for the application"
  type        = string
  default     = "ugc-marketplace.example.com"
}

# -----------------------------------------------------------------------------
# Monitoring (CloudWatch)
# -----------------------------------------------------------------------------

variable "monitoring_enable_rds_alarms" {
  description = "Whether to enable RDS CloudWatch alarms"
  type        = bool
  default     = true
}

variable "monitoring_enable_elasticache_alarms" {
  description = "Whether to enable ElastiCache CloudWatch alarms"
  type        = bool
  default     = true
}

variable "monitoring_enable_eks_alarms" {
  description = "Whether to enable EKS CloudWatch alarms"
  type        = bool
  default     = true
}

variable "monitoring_alarm_notification_arns" {
  description = "List of SNS topic ARNs for alarm notifications"
  type        = list(string)
  default     = []
}
