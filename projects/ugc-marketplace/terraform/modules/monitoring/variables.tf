variable "name_prefix" {
  type = string
}

variable "eks_cluster_name" {
  type    = string
  default = ""
}

variable "rds_instance_id" {
  type    = string
  default = ""
}

variable "elasticache_cluster_id" {
  type    = string
  default = ""
}

variable "enable_rds_alarms" {
  type    = bool
  default = true
}

variable "enable_elasticache_alarms" {
  type    = bool
  default = true
}

variable "enable_eks_alarms" {
  type    = bool
  default = true
}

variable "alarm_notification_arns" {
  type    = list(string)
  default = []
}

variable "tags" {
  type    = map(string)
  default = {}
}
