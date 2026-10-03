output "cluster_name" {
  value = aws_eks_cluster.this.name
}

output "cluster_arn" {
  value = aws_eks_cluster.this.arn
}

output "cluster_endpoint" {
  value = aws_eks_cluster.this.endpoint
}

output "cluster_certificate_authority_data" {
  value = aws_eks_cluster.this.certificate_authority[0].data
}

output "cluster_security_group_id" {
  value = aws_security_group.cluster.id
}

output "oidc_provider_arn" {
  value = aws_iam_openid_connect_provider.eks.arn
}

output "node_group_arns" {
  value = { for k, v in aws_eks_node_group.this : k => v.arn }
}

output "node_group_ids" {
  value = { for k, v in aws_eks_node_group.this : k => v.id }
}

output "alb_dns_name" {
  value = ""
}
