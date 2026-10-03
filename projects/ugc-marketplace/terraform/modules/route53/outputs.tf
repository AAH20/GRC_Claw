output "zone_id" {
  value = var.route53_zone_id
}

output "record_fqdns" {
  value = compact([
    var.cloudfront_domain_name != "" ? aws_route53_record.cloudfront[0].fqdn : "",
    var.alb_dns_name != null ? aws_route53_record.alb[0].fqdn : "",
  ])
}
