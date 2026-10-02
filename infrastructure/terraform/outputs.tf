# =============================================================================
# GRC Claw — Terraform Outputs
# =============================================================================

# =============================================================================
# AWS Outputs
# =============================================================================

output "aws_eks_cluster_name" {
  description = "Name of the EKS cluster"
  value       = var.enable_aws ? aws_eks_cluster.main[0].name : null
}

output "aws_eks_cluster_endpoint" {
  description = "Endpoint for the EKS cluster"
  value       = var.enable_aws ? aws_eks_cluster.main[0].endpoint : null
}

output "aws_eks_cluster_certificate_authority" {
  description = "Certificate authority data for the EKS cluster"
  value       = var.enable_aws ? aws_eks_cluster.main[0].certificate_authority[0].data : null
  sensitive   = true
}

output "aws_rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = var.enable_aws ? aws_db_instance.postgres[0].endpoint : null
}

output "aws_rds_arn" {
  description = "RDS PostgreSQL ARN"
  value       = var.enable_aws ? aws_db_instance.postgres[0].arn : null
}

output "aws_redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = var.enable_aws ? aws_elasticache_replication_group.redis[0].primary_endpoint_address : null
}

output "aws_msk_bootstrap_brokers" {
  description = "MSK Kafka bootstrap brokers"
  value       = var.enable_aws ? aws_msk_cluster.kafka[0].bootstrap_brokers_tls : null
}

output "aws_s3_data_lake_bucket" {
  description = "S3 data lake bucket name"
  value       = var.enable_aws ? aws_s3_bucket.data_lake[0].bucket : null
}

output "aws_vpc_id" {
  description = "AWS VPC ID"
  value       = var.enable_aws ? aws_vpc.main[0].id : null
}

output "aws_private_subnet_ids" {
  description = "AWS private subnet IDs"
  value       = var.enable_aws ? aws_subnet.private[*].id : null
}

# =============================================================================
# GCP Outputs
# =============================================================================

output "gcp_gke_cluster_name" {
  description = "Name of the GKE cluster"
  value       = var.enable_gcp ? google_container_cluster.main[0].name : null
}

output "gcp_gke_cluster_endpoint" {
  description = "Endpoint for the GKE cluster"
  value       = var.enable_gcp ? google_container_cluster.main[0].endpoint : null
  sensitive   = true
}

output "gcp_sql_connection_name" {
  description = "Cloud SQL connection name"
  value       = var.enable_gcp ? google_sql_database_instance.postgres[0].connection_name : null
}

output "gcp_redis_host" {
  description = "Memorystore Redis host"
  value       = var.enable_gcp ? google_redis_instance.main[0].host : null
}

output "gcp_pubsub_topic" {
  description = "Pub/Sub events topic"
  value       = var.enable_gcp ? google_pubsub_topic.events[0].name : null
}

output "gcp_bigquery_dataset" {
  description = "BigQuery dataset ID"
  value       = var.enable_gcp ? google_bigquery_dataset.warehouse[0].dataset_id : null
}

# =============================================================================
# Azure Outputs
# =============================================================================

output "azure_aks_cluster_name" {
  description = "Name of the AKS cluster"
  value       = var.enable_azure ? azurerm_kubernetes_cluster.main[0].name : null
}

output "azure_aks_cluster_fqdn" {
  description = "FQDN of the AKS cluster"
  value       = var.enable_azure ? azurerm_kubernetes_cluster.main[0].fqdn : null
}

output "azure_postgres_fqdn" {
  description = "Azure PostgreSQL FQDN"
  value       = var.enable_azure ? azurerm_postgresql_flexible_server.main[0].fqdn : null
}

output "azure_redis_hostname" {
  description = "Azure Redis hostname"
  value       = var.enable_azure ? azurerm_redis_cache.main[0].hostname : null
}

output "azure_eventhub_namespace" {
  description = "Event Hubs namespace"
  value       = var.enable_azure ? azurerm_eventhub_namespace.main[0].name : null
}

output "azure_synapse_workspace" {
  description = "Synapse workspace name"
  value       = var.enable_azure ? azurerm_synapse_workspace.main[0].name : null
}

output "azure_resource_group" {
  description = "Azure resource group name"
  value       = var.enable_azure ? azurerm_resource_group.main[0].name : null
}

# =============================================================================
# Multi-Cloud Summary
# =============================================================================

output "active_clouds" {
  description = "List of active cloud providers"
  value = compact([
    var.enable_aws ? "aws" : "",
    var.enable_gcp ? "gcp" : "",
    var.enable_azure ? "azure" : "",
  ])
}

output "kubernetes_clusters" {
  description = "Map of Kubernetes cluster endpoints by cloud"
  value = {
    aws   = var.enable_aws ? aws_eks_cluster.main[0].endpoint : null
    gcp   = var.enable_gcp ? google_container_cluster.main[0].endpoint : null
    azure = var.enable_azure ? azurerm_kubernetes_cluster.main[0].fqdn : null
  }
  sensitive = true
}
