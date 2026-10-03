output "bucket_names" {
  description = "Names of the created S3 buckets"
  value = [
    aws_s3_bucket.assets.id,
    aws_s3_bucket.backups.id,
    aws_s3_bucket.logs.id,
  ]
}

output "bucket_arns" {
  description = "ARNs of the created S3 buckets"
  value = [
    aws_s3_bucket.assets.arn,
    aws_s3_bucket.backups.arn,
    aws_s3_bucket.logs.arn,
  ]
}

output "assets_bucket_name" {
  description = "Name of the assets bucket"
  value       = aws_s3_bucket.assets.id
}

output "backups_bucket_name" {
  description = "Name of the backups bucket"
  value       = aws_s3_bucket.backups.id
}

output "logs_bucket_name" {
  description = "Name of the logs bucket"
  value       = aws_s3_bucket.logs.id
}
