variable "name_prefix" {
  type = string
}

variable "vpc_cidr" {
  type = string
}

variable "availability_zones" {
  type = list(string)
}

variable "public_subnet_cidrs" {
  type = list(string)
}

variable "private_subnet_cidrs" {
  type = list(string)
}

variable "database_subnet_cidrs" {
  type = list(string)
}

variable "enable_nat_gateway" {
  type    = bool
  default = true
}

variable "single_nat_gateway" {
  type    = bool
  default = false
}

variable "enable_flow_logs" {
  type    = bool
  default = true
}

variable "flow_logs_retention_days" {
  type    = number
  default = 30
}

variable "tags" {
  type    = map(string)
  default = {}
}
