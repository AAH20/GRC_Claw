output "dashboard_name" {
  value = aws_cloudwatch_dashboard.this.dashboard_name
}

output "dashboard_arn" {
  value = aws_cloudwatch_dashboard.this.dashboard_arn
}

output "sns_topic_arn" {
  value = aws_sns_topic.alarms.arn
}
