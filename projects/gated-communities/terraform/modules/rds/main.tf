terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ─── DB Subnet Group ──────────────────────────────────────────────────────────

resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-db-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-db-subnet-group"
  })
}

# ─── DB Parameter Group ───────────────────────────────────────────────────────

resource "aws_db_parameter_group" "main" {
  name   = "${var.project_name}-${var.environment}-db-params"
  family = "${var.db_engine}${split(".", var.db_engine_version)[0]}"

  parameter {
    name  = "log_connections"
    value = "1"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"
  }

  parameter {
    name  = "log_duration"
    value = "1"
  }

  tags = var.common_tags

  lifecycle {
    create_before_destroy = true
  }
}

# ─── Security Group ───────────────────────────────────────────────────────────

resource "aws_security_group" "rds" {
  name        = "${var.project_name}-${var.environment}-rds-sg"
  description = "Security group for RDS"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.main.cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-rds-sg"
  })
}

data "aws_vpc" "main" {
  id = var.vpc_id
}

# ─── RDS Instance ─────────────────────────────────────────────────────────────

resource "aws_db_instance" "main" {
  identifier = "${var.project_name}-${var.environment}-db"

  engine         = var.db_engine
  engine_version = var.db_engine_version
  instance_class = var.db_instance_class

  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_allocated_storage * 2
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password
  port     = 5432

  multi_az               = true
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  parameter_group_name   = aws_db_parameter_group.main.name

  backup_retention_period   = 30
  backup_window             = "03:00-04:00"
  maintenance_window        = "Mon:04:00-Mon:05:00"
  auto_minor_version_upgrade = true

  performance_insights_enabled    = true
  performance_insights_retention_period = 7

  deletion_protection = true
  skip_final_snapshot = false
  final_snapshot_identifier = "${var.project_name}-${var.environment}-db-final"

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-db"
  })
}

# ─── CloudWatch Alarms ────────────────────────────────────────────────────────

resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name          = "${var.project_name}-${var.environment}-rds-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "RDS CPU utilization is above 80% for 15 minutes"
  alarm_actions       = []

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }

  tags = var.common_tags
}

resource "aws_cloudwatch_metric_alarm" "rds_storage" {
  alarm_name          = "${var.project_name}-${var.environment}-rds-low-storage"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 5368709120  # 5 GB in bytes
  alarm_description   = "RDS free storage space is below 5 GB"
  alarm_actions       = []

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }

  tags = var.common_tags
}
