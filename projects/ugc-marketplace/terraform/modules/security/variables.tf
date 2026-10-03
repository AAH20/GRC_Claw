variable "name_prefix" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "vpc_cidr" {
  type = string
}

variable "eks_cluster_security_group_id" {
  type    = string
  default = ""
}

variable "rds_engine" {
  type    = string
  default = "postgres"
}

variable "rds_engine_version" {
  type    = string
  default = "16.2"
}

variable "rds_instance_class" {
  type    = string
  default = "db.r6g.large"
}

variable "rds_port" {
  type    = number
  default = 5432
}

variable "elasticache_engine" {
  type    = string
  default = "redis"
}

variable "elasticache_engine_version" {
  type    = string
  default = "7.1"
}

variable "elasticache_node_type" {
  type    = string
  default = "cache.r6g.large"
}

variable "elasticache_port" {
  type    = number
  default = 6379
}

variable "tags" {
  type    = map(string)
  default = {}
}
