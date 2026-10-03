variable "name_prefix" {
  type = string
}

variable "create_app_bucket" {
  type    = bool
  default = true
}

variable "app_bucket_name" {
  type    = string
  default = ""
}

variable "app_bucket_versioning" {
  type    = bool
  default = true
}

variable "app_bucket_lifecycle_rules" {
  type = list(object({
    id      = string
    enabled = bool
    prefix  = string
    transitions = list(object({
      days          = number
      storage_class = string
    }))
    expiration = object({
      days = number
    })
  }))
  default = []
}

variable "app_bucket_cors_rules" {
  type = list(object({
    allowed_headers = list(string)
    allowed_methods = list(string)
    allowed_origins = list(string)
    expose_headers  = list(string)
    max_age_seconds = number
  }))
  default = []
}

variable "create_media_bucket" {
  type    = bool
  default = true
}

variable "media_bucket_name" {
  type    = string
  default = ""
}

variable "media_bucket_versioning" {
  type    = bool
  default = true
}

variable "media_bucket_cors_rules" {
  type = list(object({
    allowed_headers = list(string)
    allowed_methods = list(string)
    allowed_origins = list(string)
    expose_headers  = list(string)
    max_age_seconds = number
  }))
  default = []
}

variable "create_logs_bucket" {
  type    = bool
  default = true
}

variable "logs_bucket_name" {
  type    = string
  default = ""
}

variable "logs_bucket_lifecycle_rules" {
  type = list(object({
    id      = string
    enabled = bool
    prefix  = string
    transitions = list(object({
      days          = number
      storage_class = string
    }))
    expiration = object({
      days = number
    })
  }))
  default = []
}

variable "kms_key_id" {
  type    = string
  default = ""
}

variable "block_public_acls" {
  type    = bool
  default = true
}

variable "block_public_policy" {
  type    = bool
  default = true
}

variable "ignore_public_acls" {
  type    = bool
  default = true
}

variable "restrict_public_buckets" {
  type    = bool
  default = true
}

variable "tags" {
  type    = map(string)
  default = {}
}
