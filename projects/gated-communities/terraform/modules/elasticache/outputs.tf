output "cluster_id" {
  description = "ID of the ElastiCache cluster"
  value       = aws_elasticache_replication_group.main.id
}

output "primary_endpoint" {
  description = "Primary endpoint of the ElastiCache cluster"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "port" {
  description = "Port of the ElastiCache cluster"
  value       = aws_elasticache_replication_group.main.port
}

output "subnet_group_name" {
  description = "Name of the cache subnet group"
  value       = aws_elasticache_subnet_group.main.name
}
