# =============================================================================
# GRC Claw — Terraform Variables
# =============================================================================

# =============================================================================
# General
# =============================================================================

variable "environment" {
  description = "Deployment environment (dev, staging, production)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be one of: dev, staging, production."
  }
}

variable "kubernetes_version" {
  description = "Kubernetes version for managed clusters"
  type        = string
  default     = "1.28"
}

variable "database_password" {
  description = "Master password for PostgreSQL databases"
  type        = string
  sensitive   = true
}

# =============================================================================
# AWS Variables
# =============================================================================

variable "enable_aws" {
  description = "Enable AWS infrastructure provisioning"
  type        = bool
  default     = true
}

variable "aws_region" {
  description = "AWS region for resource deployment"
  type        = string
  default     = "us-east-1"
}

variable "aws_availability_zones" {
  description = "AWS availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "aws_vpc_cidr" {
  description = "CIDR block for AWS VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "aws_node_instance_types" {
  description = "EC2 instance types for EKS worker nodes"
  type        = list(string)
  default     = ["m6i.xlarge"]
}

variable "aws_node_desired_size" {
  description = "Desired number of EKS worker nodes"
  type        = number
  default     = 3
}

variable "aws_node_max_size" {
  description = "Maximum number of EKS worker nodes"
  type        = number
  default     = 10
}

variable "aws_node_min_size" {
  description = "Minimum number of EKS worker nodes"
  type        = number
  default     = 2
}

variable "aws_rds_instance_class" {
  description = "RDS instance class for PostgreSQL"
  type        = string
  default     = "db.r6g.xlarge"
}

variable "aws_redis_node_type" {
  description = "ElastiCache node type for Redis"
  type        = string
  default     = "cache.r6g.large"
}

variable "aws_kafka_instance_type" {
  description = "MSK broker instance type"
  type        = string
  default     = "kafka.m5.large"
}

# =============================================================================
# GCP Variables
# =============================================================================

variable "enable_gcp" {
  description = "Enable GCP infrastructure provisioning"
  type        = bool
  default     = false
}

variable "gcp_project_id" {
  description = "GCP project ID"
  type        = string
  default     = ""
}

variable "gcp_region" {
  description = "GCP region for resource deployment"
  type        = string
  default     = "us-central1"
}

variable "gcp_subnet_cidr" {
  description = "CIDR block for GCP subnet"
  type        = string
  default     = "10.1.0.0/20"
}

variable "gcp_node_count" {
  description = "Number of GKE nodes"
  type        = number
  default     = 3
}

variable "gcp_node_machine_type" {
  description = "Machine type for GKE nodes"
  type        = string
  default     = "n2-standard-4"
}

variable "gcp_sql_tier" {
  description = "Cloud SQL tier"
  type        = string
  default     = "db-custom-4-16384"
}

# =============================================================================
# Azure Variables
# =============================================================================

variable "enable_azure" {
  description = "Enable Azure infrastructure provisioning"
  type        = bool
  default     = false
}

variable "azure_subscription_id" {
  description = "Azure subscription ID"
  type        = string
  default     = ""
}

variable "azure_tenant_id" {
  description = "Azure tenant ID"
  type        = string
  default     = ""
}

variable "azure_region" {
  description = "Azure region for resource deployment"
  type        = string
  default     = "East US"
}

variable "azure_vnet_cidr" {
  description = "CIDR block for Azure VNet"
  type        = string
  default     = "10.2.0.0/16"
}

variable "azure_node_count" {
  description = "Number of AKS nodes"
  type        = number
  default     = 3
}

variable "azure_node_vm_size" {
  description = "VM size for AKS nodes"
  type        = string
  default     = "Standard_D4s_v3"
}

variable "azure_aad_admin_object_id" {
  description = "Azure AD admin object ID for Synapse"
  type        = string
  default     = ""
}
