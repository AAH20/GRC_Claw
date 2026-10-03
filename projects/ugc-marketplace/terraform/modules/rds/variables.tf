variable "name_prefix" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "database_subnet_ids" {
  type = list(string)
}

variable "engine" {
  type    = string
  default = "postgres"
}

variable "engine_version" {
  type    = string
  default = "16.2"
}

variable "instance_class" {
  type    = string
  default = "db.r6g.large"
}

variable "port" {
  type    = number
  default = 5432
}

variable "database_name" {
  type    = string
  default = "ugc_marketplace"
}

variable "master_username" {
  type    = string
  default = "ugc_admin"
}

variable "master_password" {
  type      = string
  sensitive = true
  default   = ""
}

variable "allocated_storage" {
  type    = number
  default = 100
}

variable "max_allocated_storage" {
  type    = number
  default = 500
}

variable "storage_type" {
  type    = string
  default = "gp3"
}

variable "storage_encrypted" {
  type    = bool
  default = true
}

variable "kms_key_id" {
  type    = string
  default = ""
}

variable "multi_az" {
  type    = bool
  default = true
}

variable "backup_retention_period" {
  type    = number
  default = 30
}

variable "backup_window" {
  type    = string
  default = "03:00-04:00"
}

variable "maintenance_window" {
  type    = string
  default = "sun:04:00-sun:05:00"
}

variable "deletion_protection" {
  type    = bool
  default = true
}

variable "skip_final_snapshot" {
  type    = bool
  default = false
}

variable "final_snapshot_identifier" {
  type    = string
  default = null
}

variable "performance_insights_enabled" {
  type    = bool
  default = true
}

variable "performance_insights_kms_key_id" {
  type    = string
  default = ""
}

variable "security_group_ids" {
  type    = list(string)
  default = []
}

variable "tags" {
  type    = map(string)
  default = {}
}
