# =============================================================================
# GRC Claw — Multi-Cloud Infrastructure (AWS / GCP / Azure)
# =============================================================================
# This module provisions the foundational infrastructure for the GRC Claw
# shared platform across AWS, GCP, and Azure.
# =============================================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
  }

  backend "s3" {
    bucket         = "grc-claw-terraform-state"
    key            = "infrastructure/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "grc-claw-terraform-locks"
  }
}

# =============================================================================
# AWS Provider
# =============================================================================
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "grc-claw"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# =============================================================================
# GCP Provider
# =============================================================================
provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# =============================================================================
# Azure Provider
# =============================================================================
provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
  subscription_id = var.azure_subscription_id
  tenant_id       = var.azure_tenant_id
}

# =============================================================================
# AWS Infrastructure
# =============================================================================

# VPC
resource "aws_vpc" "main" {
  count                = var.enable_aws ? 1 : 0
  cidr_block           = var.aws_vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "grc-claw-${var.environment}"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  count  = var.enable_aws ? 1 : 0
  vpc_id = aws_vpc.main[0].id

  tags = {
    Name = "grc-claw-${var.environment}"
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count                   = var.enable_aws ? length(var.aws_availability_zones) : 0
  vpc_id                  = aws_vpc.main[0].id
  cidr_block              = cidrsubnet(var.aws_vpc_cidr, 8, count.index)
  availability_zone       = var.aws_availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "grc-claw-public-${var.aws_availability_zones[count.index]}"
    Type = "public"
  }
}

# Private Subnets
resource "aws_subnet" "private" {
  count             = var.enable_aws ? length(var.aws_availability_zones) : 0
  vpc_id            = aws_vpc.main[0].id
  cidr_block        = cidrsubnet(var.aws_vpc_cidr, 8, count.index + 10)
  availability_zone = var.aws_availability_zones[count.index]

  tags = {
    Name = "grc-claw-private-${var.aws_availability_zones[count.index]}"
    Type = "private"
  }
}

# EKS Cluster
resource "aws_eks_cluster" "main" {
  count    = var.enable_aws ? 1 : 0
  name     = "grc-claw-${var.environment}"
  role_arn = aws_iam_role.eks_cluster[0].arn
  version  = var.kubernetes_version

  vpc_config {
    subnet_ids              = aws_subnet.private[*].id
    endpoint_private_access = true
    endpoint_public_access  = true
    security_group_ids      = [aws_security_group.eks_cluster[0].id]
  }

  encryption_config {
    provider {
      key_arn = aws_kms_key.eks[0].arn
    }
    resources = ["secrets"]
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy,
    aws_iam_role_policy_attachment.eks_service_policy,
  ]

  tags = {
    Name = "grc-claw-${var.environment}"
  }
}

# EKS Managed Node Group
resource "aws_eks_node_group" "main" {
  count           = var.enable_aws ? 1 : 0
  cluster_name    = aws_eks_cluster.main[0].name
  node_group_name = "grc-claw-workers"
  node_role_arn   = aws_iam_role.eks_node[0].arn
  subnet_ids      = aws_subnet.private[*].id
  instance_types  = var.aws_node_instance_types
  capacity_type   = "ON_DEMAND"
  disk_size       = 100

  scaling_config {
    desired_size = var.aws_node_desired_size
    max_size     = var.aws_node_max_size
    min_size     = var.aws_node_min_size
  }

  update_config {
    max_unavailable = 1
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.eks_ecr_policy,
  ]

  tags = {
    Name = "grc-claw-${var.environment}"
  }
}

# RDS PostgreSQL
resource "aws_db_instance" "postgres" {
  count                  = var.enable_aws ? 1 : 0
  identifier             = "grc-claw-${var.environment}"
  engine                 = "postgres"
  engine_version         = "16.1"
  instance_class         = var.aws_rds_instance_class
  allocated_storage      = 100
  max_allocated_storage  = 500
  storage_type           = "gp3"
  storage_encrypted      = true
  kms_key_id             = aws_kms_key.rds[0].arn
  db_name                = "grc_claw"
  username               = "grc_admin"
  password               = var.database_password
  multi_az               = true
  publicly_accessible    = false
  db_subnet_group_name   = aws_db_subnet_group.main[0].name
  vpc_security_group_ids = [aws_security_group.rds[0].id]
  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "Mon:04:00-Mon:05:00"
  deletion_protection    = true
  skip_final_snapshot    = false
  final_snapshot_identifier = "grc-claw-final"

  tags = {
    Name = "grc-claw-${var.environment}"
  }
}

