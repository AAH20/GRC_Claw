# =============================================================================
# UGC Marketplace — Root Module
# =============================================================================
# Production-grade infrastructure for the UGC Marketplace platform.
# Provisions: VPC, EKS, RDS (PostgreSQL), ElastiCache (Redis), S3, CloudFront
# =============================================================================

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.40"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.27"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Remote state — uncomment and configure after bootstrapping the backend
  # backend "s3" {
  #   bucket         = "ugc-marketplace-terraform-state"
  #   key            = "prod/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "ugc-marketplace-terraform-locks"
  # }
}

# -----------------------------------------------------------------------------
# Providers
# -----------------------------------------------------------------------------

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"

  default_tags {
    tags = local.common_tags
  }
}

# -----------------------------------------------------------------------------
# Data Sources
# -----------------------------------------------------------------------------

data "aws_caller_identity" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_route53_zone" "primary" {
  count        = var.create_route53_zone ? 0 : 1
  name         = var.domain_name
  private_zone = false
}

# -----------------------------------------------------------------------------
# Local Values
# -----------------------------------------------------------------------------

locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Owner       = var.owner
    CostCenter  = var.cost_center
  }

  vpc_cidr = var.vpc_cidr

  # Public subnets: 1 per AZ (for ALB, NAT Gateway)
  public_subnet_cidrs = [
    for i in range(var.availability_zone_count) : cidrsubnet(local.vpc_cidr, 8, i)
  ]

  # Private subnets: 1 per AZ (for EKS nodes, RDS, ElastiCache)
  private_subnet_cidrs = [
    for i in range(var.availability_zone_count) : cidrsubnet(local.vpc_cidr, 8, i + 100)
  ]

  # Database subnets: 1 per AZ (for RDS, ElastiCache — isolated from public)
  database_subnet_cidrs = [
    for i in range(var.availability_zone_count) : cidrsubnet(local.vpc_cidr, 8, i + 200)
  ]

  azs = slice(data.aws_availability_zones.available.names, 0, var.availability_zone_count)
}

# -----------------------------------------------------------------------------
# Random Suffix (for globally-unique resource names)
# -----------------------------------------------------------------------------

resource "random_id" "suffix" {
  byte_length = 4
}

# =============================================================================
# MODULE: Networking (VPC)
# =============================================================================

module "vpc" {
  source = "./modules/vpc"

  name_prefix           = local.name_prefix
  vpc_cidr              = local.vpc_cidr
  availability_zones    = local.azs
  public_subnet_cidrs   = local.public_subnet_cidrs
  private_subnet_cidrs  = local.private_subnet_cidrs
  database_subnet_cidrs = local.database_subnet_cidrs

  enable_nat_gateway     = var.enable_nat_gateway
  single_nat_gateway     = var.single_nat_gateway
  enable_flow_logs       = var.enable_vpc_flow_logs
  flow_logs_retention_days = var.flow_logs_retention_days

  tags = local.common_tags
}

# =============================================================================
# MODULE: Security (Security Groups, KMS)
# =============================================================================

module "security" {
  source = "./modules/security"

  name_prefix = local.name_prefix
  vpc_id      = module.vpc.vpc_id
  vpc_cidr    = local.vpc_cidr

  # EKS
  eks_cluster_security_group_id = module.eks.cluster_security_group_id

  # RDS
  rds_engine         = var.rds_engine
  rds_engine_version = var.rds_engine_version
  rds_instance_class = var.rds_instance_class
  rds_port           = var.rds_port

  # ElastiCache
  elasticache_engine         = var.elasticache_engine
  elasticache_engine_version = var.elasticache_engine_version
  elasticache_node_type      = var.elasticache_node_type
  elasticache_port           = var.elasticache_port

  tags = local.common_tags
}

# =============================================================================
# MODULE: EKS (Kubernetes)
# =============================================================================

module "eks" {
  source = "./modules/eks"

  name_prefix = local.name_prefix
  cluster_version = var.eks_cluster_version

  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids

  # Managed node groups
  node_groups = var.eks_node_groups

  # Cluster access
  cluster_endpoint_private_access = var.eks_cluster_endpoint_private_access
  cluster_endpoint_public_access  = var.eks_cluster_endpoint_public_access
  cluster_endpoint_public_access_cidrs = var.eks_cluster_endpoint_public_access_cidrs

  # Encryption
  cluster_encryption_key_arn = module.security.eks_kms_key_arn

  # Logging
  cluster_enabled_log_types = var.eks_cluster_enabled_log_types

  tags = local.common_tags
}

# =============================================================================
# MODULE: RDS (PostgreSQL)
# =============================================================================

module "rds" {
  source = "./modules/rds"

  name_prefix = local.name_prefix

  vpc_id             = module.vpc.vpc_id
  database_subnet_ids = module.vpc.database_subnet_ids

  engine         = var.rds_engine
  engine_version = var.rds_engine_version
  instance_class = var.rds_instance_class
  port           = var.rds_port

  database_name     = var.rds_database_name
  master_username   = var.rds_master_username
  master_password   = var.rds_master_password

  allocated_storage     = var.rds_allocated_storage
  max_allocated_storage = var.rds_max_allocated_storage
  storage_type          = var.rds_storage_type
  storage_encrypted     = var.rds_storage_encrypted
  kms_key_id            = module.security.rds_kms_key_arn

  multi_az                = var.rds_multi_az
  backup_retention_period = var.rds_backup_retention_period
  backup_window           = var.rds_backup_window
  maintenance_window      = var.rds_maintenance_window
  deletion_protection     = var.rds_deletion_protection
  skip_final_snapshot     = var.rds_skip_final_snapshot
  final_snapshot_identifier = var.rds_final_snapshot_identifier

