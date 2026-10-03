output "eks_kms_key_arn" {
  value = aws_kms_key.eks.arn
}

output "eks_kms_key_id" {
  value = aws_kms_key.eks.key_id
}

output "rds_kms_key_arn" {
  value = aws_kms_key.rds.arn
}

output "rds_kms_key_id" {
  value = aws_kms_key.rds.key_id
}

output "elasticache_kms_key_arn" {
  value = aws_kms_key.elasticache.arn
}

output "elasticache_kms_key_id" {
  value = aws_kms_key.elasticache.key_id
}

output "s3_kms_key_arn" {
  value = aws_kms_key.s3.arn
}

output "s3_kms_key_id" {
  value = aws_kms_key.s3.key_id
}

output "eks_nodes_security_group_id" {
  value = aws_security_group.eks_nodes.id
}

output "rds_security_group_id" {
  value = aws_security_group.rds.id
}

output "elasticache_security_group_id" {
  value = aws_security_group.elasticache.id
}
