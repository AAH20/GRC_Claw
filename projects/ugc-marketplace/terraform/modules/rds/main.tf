# =============================================================================
# RDS Module — PostgreSQL
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
  description = "Database engine"
  type        = string
  default     = "postgres"
}

variable "engine_version" {
  description = "Database engine version"
  type        = string
  default     = "16.2"
}

variable "instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.r6g.large"
}

variable "port" {
  description = "Database port"
  type        = number
  default     = 5432
}

variable "database_name" {
  description = "Name of the default database"
  type        = string
  default     = "ugc_marketplace"
}

variable "master_username" {
  description = "Master username"
  type        = string
  default     = "ugc_admin"
}

variable "master_password" {
  description = "Master password"
  type        = string
  sensitive   = true
  default     = ""
}

variable "allocated_storage" {
  description = "Initial allocated storage in GB"
  type        = number
  default     = 100
}

variable "max_allocated_storage" {
  description = "Maximum allocated storage for autoscaling in GB"
  type        = number
  default     = 500
}

variable "storage_type" {
  description = "Storage type"
  type        = string
  default     = "gp3"
}

variable "storage_encrypted" {
  description = "Whether to encrypt storage"
  type        = bool
  default     = true
}

variable "kms_key_id" {
  description = "KMS key ID for encryption"
  type        = string
  default     = ""
}

variable "multi_az" {
  description = "Whether to create a Multi-AZ deployment"
  type        = bool
  default     = true
}

variable "backup_retention_period" {
  description = "Number of days to retain backups"
  type        = number
  default     = 30
}

variable "backup_window" {
  description = "Preferred backup window"
  type        = string
  default     = "03:00-04:00"
}

variable "maintenance_window" {
  description = "Preferred maintenance window"
  type        = string
  default     = "sun:04:00-sun:05:00"
}

variable "deletion_protection" {
  description = "Whether to enable deletion protection"
  type        = bool
  default     = true
}

variable "skip_final_snapshot" {
  description = "Whether to skip the final snapshot on deletion"
  type        = bool
  default     = false
}

variable "final_snapshot_identifier" {
  description = "Identifier for the final snapshot"
  type        = string
  default     = null
}

variable "performance_insights_enabled" {
  description = "Whether to enable Performance Insights"
  type        = bool
  default     = true
}

variable "performance_insights_kms_key_id" {
  description = "KMS key ID for Performance Insights"
  type        = string
  default     = ""
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
# DB Subnet Group
# -----------------------------------------------------------------------------

resource "aws_db_subnet_group" "this" {
  name       = "${var.name_prefix}-db-subnet-group"
  subnet_ids = var.database_subnet_ids

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-db-subnet-group"
  })
}

# -----------------------------------------------------------------------------
# RDS Instance
# -----------------------------------------------------------------------------

resource "aws_db_instance" "this" {
  identifier = "${var.name_prefix}-db"

  engine         = var.engine
  engine_version = var.engine_version
  instance_class = var.instance_class

  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type          = var.storage_type
  storage_encrypted     = var.storage_encrypted
  kms_key_id            = var.kms_key_id != "" ? var.kms_key_id : null

  db_name  = var.database_name
  username = var.master_username
  password = var.master_password
  port     = var.port

  multi_az               = var.multi_az
  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = var.security_group_ids

  backup_retention_period = var.backup_retention_period
  backup_window           = var.backup_window
  maintenance_window      = var.maintenance_window

  deletion_protection = var.deletion_protection
  skip_final_snapshot = var.skip_final_snapshot
  final_snapshot_identifier = var.final_snapshot_identifier

  performance_insights_enabled          = var.performance_insights_enabled
  performance_insights_kms_key_id       = var.performance_insights_kms_key_id != "" ? var.performance_insights_kms_key_id : null

  auto_minor_version_upgrade = true
  copy_tags_to_snapshot      = true

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-rds"
  })
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------

output "instance_id" {
  description = "ID of the RDS instance"
  value       = aws_db_instance.this.id
}

output "instance_arn" {
  description = "ARN of the RDS instance"
  value       = aws_db_instance.this.arn
}

output "instance_endpoint" {
  description = "Connection endpoint for the RDS instance"
  value       = aws_db_instance.this.endpoint
}

output "instance_address" {
  description = "Hostname of the RDS instance"
  value       = aws_db_instance.this.address
}

output "instance_port" {
  description = "Port of the RDS instance"
  value       = aws_db_instance.this.port
}

output "database_name" {
  description = "Name of the default database"
  value       = aws_db_instance.this.db_name
}

output "master_username" {
  description = "Master username"
  value       = aws_db_instance.this.username
}

output "security_group_id" {
  description = "Security group ID for the RDS instance"
  value       = var.security_group_ids[0]
}
