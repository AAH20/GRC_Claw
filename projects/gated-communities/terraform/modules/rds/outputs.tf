output "instance_endpoint" {
  description = "Connection endpoint for the RDS instance"
  value       = aws_db_instance.main.endpoint
}

output "instance_address" {
  description = "Hostname of the RDS instance"
  value       = aws_db_instance.main.address
}

output "instance_port" {
  description = "Port of the RDS instance"
  value       = aws_db_instance.main.port
}

output "instance_id" {
  description = "ID of the RDS instance"
  value       = aws_db_instance.main.id
}

output "subnet_group_name" {
  description = "Name of the DB subnet group"
  value       = aws_db_subnet_group.main.name
}
