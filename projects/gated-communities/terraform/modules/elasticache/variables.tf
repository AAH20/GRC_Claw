variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs"
  type        = list(string)
}

variable "cache_node_type" {
  description = "ElastiCache node type"
  type        = string
}

variable "cache_num_nodes" {
  description = "Number of cache nodes"
  type        = number
}

variable "common_tags" {
  description = "Common tags for all resources"
  type        = map(string)
}