# ElastiCache Redis
resource "aws_elasticache_replication_group" "redis" {
  count                      = var.enable_aws ? 1 : 0
  replication_group_id       = "grc-claw-${var.environment}"
  description                = "GRC Claw Redis cluster"
  node_type                  = var.aws_redis_node_type
  number_cache_clusters      = 2
  automatic_failover_enabled = true
  multi_az_enabled           = true
  engine                     = "redis"
  engine_version             = "7.1"
  port                       = 6379
  parameter_group_name       = "default.redis7"
  subnet_group_name          = aws_elasticache_subnet_group.main[0].name
  security_group_ids         = [aws_security_group.redis[0].id]
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  snapshot_retention_limit   = 7
  snapshot_window            = "05:00-06:00"

  tags = {
    Name = "grc-claw-${var.environment}"
  }
}

# MSK (Managed Kafka)
resource "aws_msk_cluster" "kafka" {
  count                  = var.enable_aws ? 1 : 0
  cluster_name           = "grc-claw-${var.environment}"
  kafka_version          = "3.5.1"
  number_of_broker_nodes = 3
  broker_node_group_info {
    instance_type   = var.aws_kafka_instance_type
    client_subnets  = aws_subnet.private[*].id
    security_groups = [aws_security_group.kafka[0].id]
    storage_info {
      ebs_storage_info {
        volume_size = 100
      }
    }
  }
  encryption_info {
    encryption_at_rest_kms_key_arn = aws_kms_key.msk[0].arn
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster    = true
    }
  }
  client_authentication {
    sasl {
      iam = true
    }
  }
  logging_info {
    broker_logs {
      cloudwatch_logs {
        enabled   = true
        log_group = aws_cloudwatch_log_group.kafka[0].name
      }
    }
  }

  tags = {
    Name = "grc-claw-${var.environment}"
  }
}

# S3 Bucket for Data Lake
resource "aws_s3_bucket" "data_lake" {
  count  = var.enable_aws ? 1 : 0
  bucket = "grc-claw-data-lake-${var.environment}-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "grc-claw-${var.environment}"
  }
}

resource "aws_s3_bucket_versioning" "data_lake" {
  count  = var.enable_aws ? 1 : 0
  bucket = aws_s3_bucket.data_lake[0].id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  count  = var.enable_aws ? 1 : 0
  bucket = aws_s3_bucket.data_lake[0].id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3[0].arn
    }
    bucket_key_enabled = true
  }
}

# =============================================================================
# GCP Infrastructure
# =============================================================================

# VPC Network
resource "google_compute_network" "main" {
  count                   = var.enable_gcp ? 1 : 0
  name                    = "grc-claw-${var.environment}"
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
}

# Subnets
resource "google_compute_subnetwork" "main" {
  count         = var.enable_gcp ? 1 : 0
  name          = "grc-claw-${var.environment}"
  ip_cidr_range = var.gcp_subnet_cidr
  region        = var.gcp_region
  network       = google_compute_network.main[0].id

  private_ip_google_access = true

  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

# GKE Cluster
resource "google_container_cluster" "main" {
  count    = var.enable_gcp ? 1 : 0
  name     = "grc-claw-${var.environment}"
  location = var.gcp_region
  network  = google_compute_network.main[0].id
  subnetwork = google_compute_subnetwork.main[0].id

  remove_default_node_pool = true
  initial_node_count       = 1

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = "0.0.0.0/0"
      display_name = "all"
    }
  }

  release_channel {
    channel = "REGULAR"
  }

  workload_identity_config {
    workload_pool = "${var.gcp_project_id}.svc.id.goog"
  }

  depends_on = [google_project_service.container]
}

# GKE Node Pool
resource "google_container_node_pool" "main" {
  count      = var.enable_gcp ? 1 : 0
  name       = "grc-claw-workers"
  location   = var.gcp_region
  cluster    = google_container_cluster.main[0].name
  node_count = var.gcp_node_count

  node_config {
    machine_type = var.gcp_node_machine_type
    disk_size_gb = 100
    disk_type    = "pd-ssd"
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
    ]
    workload_metadata_config {
      mode = "GKE_METADATA"
    }
    tags = ["grc-claw", var.environment]
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  upgrade_settings {
    max_surge       = 1
    max_unavailable = 0
  }
}

