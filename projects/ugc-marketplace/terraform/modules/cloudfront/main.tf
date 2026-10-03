# =============================================================================
# CloudFront Module — CDN
# =============================================================================

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "s3_media_bucket_domain_name" {
  description = "Domain name of the S3 media bucket"
  type        = string
  default     = ""
}

variable "s3_app_bucket_domain_name" {
  description = "Domain name of the S3 app bucket"
  type        = string
  default     = ""
}

variable "create_alb_origin" {
  description = "Whether to create an ALB origin"
  type        = bool
  default     = true
}

variable "alb_dns_name" {
  description = "DNS name of the ALB"
  type        = string
  default     = null
}

variable "default_cache_behavior_ttl" {
  description = "Default TTL in seconds"
  type        = number
  default     = 86400
}

variable "default_cache_behavior_max_ttl" {
  description = "Maximum TTL in seconds"
  type        = number
  default     = 31536000
}

variable "default_cache_behavior_compress" {
  description = "Whether to compress content"
  type        = bool
  default     = true
}

variable "ordered_cache_behaviors" {
  description = "Ordered cache behaviors"
  type = list(object({
    path_pattern           = string
    target_origin_id       = string
    viewer_protocol_policy = string
    allowed_methods        = list(string)
    cached_methods         = list(string)
    compress               = bool
    ttl                    = number
    max_ttl                = number
  }))
  default = []
}

variable "acm_certificate_arn" {
  description = "ARN of the ACM certificate"
  type        = string
  default     = ""
}

variable "aliases" {
  description = "List of domain aliases"
  type        = list(string)
  default     = []
}

variable "enable_logging" {
  description = "Whether to enable access logging"
  type        = bool
  default     = true
}

variable "logs_bucket_domain_name" {
  description = "Domain name of the logs bucket"
  type        = string
  default     = ""
}

variable "create_waf" {
  description = "Whether to create a WAF WebACL"
  type        = bool
  default     = true
}

variable "waf_web_acl_arn" {
  description = "ARN of an existing WAF WebACL"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# -----------------------------------------------------------------------------
# CloudFront Distribution
# -----------------------------------------------------------------------------

resource "aws_cloudfront_distribution" "this" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "${var.name_prefix} CDN"
  default_root_object = "index.html"
  price_class         = "PriceClass_100"

  # Origin: S3 Media Bucket
  origin {
    domain_name = var.s3_media_bucket_domain_name
    origin_id   = "s3-media"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.this.cloudfront_access_identity_path
    }
  }

  # Origin: S3 App Bucket
  origin {
    domain_name = var.s3_app_bucket_domain_name
    origin_id   = "s3-app"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.this.cloudfront_access_identity_path
    }
  }

  # Origin: ALB (conditional)
  dynamic "origin" {
    for_each = var.create_alb_origin && var.alb_dns_name != null ? [1] : []
    content {
      domain_name = var.alb_dns_name
      origin_id   = "alb"

      custom_origin_config {
        http_port              = 80
        https_port             = 443
        origin_protocol_policy = "https-only"
        origin_ssl_protocols   = ["TLSv1.2"]
      }
    }
  }

  # Default cache behavior
  default_cache_behavior {
    target_origin_id       = "s3-media"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    compress               = var.default_cache_behavior_compress

    min_ttl     = 0
    default_ttl = var.default_cache_behavior_ttl
    max_ttl     = var.default_cache_behavior_max_ttl

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
  }

  # Ordered cache behaviors
  dynamic "ordered_cache_behavior" {
    for_each = var.ordered_cache_behaviors
    content {
      path_pattern           = ordered_cache_behavior.value.path_pattern
      target_origin_id       = ordered_cache_behavior.value.target_origin_id
      viewer_protocol_policy = ordered_cache_behavior.value.viewer_protocol_policy
      allowed_methods        = ordered_cache_behavior.value.allowed_methods
      cached_methods         = ordered_cache_behavior.value.cached_methods
      compress               = ordered_cache_behavior.value.compress

      min_ttl     = 0
      default_ttl = ordered_cache_behavior.value.ttl
      max_ttl     = ordered_cache_behavior.value.max_ttl

      forwarded_values {
        query_string = true
        cookies {
          forward = "all"
        }
      }
    }
  }

  # SSL/TLS
  viewer_certificate {
    cloudfront_default_certificate = var.acm_certificate_arn == "" ? true : false
    acm_certificate_arn            = var.acm_certificate_arn != "" ? var.acm_certificate_arn : null
    ssl_support_method             = var.acm_certificate_arn != "" ? "sni-only" : null
    minimum_protocol_version       = "TLSv1.2_2021"
  }

  # Aliases
  aliases = var.aliases

  # Logging
  dynamic "logging_config" {
    for_each = var.enable_logging && var.logs_bucket_domain_name != "" ? [1] : []
    content {
      include_cookies = false
      bucket          = var.logs_bucket_domain_name
      prefix          = "cdn/"
    }
  }

  # WAF
  web_acl_id = var.create_waf ? (var.waf_web_acl_arn != "" ? var.waf_web_acl_arn : aws_wafv2_web_acl.this[0].arn) : null

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-cloudfront"
  })
}

# -----------------------------------------------------------------------------
# CloudFront Origin Access Identity
# -----------------------------------------------------------------------------

resource "aws_cloudfront_origin_access_identity" "this" {
  comment = "${var.name_prefix} OAI"
}

# -----------------------------------------------------------------------------
# WAF WebACL
# -----------------------------------------------------------------------------

resource "aws_wafv2_web_acl" "this" {
  count = var.create_waf && var.waf_web_acl_arn == "" ? 1 : 0

  name        = "${var.name_prefix}-cloudfront-waf"
  description = "WAF WebACL for CloudFront distribution"
  scope       = "CLOUDFRONT"

  default_action {
    allow {}
  }

  # AWS Managed Rules — Common Rule Set
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesCommonRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  # AWS Managed Rules — Known Bad Inputs
  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesKnownBadInputsRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  # AWS Managed Rules — SQL Injection
  rule {
    name     = "AWSManagedRulesSQLiRuleSet"
    priority = 3

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesSQLiRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.name_prefix}-cloudfront-waf-metric"
    sampled_requests_enabled   = true
  }

  tags = var.tags
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------

output "distribution_id" {
  description = "ID of the CloudFront distribution"
  value       = aws_cloudfront_distribution.this.id
}

output "distribution_arn" {
  description = "ARN of the CloudFront distribution"
  value       = aws_cloudfront_distribution.this.arn
}

output "domain_name" {
  description = "Domain name of the CloudFront distribution"
  value       = aws_cloudfront_distribution.this.domain_name
}

output "hosted_zone_id" {
  description = "Route 53 hosted zone ID for the CloudFront distribution"
  value       = aws_cloudfront_distribution.this.hosted_zone_id
}

output "status" {
  description = "Status of the CloudFront distribution"
  value       = aws_cloudfront_distribution.this.status
}
