terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "gated-communities-terraform-state"
    key            = "infrastructure/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "gated-communities-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Owner       = var.owner
  }
}

# ─── VPC Module ───────────────────────────────────────────────────────────────
module "vpc" {
  source = "./modules/vpc"

  project_name        = var.project_name
  environment         = var.environment
  vpc_cidr            = var.vpc_cidr
  availability_zones  = var.availability_zones
  private_subnet_cidrs = var.private_subnet_cidrs
  public_subnet_cidrs  = var.public_subnet_cidrs
  common_tags         = local.common_tags
}

# ─── EKS Module ───────────────────────────────────────────────────────────────
module "eks" {
  source = "./modules/eks"

  project_name       = var.project_name
  environment        = var.environment
  cluster_version    = var.eks_cluster_version
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  public_subnet_ids  = module.vpc.public_subnet_ids
  node_instance_types = var.eks_node_instance_types
  node_desired_size   = var.eks_node_desired_size
  node_min_size       = var.eks_node_min_size
  node_max_size       = var.eks_node_max_size
  common_tags         = local.common_tags
}

# ─── RDS Module ───────────────────────────────────────────────────────────────
module "rds" {
  source = "./modules/rds"

  project_name       = var.project_name
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  db_engine          = var.rds_engine
  db_engine_version  = var.rds_engine_version
  db_instance_class  = var.rds_instance_class
  db_allocated_storage = var.rds_allocated_storage
  db_name            = var.rds_db_name
  db_username        = var.rds_username
  db_password        = var.rds_password
  common_tags        = local.common_tags
}

# ─── ElastiCache Module ───────────────────────────────────────────────────────
module "elasticache" {
  source = "./modules/elasticache"

  project_name       = var.project_name
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  cache_node_type    = var.elasticache_node_type
  cache_num_nodes    = var.elasticache_num_nodes
  common_tags        = local.common_tags
}

# ─── S3 Module ────────────────────────────────────────────────────────────────
module "s3" {
  source = "./modules/s3"

  project_name = var.project_name
  environment  = var.environment
  common_tags  = local.common_tags
}
