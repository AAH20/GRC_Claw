# =============================================================================
# Monitoring Module — CloudWatch
# =============================================================================

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "eks_cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = ""
}

variable "rds_instance_id" {
  description = "ID of the RDS instance"
  type        = string
  default     = ""
}

variable "elasticache_cluster_id" {
  description = "ID of the ElastiCache cluster"
  type        = string
  default     = ""
}

variable "enable_rds_alarms" {
  description = "Whether to enable RDS alarms"
  type        = bool
  default     = true
}

variable "enable_elasticache_alarms" {
  description = "Whether to enable ElastiCache alarms"
  type        = bool
  default     = true
}

variable "enable_eks_alarms" {
  description = "Whether to enable EKS alarms"
  type        = bool
  default     = true
}

variable "alarm_notification_arns" {
  description = "List of SNS topic ARNs for alarm notifications"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# -----------------------------------------------------------------------------
# SNS Topic for Alarms
# -----------------------------------------------------------------------------

resource "aws_sns_topic" "alarms" {
  name = "${var.name_prefix}-alarms"

  tags = var.tags
}

# -----------------------------------------------------------------------------
# RDS Alarms
# -----------------------------------------------------------------------------

resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  count = var.enable_rds_alarms ? 1 : 0

  alarm_name          = "${var.name_prefix}-rds-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "RDS CPU utilization is above 80%"

  dimensions = {
    DBInstanceIdentifier = var.rds_instance_id
  }

  alarm_actions = var.alarm_notification_arns
  ok_actions    = var.alarm_notification_arns

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "rds_storage" {
  count = var.enable_rds_alarms ? 1 : 0

  alarm_name          = "${var.name_prefix}-rds-low-storage"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 5368709120 # 5 GB in bytes
  alarm_description   = "RDS free storage space is below 5 GB"

  dimensions = {
    DBInstanceIdentifier = var.rds_instance_id
  }

  alarm_actions = var.alarm_notification_arns
  ok_actions    = var.alarm_notification_arns

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "rds_connections" {
  count = var.enable_rds_alarms ? 1 : 0

  alarm_name          = "${var.name_prefix}-rds-high-connections"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "RDS database connections are above 80"

  dimensions = {
    DBInstanceIdentifier = var.rds_instance_id
  }

  alarm_actions = var.alarm_notification_arns
  ok_actions    = var.alarm_notification_arns

  tags = var.tags
}

# -----------------------------------------------------------------------------
# ElastiCache Alarms
# -----------------------------------------------------------------------------

resource "aws_cloudwatch_metric_alarm" "elasticache_cpu" {
  count = var.enable_elasticache_alarms ? 1 : 0

  alarm_name          = "${var.name_prefix}-elasticache-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "ElastiCache CPU utilization is above 80%"

  dimensions = {
    CacheClusterId = var.elasticache_cluster_id
  }

  alarm_actions = var.alarm_notification_arns
  ok_actions    = var.alarm_notification_arns

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "elasticache_memory" {
  count = var.enable_elasticache_alarms ? 1 : 0

  alarm_name          = "${var.name_prefix}-elasticache-high-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "DatabaseMemoryUsagePercentage"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "ElastiCache memory usage is above 80%"

  dimensions = {
    CacheClusterId = var.elasticache_cluster_id
  }

  alarm_actions = var.alarm_notification_arns
  ok_actions    = var.alarm_notification_arns

  tags = var.tags
}

# -----------------------------------------------------------------------------
# EKS Alarms
# -----------------------------------------------------------------------------

resource "aws_cloudwatch_metric_alarm" "eks_node_cpu" {
  count = var.enable_eks_alarms ? 1 : 0

  alarm_name          = "${var.name_prefix}-eks-high-node-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "node_cpu_utilization"
  namespace           = "ContainerInsights"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "EKS node CPU utilization is above 80%"

  dimensions = {
    ClusterName = var.eks_cluster_name
  }

  alarm_actions = var.alarm_notification_arns
  ok_actions    = var.alarm_notification_arns

  tags = var.tags
}

# -----------------------------------------------------------------------------
# CloudWatch Dashboard
# -----------------------------------------------------------------------------

resource "aws_cloudwatch_dashboard" "this" {
  dashboard_name = "${var.name_prefix}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "RDS CPU Utilization"
          region = "us-east-1"
          metrics = [
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", var.rds_instance_id]
          ]
          period = 300
          stat   = "Average"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "ElastiCache CPU Utilization"
          region = "us-east-1"
          metrics = [
            ["AWS/ElastiCache", "CPUUtilization", "CacheClusterId", var.elasticache_cluster_id]
          ]
          period = 300
          stat   = "Average"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "RDS Connections"
          region = "us-east-1"
          metrics = [
            ["AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier", var.rds_instance_id]
          ]
          period = 300
          stat   = "Average"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "ElastiCache Memory Usage"
          region = "us-east-1"
          metrics = [
            ["AWS/ElastiCache", "DatabaseMemoryUsagePercentage", "CacheClusterId", var.elasticache_cluster_id]
          ]
          period = 300
          stat   = "Average"
        }
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------

output "dashboard_name" {
  description = "Name of the CloudWatch dashboard"
  value       = aws_cloudwatch_dashboard.this.dashboard_name
}

output "dashboard_arn" {
  description = "ARN of the CloudWatch dashboard"
  value       = aws_cloudwatch_dashboard.this.dashboard_arn
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic for alarm notifications"
  value       = aws_sns_topic.alarms.arn
}
