variable "name_prefix" {
  type = string
}

variable "s3_media_bucket_domain_name" {
  type    = string
  default = ""
}

variable "s3_app_bucket_domain_name" {
  type    = string
  default = ""
}

variable "create_alb_origin" {
  type    = bool
  default = true
}

variable "alb_dns_name" {
  type    = string
  default = null
}

variable "default_cache_behavior_ttl" {
  type    = number
  default = 86400
}

variable "default_cache_behavior_max_ttl" {
  type    = number
  default = 31536000
}

variable "default_cache_behavior_compress" {
  type    = bool
  default = true
}

variable "ordered_cache_behaviors" {
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
  type    = string
  default = ""
}

variable "aliases" {
  type    = list(string)
  default = []
}

variable "enable_logging" {
  type    = bool
  default = true
}

variable "logs_bucket_domain_name" {
  type    = string
  default = ""
}

variable "create_waf" {
  type    = bool
  default = true
}

variable "waf_web_acl_arn" {
  type    = string
  default = ""
}

variable "tags" {
  type    = map(string)
  default = {}
}
