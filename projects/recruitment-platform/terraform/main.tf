terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  backend "s3" {
    bucket         = "recruitment-platform-terraform-state"
    key            = "infrastructure/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "recruitment-platform-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
  token                  = data.aws_eks_cluster_auth.this.token
}

provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
    token                  = data.aws_eks_cluster_auth.this.token
  }
}

# -----------------------------------------------------------------------------
# Data Sources
# -----------------------------------------------------------------------------

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

data "aws_eks_cluster_auth" "this" {
  name = module.eks.cluster_name
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

  cluster_name = "${local.name_prefix}-eks"

  vpc_cidr = var.vpc_cidr

  private_subnets = [
    for i in range(var.az_count) : cidrsubnet(local.vpc_cidr, 8, i)
  ]

  public_subnets = [
    for i in range(var.az_count) : cidrsubnet(local.vpc_cidr, 8, i + 100)
  ]

  database_subnets = [
    for i in range(var.az_count) : cidrsubnet(local.vpc_cidr, 8, i + 200)
  ]
}

# -----------------------------------------------------------------------------
# VPC Module
# -----------------------------------------------------------------------------

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.1"

  name = "${local.name_prefix}-vpc"
  cidr = local.vpc_cidr

  azs             = slice(data.aws_availability_zones.available.names, 0, var.az_count)
  private_subnets = local.private_subnets
  public_subnets  = local.public_subnets
  database_subnets = local.database_subnets

  enable_nat_gateway     = true
  single_nat_gateway     = var.environment != "production"
  enable_dns_hostnames   = true
  enable_dns_support     = true
  enable_flow_log        = true

  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = "1"
  }

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# EKS Module
# -----------------------------------------------------------------------------

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.16"

  cluster_name    = local.cluster_name
  cluster_version = var.kubernetes_version

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cluster_endpoint_private_access = true
  cluster_endpoint_public_access  = var.eks_public_access

  cluster_enabled_log_types = [
    "api",
    "audit",
    "authenticator",
    "controllerManager",
    "scheduler"
  ]

  cluster_encryption_config = {
    provider_key_arn = aws_kms_key.eks.arn
    resources        = ["secrets"]
  }

  eks_managed_node_groups = {
    general = {
      name           = "${local.name_prefix}-general"
      instance_types = var.eks_node_instance_types

      min_size     = var.eks_node_min_size
      max_size     = var.eks_node_max_size
      desired_size = var.eks_node_desired_size

      capacity_type  = "ON_DEMAND"
      disk_size      = 100
      disk_type      = "gp3"

      labels = {
        role = "general"
      }

      tags = local.common_tags
    }

    spot = {
      name           = "${local.name_prefix}-spot"
      instance_types = var.eks_spot_instance_types

      min_size     = var.eks_spot_min_size
      max_size     = var.eks_spot_max_size
      desired_size = var.eks_spot_desired_size

      capacity_type = "SPOT"
      disk_size     = 100
      disk_type     = "gp3"

      labels = {
        role = "spot"
      }

      taints = [{
        key    = "spot"
        value  = "true"
        effect = "NO_SCHEDULE"
      }]

      tags = local.common_tags
    }
  }

  cluster_addons = {
    coredns = {
      most_recent = true
      configuration_values = jsonencode({
        computeType = "Fargate"
      })
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent = true
    }
  }

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# KMS Key for EKS Secrets Encryption
# -----------------------------------------------------------------------------

resource "aws_kms_key" "eks" {
  description             = "KMS key for EKS secrets encryption - ${local.name_prefix}"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = local.common_tags
}

resource "aws_kms_alias" "eks" {
  name          = "alias/${local.name_prefix}-eks"
  target_key_id = aws_kms_key.eks.key_id
}

# -----------------------------------------------------------------------------
# RDS Module (PostgreSQL)
# -----------------------------------------------------------------------------