  performance_insights_enabled    = var.rds_performance_insights_enabled
  performance_insights_kms_key_id = module.security.rds_kms_key_arn

  security_group_ids = [module.security.rds_security_group_id]

  tags = local.common_tags
}

# =============================================================================
# MODULE: ElastiCache (Redis)
# =============================================================================

module "elasticache" {
  source = "./modules/elasticache"

  name_prefix = local.name_prefix

  vpc_id             = module.vpc.vpc_id
  database_subnet_ids = module.vpc.database_subnet_ids

  engine         = var.elasticache_engine
  engine_version = var.elasticache_engine_version
  node_type      = var.elasticache_node_type
  port           = var.elasticache_port

  num_cache_nodes       = var.elasticache_num_cache_nodes
  automatic_failover_enabled = var.elasticache_automatic_failover_enabled
  multi_az_enabled      = var.elasticache_multi_az_enabled

  at_rest_encryption_enabled = var.elasticache_at_rest_encryption_enabled
  transit_encryption_enabled = var.elasticache_transit_encryption_enabled
  kms_key_id                 = module.security.elasticache_kms_key_arn

  snapshot_retention_limit = var.elasticache_snapshot_retention_limit
  snapshot_window          = var.elasticache_snapshot_window
  maintenance_window       = var.elasticache_maintenance_window

  security_group_ids = [module.security.elasticache_security_group_id]

  tags = local.common_tags
}

# =============================================================================
# MODULE: S3 (Storage)
# =============================================================================

module "s3" {
  source = "./modules/s3"

  name_prefix = local.name_prefix

  # Application bucket
  create_app_bucket       = var.s3_create_app_bucket
  app_bucket_name         = "${local.name_prefix}-app-data-${random_id.suffix.hex}"
  app_bucket_versioning   = var.s3_app_bucket_versioning
  app_bucket_lifecycle_rules = var.s3_app_bucket_lifecycle_rules
  app_bucket_cors_rules   = var.s3_app_bucket_cors_rules

  # Media/Assets bucket
  create_media_bucket       = var.s3_create_media_bucket
  media_bucket_name         = "${local.name_prefix}-media-${random_id.suffix.hex}"
  media_bucket_versioning   = var.s3_media_bucket_versioning
  media_bucket_cors_rules   = var.s3_media_bucket_cors_rules

  # Logs bucket
  create_logs_bucket       = var.s3_create_logs_bucket
  logs_bucket_name         = "${local.name_prefix}-logs-${random_id.suffix.hex}"
  logs_bucket_lifecycle_rules = var.s3_logs_bucket_lifecycle_rules

  # Encryption
  kms_key_id = module.security.s3_kms_key_arn

  # Block public access
  block_public_acls       = var.s3_block_public_acls
  block_public_policy     = var.s3_block_public_policy
  ignore_public_acls      = var.s3_ignore_public_acls
  restrict_public_buckets = var.s3_restrict_public_buckets

  tags = local.common_tags
}

# =============================================================================
# MODULE: CloudFront (CDN)
# =============================================================================

module "cloudfront" {
  source = "./modules/cloudfront"

  name_prefix = local.name_prefix

  # Origins
  s3_media_bucket_domain_name = module.s3.media_bucket_domain_name
  s3_app_bucket_domain_name    = module.s3.app_bucket_domain_name

  # ALB origin (if created)
  create_alb_origin = var.cloudfront_create_alb_origin
  alb_dns_name      = var.cloudfront_create_alb_origin ? module.eks.alb_dns_name : null

  # Cache behaviors
  default_cache_behavior_ttl            = var.cloudfront_default_cache_ttl
  default_cache_behavior_max_ttl        = var.cloudfront_default_cache_max_ttl
  default_cache_behavior_compress       = var.cloudfront_default_cache_compress
  ordered_cache_behaviors               = var.cloudfront_ordered_cache_behaviors

  # SSL/TLS
  acm_certificate_arn = var.cloudfront_acm_certificate_arn
  aliases             = var.cloudfront_aliases

  # Logging
  enable_logging       = var.cloudfront_enable_logging
  logs_bucket_domain_name = module.s3.logs_bucket_domain_name

  # WAF
  create_waf           = var.cloudfront_create_waf
  waf_web_acl_arn      = var.cloudfront_waf_web_acl_arn

  tags = local.common_tags
}

# =============================================================================
# MODULE: Route 53 (DNS)
# =============================================================================

module "route53" {
  source = "./modules/route53"

  count = var.create_route53_records ? 1 : 0

  name_prefix = local.name_prefix

  domain_name    = var.domain_name
  route53_zone_id = var.create_route53_zone ? null : data.aws_route53_zone.primary[0].zone_id

  # Records
  cloudfront_domain_name = module.cloudfront.cloudfront_domain_name
  cloudfront_hosted_zone_id = module.cloudfront.cloudfront_hosted_zone_id

  alb_dns_name = var.cloudfront_create_alb_origin ? module.eks.alb_dns_name : null

  tags = local.common_tags
}

# =============================================================================
# MODULE: Monitoring (CloudWatch)
# =============================================================================

module "monitoring" {
  source = "./modules/monitoring"

  name_prefix = local.name_prefix

  # EKS
  eks_cluster_name = module.eks.cluster_name

  # RDS
  rds_instance_id = module.rds.instance_id

  # ElastiCache
  elasticache_cluster_id = module.elasticache.cluster_id

  # Alarms
  enable_rds_alarms       = var.monitoring_enable_rds_alarms
  enable_elasticache_alarms = var.monitoring_enable_elasticache_alarms
  enable_eks_alarms       = var.monitoring_enable_eks_alarms

  alarm_notification_arns = var.monitoring_alarm_notification_arns

  tags = local.common_tags
}