# Cloud SQL PostgreSQL
resource "google_sql_database_instance" "postgres" {
  count            = var.enable_gcp ? 1 : 0
  name             = "grc-claw-${var.environment}"
  database_version = "POSTGRES_16"
  region           = var.gcp_region

  settings {
    tier              = var.gcp_sql_tier
    availability_type = "REGIONAL"
    disk_size         = 100
    disk_type         = "PD_SSD"
    disk_autoresize   = true

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
    }

    maintenance_window {
      day          = 1
      hour         = 4
      update_track = "stable"
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.main[0].id
    }

    database_flags {
      name  = "log_min_duration_statement"
      value = "1000"
    }
  }

  deletion_protection = true

  depends_on = [google_service_networking_connection.private_vpc_connection]
}

# Memorystore Redis
resource "google_redis_instance" "main" {
  count              = var.enable_gcp ? 1 : 0
  name               = "grc-claw-${var.environment}"
  tier               = "STANDARD_HA"
  memory_size_gb     = 5
  region             = var.gcp_region
  authorized_network = google_compute_network.main[0].id
  connect_mode       = "PRIVATE_SERVICE_ACCESS"

  redis_configs = {
    maxmemory-policy = "allkeys-lru"
  }

  depends_on = [google_service_networking_connection.private_vpc_connection]
}

# Pub/Sub (Kafka alternative on GCP)
resource "google_pubsub_topic" "events" {
  count = var.enable_gcp ? 1 : 0
  name  = "grc-claw-events-${var.environment}"

  message_retention_duration = "86400s"

  labels = {
    environment = var.environment
  }
}

