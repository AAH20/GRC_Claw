output "app_bucket_id" {
  value = var.create_app_bucket ? aws_s3_bucket.app[0].id : null
}

output "app_bucket_arn" {
  value = var.create_app_bucket ? aws_s3_bucket.app[0].arn : null
}

output "app_bucket_domain_name" {
  value = var.create_app_bucket ? aws_s3_bucket.app[0].bucket_domain_name : null
}

output "media_bucket_id" {
  value = var.create_media_bucket ? aws_s3_bucket.media[0].id : null
}

output "media_bucket_arn" {
  value = var.create_media_bucket ? aws_s3_bucket.media[0].arn : null
}

output "media_bucket_domain_name" {
  value = var.create_media_bucket ? aws_s3_bucket.media[0].bucket_domain_name : null
}

output "logs_bucket_id" {
  value = var.create_logs_bucket ? aws_s3_bucket.logs[0].id : null
}

output "logs_bucket_arn" {
  value = var.create_logs_bucket ? aws_s3_bucket.logs[0].arn : null
}

output "logs_bucket_domain_name" {
  value = var.create_logs_bucket ? aws_s3_bucket.logs[0].bucket_domain_name : null
}
