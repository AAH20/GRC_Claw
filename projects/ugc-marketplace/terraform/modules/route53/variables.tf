variable "name_prefix" {
  type = string
}

variable "domain_name" {
  type = string
}

variable "route53_zone_id" {
  type    = string
  default = null
}

variable "cloudfront_domain_name" {
  type    = string
  default = ""
}

variable "cloudfront_hosted_zone_id" {
  type    = string
  default = ""
}

variable "alb_dns_name" {
  type    = string
  default = null
}

variable "tags" {
  type    = map(string)
  default = {}
}