resource "google_pubsub_subscription" "events" {
  count  = var.enable_gcp ? 1 : 0
  name   = "grc-claw-events-sub-${var.environment}"
  topic  = google_pubsub_topic.events[0].name

  ack_deadline_seconds       = 60
  message_retention_duration = "604800s"
  retain_acked_messages      = false

  expiration_policy {
    ttl = ""
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
}

# BigQuery Dataset (Snowflake alternative on GCP)
resource "google_bigquery_dataset" "warehouse" {
  count         = var.enable_gcp ? 1 : 0
  dataset_id    = "grc_claw_dw_${var.environment}"
  friendly_name = "GRC Claw Data Warehouse"
  description   = "Data warehouse for GRC Claw analytics"
  location      = "US"

  default_table_expiration_ms = null

  labels = {
    environment = var.environment
  }
}

# =============================================================================
# Azure Infrastructure
# =============================================================================

# Resource Group
resource "azurerm_resource_group" "main" {
  count    = var.enable_azure ? 1 : 0
  name     = "grc-claw-${var.environment}"
  location = var.azure_region

  tags = {
    environment = var.environment
  }
}

# Virtual Network
resource "azurerm_virtual_network" "main" {
  count               = var.enable_azure ? 1 : 0
  name                = "grc-claw-${var.environment}"
  location            = azurerm_resource_group.main[0].location
  resource_group_name = azurerm_resource_group.main[0].name
  address_space       = [var.azure_vnet_cidr]

  tags = {
    environment = var.environment
  }
}

# Subnets
resource "azurerm_subnet" "aks" {
  count                = var.enable_azure ? 1 : 0
  name                 = "aks-subnet"
  resource_group_name  = azurerm_resource_group.main[0].name
  virtual_network_name = azurerm_virtual_network.main[0].name
  address_prefixes     = [cidrsubnet(var.azure_vnet_cidr, 4, 0)]
}

resource "azurerm_subnet" "data" {
  count                = var.enable_azure ? 1 : 0
  name                 = "data-subnet"
  resource_group_name  = azurerm_resource_group.main[0].name
  virtual_network_name = azurerm_virtual_network.main[0].name
  address_prefixes     = [cidrsubnet(var.azure_vnet_cidr, 4, 1)]
}

# AKS Cluster
resource "azurerm_kubernetes_cluster" "main" {
  count               = var.enable_azure ? 1 : 0
  name                = "grc-claw-${var.environment}"
  location            = azurerm_resource_group.main[0].location
  resource_group_name = azurerm_resource_group.main[0].name
  dns_prefix          = "grc-claw-${var.environment}"
  kubernetes_version  = var.kubernetes_version

  default_node_pool {
    name                = "default"
    node_count          = var.azure_node_count
    vm_size             = var.azure_node_vm_size
    vnet_subnet_id      = azurerm_subnet.aks[0].id
    enable_auto_scaling = true
    min_count           = 1
    max_count           = 5
    os_disk_size_gb     = 100
    type                = "VirtualMachineScaleSets"
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin    = "azure"
    network_policy    = "calico"
    load_balancer_sku = "standard"
  }

  oms_agent {
    log_analytics_workspace_id = azurerm_log_analytics_workspace.main[0].id
  }

  tags = {
    environment = var.environment
  }
}

# Azure Database for PostgreSQL
resource "azurerm_postgresql_flexible_server" "main" {
  count               = var.enable_azure ? 1 : 0
  name                = "grc-claw-${var.environment}"
  resource_group_name = azurerm_resource_group.main[0].name
  location            = azurerm_resource_group.main[0].location
  version             = "16"
  sku_name            = "GP_Standard_D4s_v3"
  storage_mb          = 131072
  backup_retention_days = 30
  geo_redundant_backup_enabled = true
  auto_grow_enabled   = true

  administrator_login    = "grc_admin"
  administrator_password = var.database_password

  delegated_subnet_id = azurerm_subnet.data[0].id
  private_dns_zone_id = azurerm_private_dns_zone.postgres[0].id

  depends_on = [azurerm_private_dns_zone_virtual_network_link.postgres]
}

# Azure Cache for Redis
resource "azurerm_redis_cache" "main" {
  count               = var.enable_azure ? 1 : 0
  name                = "grc-claw-${var.environment}"
  location            = azurerm_resource_group.main[0].location
  resource_group_name = azurerm_resource_group.main[0].name
  capacity            = 1
  family              = "C"
  sku_name            = "Standard"
  enable_non_ssl_port = false
  minimum_tls_version = "1.2"

  redis_configuration {
    maxmemory_policy = "allkeys-lru"
  }

  patch_schedule {
    day_of_week    = "Sunday"
    start_hour_utc = 2
  }
}

# Event Hubs (Kafka alternative on Azure)
resource "azurerm_eventhub_namespace" "main" {
  count               = var.enable_azure ? 1 : 0
  name                = "grc-claw-${var.environment}"
  location            = azurerm_resource_group.main[0].location
  resource_group_name = azurerm_resource_group.main[0].name
  sku                 = "Standard"
  capacity            = 2

  auto_inflate_enabled     = true
  maximum_throughput_units = 20

  tags = {
    environment = var.environment
  }
}

resource "azurerm_eventhub" "events" {
  count               = var.enable_azure ? 1 : 0
  name                = "grc-claw-events"
  namespace_name      = azurerm_eventhub_namespace.main[0].name
  resource_group_name = azurerm_resource_group.main[0].name
  partition_count     = 6
  message_retention   = 7
}

# Azure Synapse Analytics (Snowflake alternative on Azure)
resource "azurerm_synapse_workspace" "main" {
  count                                = var.enable_azure ? 1 : 0
  name                                 = "grcclaw${var.environment}"
  resource_group_name                  = azurerm_resource_group.main[0].name
  location                             = azurerm_resource_group.main[0].location
  storage_data_lake_gen2_filesystem_id = azurerm_storage_data_lake_gen2_filesystem.main[0].id
  sql_administrator_login              = "grc_admin"
  sql_administrator_login_password     = var.database_password

  aad_admin {
    login     = "AzureAD Admin"
    object_id = var.azure_aad_admin_object_id
    tenant_id = var.azure_tenant_id
  }

  identity {
    type = "SystemAssigned"
  }

  tags = {
    environment = var.environment
  }
}

# =============================================================================
# Data Sources
# =============================================================================
data "aws_caller_identity" "current" {}

# =============================================================================
# Kubernetes & Helm Providers (post-cluster creation)
# =============================================================================
provider "kubernetes" {
  host                   = var.enable_aws ? aws_eks_cluster.main[0].endpoint : ""
  cluster_ca_certificate = var.enable_aws ? base64decode(aws_eks_cluster.main[0].certificate_authority[0].data) : ""
  token                  = var.enable_aws ? data.aws_eks_cluster_auth.main[0].token : ""
}

data "aws_eks_cluster_auth" "main" {
  count = var.enable_aws ? 1 : 0
  name  = aws_eks_cluster.main[0].name
}

provider "helm" {
  kubernetes {
    host                   = var.enable_aws ? aws_eks_cluster.main[0].endpoint : ""
    cluster_ca_certificate = var.enable_aws ? base64decode(aws_eks_cluster.main[0].certificate_authority[0].data) : ""
    token                  = var.enable_aws ? data.aws_eks_cluster_auth.main[0].token : ""
  }
}

# =============================================================================
# Kubernetes Deployments via Helm
# =============================================================================

# Strimzi Kafka Operator
resource "helm_release" "strimzi" {
  count      = var.enable_aws ? 1 : 0
  name       = "strimzi-kafka-operator"
  repository = "https://strimzi.io/charts/"
  chart      = "strimzi-kafka-operator"
  namespace  = "grc-claw"
  create_namespace = true

  set {
    name  = "watchNamespaces"
    value = "{grc-claw}"
  }
}

# Prometheus Stack
resource "helm_release" "prometheus" {
  count      = var.enable_aws ? 1 : 0
  name       = "kube-prometheus-stack"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  namespace  = "grc-claw"
  create_namespace = true

  values = [
    file("${path.module}/../monitoring/prometheus/prometheus.yml")
  ]
}

# Istio
resource "helm_release" "istio_base" {
  count      = var.enable_aws ? 1 : 0
  name       = "istio-base"
  repository = "https://istio-release.storage.googleapis.com/charts"
  chart      = "base"
  namespace  = "istio-system"
  create_namespace = true
}

resource "helm_release" "istiod" {
  count      = var.enable_aws ? 1 : 0
  name       = "istiod"
  repository = "https://istio-release.storage.googleapis.com/charts"
  chart      = "istiod"
  namespace  = "istio-system"

  depends_on = [helm_release.istio_base]
}

# Cert Manager
resource "helm_release" "cert_manager" {
  count      = var.enable_aws ? 1 : 0
  name       = "cert-manager"
  repository = "https://charts.jetstack.io"
  chart      = "cert-manager"
  namespace  = "cert-manager"
  create_namespace = true

  set {
    name  = "installCRDs"
    value = "true"
  }
}

# =============================================================================
# AWS IAM Resources
# =============================================================================

resource "aws_iam_role" "eks_cluster" {
  count = var.enable_aws ? 1 : 0
  name  = "grc-claw-eks-cluster-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "eks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  count      = var.enable_aws ? 1 : 0
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster[0].name
}

resource "aws_iam_role_policy_attachment" "eks_service_policy" {
  count      = var.enable_aws ? 1 : 0
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSServicePolicy"
  role       = aws_iam_role.eks_cluster[0].name
}

resource "aws_iam_role" "eks_node" {
  count = var.enable_aws ? 1 : 0
  name  = "grc-claw-eks-node-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_node_policy" {
  count      = var.enable_aws ? 1 : 0
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_node[0].name
}

resource "aws_iam_role_policy_attachment" "eks_cni_policy" {
  count      = var.enable_aws ? 1 : 0
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.eks_node[0].name
}

resource "aws_iam_role_policy_attachment" "eks_ecr_policy" {
  count      = var.enable_aws ? 1 : 0
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.eks_node[0].name
}

# =============================================================================
# AWS KMS Keys
# =============================================================================

resource "aws_kms_key" "eks" {
  count                   = var.enable_aws ? 1 : 0
  description             = "EKS Secret Encryption Key"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name = "grc-claw-eks-${var.environment}"
  }
}

resource "aws_kms_key" "rds" {
  count                   = var.enable_aws ? 1 : 0
  description             = "RDS Encryption Key"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name = "grc-claw-rds-${var.environment}"
  }
}

