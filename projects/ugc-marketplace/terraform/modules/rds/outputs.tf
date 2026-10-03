output "instance_id" {
  value = aws_db_instance.this.id
}

output "instance_arn" {
  value = aws_db_instance.this.arn
}

output "instance_endpoint" {
  value = aws_db_instance.this.endpoint
}

output "instance_address" {
  value = aws_db_instance.this.address
}

output "instance_port" {
  value = aws_db_instance.this.port
}

output "database_name" {
  value = aws_db_instance.this.db_name
}

output "master_username" {
  value = aws_db_instance.this.username
}

output "security_group_id" {
  value = var.security_group_ids[0]
}
