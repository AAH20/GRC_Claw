# =============================================================================
# Route 53 Module — DNS
# =============================================================================

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "domain_name" {
  description = "Primary domain name"
  type        = string
}

variable "route53_zone_id" {
  description = "ID of the Route 53 hosted zone"
  type        = string
  default     = null
}

variable "cloudfront_domain_name" {
  description = "Domain name of the CloudFront distribution"
  type        = string
  default     = ""
}

variable "cloudfront_hosted_zone_id" {
  description = "Hosted zone ID of the CloudFront distribution"
  type        = string
  default     = ""
}

variable "alb_dns_name" {
  description = "DNS name of the ALB"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# -----------------------------------------------------------------------------
# Route 53 Records
# -----------------------------------------------------------------------------

resource "aws_route53_record" "cloudfront" {
  count = var.cloudfront_domain_name != "" ? 1 : 0

  zone_id = var.route53_zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = var.cloudfront_domain_name
    zone_id                = var.cloudfront_hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "cloudfront_ipv6" {
  count = var.cloudfront_domain_name != "" ? 1 : 0

  zone_id = var.route53_zone_id
  name    = var.domain_name
  type    = "AAAA"

  alias {
    name                   = var.cloudfront_domain_name
    zone_id                = var.cloudfront_hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "alb" {
  count = var.alb_dns_name != null ? 1 : 0

  zone_id = var.route53_zone_id
  name    = "api.${var.domain_name}"
  type    = "A"

  alias {
    name                   = var.alb_dns_name
    zone_id                = "Z35SXDOTRQ7X7K" # ALB hosted zone ID (us-east-1)
    evaluate_target_health = true
  }
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------

output "zone_id" {
  description = "ID of the Route 53 hosted zone"
  value       = var.route53_zone_id
}

output "record_fqdns" {
  description = "FQDNs of the Route 53 records"
  value = compact([
    var.cloudfront_domain_name != "" ? aws_route53_record.cloudfront[0].fqdn : "",
    var.alb_dns_name != null ? aws_route53_record.alb[0].fqdn : "",
  ])
}