resource "aws_kms_key" "msk" {
  count                   = var.enable_aws ? 1 : 0
  description             = "MSK Encryption Key"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name = "grc-claw-msk-${var.environment}"
  }
}

resource "aws_kms_key" "s3" {
  count                   = var.enable_aws ? 1 : 0
  description             = "S3 Encryption Key"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name = "grc-claw-s3-${var.environment}"
  }
}

# =============================================================================
# AWS Security Groups
# =============================================================================

resource "aws_security_group" "eks_cluster" {
  count       = var.enable_aws ? 1 : 0
  name        = "grc-claw-eks-cluster-${var.environment}"
  description = "EKS cluster security group"
  vpc_id      = aws_vpc.main[0].id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "grc-claw-eks-cluster-${var.environment}"
  }
}

resource "aws_security_group" "rds" {
  count       = var.enable_aws ? 1 : 0
  name        = "grc-claw-rds-${var.environment}"
  description = "RDS security group"
  vpc_id      = aws_vpc.main[0].id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.aws_vpc_cidr]
  }

  tags = {
    Name = "grc-claw-rds-${var.environment}"
  }
}

resource "aws_security_group" "redis" {
  count       = var.enable_aws ? 1 : 0
  name        = "grc-claw-redis-${var.environment}"
  description = "Redis security group"
  vpc_id      = aws_vpc.main[0].id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [var.aws_vpc_cidr]
  }

  tags = {
    Name = "grc-claw-redis-${var.environment}"
  }
}

