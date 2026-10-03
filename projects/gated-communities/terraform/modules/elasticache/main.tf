terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ─── ElastiCache Subnet Group ─────────────────────────────────────────────────

resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-cache-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-cache-subnet-group"
  })
}

# ─── ElastiCache Parameter Group ─────────────────────────────────────────────

resource "aws_elasticache_parameter_group" "main" {
  name   = "${var.project_name}-${var.environment}-cache-params"
  family = "redis7"

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  tags = var.common_tags
}

# ─── Security Group ───────────────────────────────────────────────────────────

resource "aws_security_group" "elasticache" {
  name        = "${var.project_name}-${var.environment}-elasticache-sg"
  description = "Security group for ElastiCache"
  vpc_id      = var.vpc_id

  ingress {
    description = "Allow Redis access from VPC"
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.main.cidr_block]
  }

  egress {
    description = "Allow outbound traffic to VPC CIDR"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [data.aws_vpc.main.cidr_block]
  }

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-elasticache-sg"
  })
}

data "aws_vpc" "main" {
  id = var.vpc_id
}

# ─── ElastiCache Replication Group ───────────────────────────────────────────

resource "aws_elasticache_replication_group" "main" {
  replication_group_id = "${var.project_name}-${var.environment}-cache"
  description          = "Redis cluster for ${var.project_name}"

  engine         = "redis"
  engine_version = "7.1"
  node_type      = var.cache_node_type

  num_cache_clusters       = var.cache_num_nodes
  automatic_failover_enabled = var.cache_num_nodes > 1
  multi_az_enabled         = var.cache_num_nodes > 1

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true

  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.elasticache.id]
  parameter_group_name = aws_elasticache_parameter_group.main.name

  snapshot_retention_limit = 7
  snapshot_window          = "05:00-06:00"
  maintenance_window       = "sun:06:00-sun:07:00"

  auto_minor_version_upgrade = true

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-cache"
  })
}