module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.1"

  identifier = "${local.name_prefix}-postgres"

  engine               = "postgres"
  engine_version       = var.rds_engine_version
  family               = "postgres${split(".", var.rds_engine_version)[0]}"
  major_engine_version = split(".", var.rds_engine_version)[0]
  instance_class       = var.rds_instance_class

  allocated_storage     = var.rds_allocated_storage
  max_allocated_storage = var.rds_max_allocated_storage

  db_name  = var.rds_database_name
  username = var.rds_username
  port     = 5432

  multi_az               = var.environment == "production"
  db_subnet_group_name   = module.vpc.database_subnet_group
  vpc_security_group_ids = [aws_security_group.rds.id]

  maintenance_window      = "Mon:03:00-Mon:04:00"
  backup_window           = "04:00-05:00"
  backup_retention_period = var.rds_backup_retention

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  deletion_protection = var.environment == "production"
  skip_final_snapshot = var.environment != "production"
  final_snapshot_identifier = var.environment == "production" ? "${local.name_prefix}-final-snapshot" : null

  performance_insights_enabled    = true
  performance_insights_kms_key_id = aws_kms_key.rds.arn

  create_monitoring_role = true
  monitoring_interval    = 60

  parameters = [
    {
      name  = "autovacuum"
      value = "1"
    },
    {
      name  = "client_encoding"
      value = "UTF8"
    }
  ]

  tags = local.common_tags
}

resource "aws_kms_key" "rds" {
  description             = "KMS key for RDS encryption - ${local.name_prefix}"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = local.common_tags
}

resource "aws_security_group" "rds" {
  name_prefix = "${local.name_prefix}-rds-"
  description = "Security group for RDS PostgreSQL"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description     = "PostgreSQL from EKS"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [module.eks.cluster_security_group_id]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags

  lifecycle {
    create_before_destroy = true
  }
}

# -----------------------------------------------------------------------------
# ElastiCache Module (Redis)
# -----------------------------------------------------------------------------

module "elasticache" {
  source  = "terraform-aws-modules/elasticache/aws"
  version = "~> 1.0"

  cluster_id               = "${local.name_prefix}-redis"
  create_cluster           = false
  create_replication_group = true

  engine               = "redis"
  engine_version       = var.elasticache_engine_version
  node_type            = var.elasticache_node_type
  num_cache_clusters   = var.elasticache_num_cache_clusters
  automatic_failover_enabled = var.environment == "production"

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = random_password.redis_auth_token.result

  subnet_group_name  = aws_elasticache_subnet_group.redis.name
  security_group_ids = [aws_security_group.elasticache.id]

  log_delivery_configuration = {
    slow-log = {
      destination      = aws_cloudwatch_log_group.redis_slow.name
      destination_type = "cloudwatch-logs"
      log_format        = "json"
    }
  }

  tags = local.common_tags
}

resource "random_password" "redis_auth_token" {
  length  = 32
  special = false
}

resource "aws_elasticache_subnet_group" "redis" {
  name       = "${local.name_prefix}-redis-subnet"
  subnet_ids = module.vpc.database_subnets
}

resource "aws_security_group" "elasticache" {
  name_prefix = "${local.name_prefix}-elasticache-"
  description = "Security group for ElastiCache Redis"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description     = "Redis from EKS"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [module.eks.cluster_security_group_id]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_cloudwatch_log_group" "redis_slow" {
  name              = "/aws/elasticache/${local.name_prefix}-redis/slow-log"
  retention_in_days = 30

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# S3 Buckets
# -----------------------------------------------------------------------------

resource "aws_s3_bucket" "app_storage" {
  bucket = "${local.name_prefix}-app-storage-${data.aws_caller_identity.current.account_id}"

  tags = local.common_tags
}

resource "aws_s3_bucket_versioning" "app_storage" {
  bucket = aws_s3_bucket.app_storage.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "app_storage" {
  bucket = aws_s3_bucket.app_storage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "app_storage" {
  bucket = aws_s3_bucket.app_storage.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "app_storage" {
  bucket = aws_s3_bucket.app_storage.id

  rule {
    id     = "transition-to-ia"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 365
      storage_class = "GLACIER"
    }
  }
}

resource "aws_s3_bucket" "backups" {
  bucket = "${local.name_prefix}-backups-${data.aws_caller_identity.current.account_id}"

  tags = local.common_tags
}

resource "aws_s3_bucket_versioning" "backups" {
  bucket = aws_s3_bucket.backups.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "backups" {
  bucket = aws_s3_bucket.backups.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    id     = "expire-old-backups"
    status = "Enabled"

    expiration {
      days = var.backup_retention_days
    }
  }
}

resource "aws_kms_key" "s3" {
  description             = "KMS key for S3 encryption - ${local.name_prefix}"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# IAM Roles for Service Accounts (IRSA)
# -----------------------------------------------------------------------------

module "eks_admin_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.20"

  role_name = "${local.name_prefix}-admin"

  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["kube-system:admin"]
    }
  }

  tags = local.common_tags
}

module "cert_manager_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.20"

  role_name = "${local.name_prefix}-cert-manager"

  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["cert-manager:cert-manager"]
    }
  }

  role_policy_arns = {
    route53 = aws_iam_policy.cert_manager_route53.arn
  }

  tags = local.common_tags
}

