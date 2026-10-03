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
  default = "redis"
}

variable "engine_version" {
  type    = string
  default = "7.1"
}

variable "node_type" {
  type    = string
  default = "cache.r6g.large"
}

variable "port" {
  type    = number
  default = 6379
}

variable "num_cache_nodes" {
  type    = number
  default = 2
}

variable "automatic_failover_enabled" {
  type    = bool
  default = true
}

variable "multi_az_enabled" {
  type    = bool
  default = true
}

variable "at_rest_encryption_enabled" {
  type    = bool
  default = true
}

variable "transit_encryption_enabled" {
  type    = bool
  default = true
}

variable "kms_key_id" {
  type    = string
  default = ""
}

variable "snapshot_retention_limit" {
  type    = number
  default = 7
}

variable "snapshot_window" {
  type    = string
  default = "05:00-06:00"
}

variable "maintenance_window" {
  type    = string
  default = "sun:06:00-sun:07:00"
}

variable "security_group_ids" {
  type    = list(string)
  default = []
}

variable "tags" {
  type    = map(string)
  default = {}
}