resource "aws_security_group" "kafka" {
  count       = var.enable_aws ? 1 : 0
  name        = "grc-claw-kafka-${var.environment}"
  description = "Kafka security group"
  vpc_id      = aws_vpc.main[0].id

  ingress {
    from_port   = 9092
    to_port     = 9092
    protocol    = "tcp"
    cidr_blocks = [var.aws_vpc_cidr]
  }

  ingress {
    from_port   = 9094
    to_port     = 9094
    protocol    = "tcp"
    cidr_blocks = [var.aws_vpc_cidr]
  }

  tags = {
    Name = "grc-claw-kafka-${var.environment}"
  }
}

# =============================================================================
# AWS Subnet Groups
# =============================================================================

resource "aws_db_subnet_group" "main" {
  count      = var.enable_aws ? 1 : 0
  name       = "grc-claw-${var.environment}"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "grc-claw-${var.environment}"
  }
}

resource "aws_elasticache_subnet_group" "main" {
  count      = var.enable_aws ? 1 : 0
  name       = "grc-claw-${var.environment}"
  subnet_ids = aws_subnet.private[*].id
}

# =============================================================================
# AWS CloudWatch
# =============================================================================

resource "aws_cloudwatch_log_group" "kafka" {
  count             = var.enable_aws ? 1 : 0
  name              = "/grc-claw/kafka/${var.environment}"
  retention_in_days = 30

  tags = {
    Name = "grc-claw-kafka-${var.environment}"
  }
}

# =============================================================================
# GCP Supporting Resources
# =============================================================================

resource "google_project_service" "container" {
  count   = var.enable_gcp ? 1 : 0
  service = "container.googleapis.com"
}

resource "google_project_service" "sqladmin" {
  count   = var.enable_gcp ? 1 : 0
  service = "sqladmin.googleapis.com"
}

resource "google_project_service" "redis" {
  count   = var.enable_gcp ? 1 : 0
  service = "redis.googleapis.com"
}

resource "google_project_service" "pubsub" {
  count   = var.enable_gcp ? 1 : 0
  service = "pubsub.googleapis.com"
}

resource "google_project_service" "bigquery" {
  count   = var.enable_gcp ? 1 : 0
  service = "bigquery.googleapis.com"
}

resource "google_service_networking_connection" "private_vpc_connection" {
  count                   = var.enable_gcp ? 1 : 0
  network                 = google_compute_network.main[0].id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_alloc[0].name]
}

resource "google_compute_global_address" "private_ip_alloc" {
  count         = var.enable_gcp ? 1 : 0
  name          = "grc-claw-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.main[0].id
}

# =============================================================================
# Azure Supporting Resources
# =============================================================================

resource "azurerm_log_analytics_workspace" "main" {
  count               = var.enable_azure ? 1 : 0
  name                = "grc-claw-${var.environment}"
  location            = azurerm_resource_group.main[0].location
  resource_group_name = azurerm_resource_group.main[0].name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_storage_account" "datalake" {
  count                    = var.enable_azure ? 1 : 0
  name                     = "grcclaw${var.environment}"
  resource_group_name      = azurerm_resource_group.main[0].name
  location                 = azurerm_resource_group.main[0].location
  account_tier             = "Standard"
  account_replication_type = "GRS"
  account_kind             = "StorageV2"
  is_hns_enabled           = true

  tags = {
    environment = var.environment
  }
}

resource "azurerm_storage_data_lake_gen2_filesystem" "main" {
  count              = var.enable_azure ? 1 : 0
  name               = "grc-claw-data"
  storage_account_id = azurerm_storage_account.datalake[0].id
}

resource "azurerm_private_dns_zone" "postgres" {
  count               = var.enable_azure ? 1 : 0
  name                = "grc-claw.postgres.database.azure.com"
  resource_group_name = azurerm_resource_group.main[0].name
}

resource "azurerm_private_dns_zone_virtual_network_link" "postgres" {
  count                 = var.enable_azure ? 1 : 0
  name                  = "grc-claw-postgres-link"
  resource_group_name   = azurerm_resource_group.main[0].name
  private_dns_zone_name = azurerm_private_dns_zone.postgres[0].name
  virtual_network_id    = azurerm_virtual_network.main[0].id
}
