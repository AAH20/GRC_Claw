output "cluster_id" {
  value = aws_elasticache_replication_group.this.id
}

output "cluster_arn" {
  value = aws_elasticache_replication_group.this.arn
}

output "primary_endpoint" {
  value = aws_elasticache_replication_group.this.primary_endpoint_address
}

output "reader_endpoint" {
  value = aws_elasticache_replication_group.this.reader_endpoint_address
}

output "port" {
  value = aws_elasticache_replication_group.this.port
}

output "security_group_id" {
  value = var.security_group_ids[0]
}
