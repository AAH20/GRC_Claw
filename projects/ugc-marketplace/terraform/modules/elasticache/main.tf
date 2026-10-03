# =============================================================================
# ElastiCache Module — Redis
# =============================================================================

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "database_subnet_ids" {
  description = "List of database subnet IDs"
  type        = list(string)
}

variable "engine" {
  description = "Engine type"
  type        = string
  default     = "redis"
}

variable "engine_version" {
  description = "Engine version"
  type        = string
  default     = "7.1"
}

variable "node_type" {
  description = "Node type"
  type        = string
  default     = "cache.r6g.large"
}

variable "port" {
  description = "Port number"
  type        = number
  default     = 6379
}

variable "num_cache_nodes" {
  description = "Number of cache nodes"
  type        = number
  default     = 2
}

variable "automatic_failover_enabled" {
  description = "Whether to enable automatic failover"
  type        = bool
  default     = true
}

variable "multi_az_enabled" {
  description = "Whether to enable Multi-AZ"
  type        = bool
  default     = true
}

variable "at_rest_encryption_enabled" {
  description = "Whether to enable at-rest encryption"
  type        = bool
  default     = true
}

variable "transit_encryption_enabled" {
  description = "Whether to enable transit encryption"
  type        = bool
  default     = true
}

variable "kms_key_id" {
  description = "KMS key ID for encryption"
  type        = string
  default     = ""
}

variable "snapshot_retention_limit" {
  description = "Number of days to retain snapshots"
  type        = number
  default     = 7
}

variable "snapshot_window" {
  description = "Preferred snapshot window"
  type        = string
  default     = "05:00-06:00"
}

variable "maintenance_window" {
  description = "Preferred maintenance window"
  type        = string
  default     = "sun:06:00-sun:07:00"
}

variable "security_group_ids" {
  description = "List of security group IDs to associate"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# -----------------------------------------------------------------------------
# ElastiCache Subnet Group
# -----------------------------------------------------------------------------

resource "aws_elasticache_subnet_group" "this" {
  name       = "${var.name_prefix}-cache-subnet-group"
  subnet_ids = var.database_subnet_ids

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-cache-subnet-group"
  })
}

# -----------------------------------------------------------------------------
# ElastiCache Replication Group
# -----------------------------------------------------------------------------

resource "aws_elasticache_replication_group" "this" {
  replication_group_id = "${var.name_prefix}-redis"
  description          = "Redis cluster for UGC Marketplace"

  engine         = var.engine
  engine_version = var.engine_version
  node_type      = var.node_type
  port           = var.port

  num_cache_nodes            = var.num_cache_nodes
  automatic_failover_enabled = var.automatic_failover_enabled
  multi_az_enabled           = var.multi_az_enabled

  at_rest_encryption_enabled = var.at_rest_encryption_enabled
  transit_encryption_enabled = var.transit_encryption_enabled
  kms_key_id                 = var.kms_key_id != "" ? var.kms_key_id : null

  subnet_group_name  = aws_elasticache_subnet_group.this.name
  security_group_ids = var.security_group_ids

  snapshot_retention_limit = var.snapshot_retention_limit
  snapshot_window          = var.snapshot_window
  maintenance_window       = var.maintenance_window

  auto_minor_version_upgrade = true

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-elasticache"
  })
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------

output "cluster_id" {
  description = "ID of the ElastiCache cluster"
  value       = aws_elasticache_replication_group.this.id
}

output "cluster_arn" {
  description = "ARN of the ElastiCache cluster"
  value       = aws_elasticache_replication_group.this.arn
}

output "primary_endpoint" {
  description = "Primary endpoint for the ElastiCache cluster"
  value       = aws_elasticache_replication_group.this.primary_endpoint_address
}

output "reader_endpoint" {
  description = "Reader endpoint for the ElastiCache cluster"
  value       = aws_elasticache_replication_group.this.reader_endpoint_address
}

output "port" {
  description = "Port for the ElastiCache cluster"
  value       = aws_elasticache_replication_group.this.port
}

output "security_group_id" {
  description = "Security group ID for the ElastiCache cluster"
  value       = var.security_group_ids[0]
}