module "external_dns_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.20"

  role_name = "${local.name_prefix}-external-dns"

  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["kube-system:external-dns"]
    }
  }

  role_policy_arns = {
    route53 = aws_iam_policy.external_dns_route53.arn
  }

  tags = local.common_tags
}

module "aws_load_balancer_controller_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.20"

  role_name = "${local.name_prefix}-aws-load-balancer-controller"

  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["kube-system:aws-load-balancer-controller"]
    }
  }

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# IAM Policies
# -----------------------------------------------------------------------------

resource "aws_iam_policy" "cert_manager_route53" {
  name        = "${local.name_prefix}-cert-manager-route53"
  description = "Policy for cert-manager Route53 access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "route53:GetChange",
          "route53:ChangeResourceRecordSets",
          "route53:ListResourceRecordSets",
          "route53:ListHostedZones",
          "route53:ListHostedZonesByName"
        ]
        Resource = "*"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_policy" "external_dns_route53" {
  name        = "${local.name_prefix}-external-dns-route53"
  description = "Policy for external-dns Route53 access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "route53:ChangeResourceRecordSets",
          "route53:ListResourceRecordSets",
          "route53:ListHostedZones",
          "route53:ListHostedZonesByName"
        ]
        Resource = "*"
      }
    ]
  })

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# Security Groups
# -----------------------------------------------------------------------------

resource "aws_security_group" "eks_nodes" {
  name_prefix = "${local.name_prefix}-eks-nodes-"
  description = "Security group for EKS worker nodes"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "Allow inter-node communication"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    self        = true
  }

  ingress {
    description     = "Allow control plane to worker nodes"
    from_port       = 1025
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [module.eks.cluster_security_group_id]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags

  lifecycle {
    create_before_destroy = true
  }
}

# -----------------------------------------------------------------------------
# CloudWatch Log Groups
# -----------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "vpc_flow" {
  name              = "/aws/vpc/${local.name_prefix}-flow-logs"
  retention_in_days = 30

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# AWS Backup
# -----------------------------------------------------------------------------

resource "aws_backup_vault" "main" {
  name        = "${local.name_prefix}-backup-vault"
  kms_key_arn = aws_kms_key.s3.arn

  tags = local.common_tags
}

resource "aws_backup_plan" "main" {
  name = "${local.name_prefix}-backup-plan"

  rule {
    rule_name         = "daily-backup"
    target_vault_name = aws_backup_vault.main.name
    schedule          = "cron(0 5 ? * * *)"

    lifecycle {
      delete_after = 35
    }
  }

  rule {
    rule_name         = "weekly-backup"
    target_vault_name = aws_backup_vault.main.name
    schedule          = "cron(0 5 ? * 1 *)"

    lifecycle {
      delete_after = 90
    }
  }

  tags = local.common_tags
}

resource "aws_backup_selection" "main" {
  iam_role_arn = aws_iam_role.backup.arn
  name         = "${local.name_prefix}-backup-selection"
  plan_id      = aws_backup_plan.main.id

  selection_tag {
    type  = "STRINGEQUALS"
    key   = "Backup"
    value = "true"
  }
}

resource "aws_iam_role" "backup" {
  name               = "${local.name_prefix}-backup-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "backup.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "backup" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
  role       = aws_iam_role.backup.name
}
