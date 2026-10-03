# =============================================================================
# S3 Module — Storage Buckets
# =============================================================================

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "create_app_bucket" {
  description = "Whether to create the application data bucket"
  type        = bool
  default     = true
}

variable "app_bucket_name" {
  description = "Name of the application data bucket"
  type        = string
  default     = ""
}

variable "app_bucket_versioning" {
  description = "Whether to enable versioning on the app bucket"
  type        = bool
  default     = true
}

variable "app_bucket_lifecycle_rules" {
  description = "Lifecycle rules for the app bucket"
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
  description = "CORS rules for the app bucket"
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
  description = "Whether to create the media/assets bucket"
  type        = bool
  default     = true
}

variable "media_bucket_name" {
  description = "Name of the media/assets bucket"
  type        = string
  default     = ""
}

variable "media_bucket_versioning" {
  description = "Whether to enable versioning on the media bucket"
  type        = bool
  default     = true
}

variable "media_bucket_cors_rules" {
  description = "CORS rules for the media bucket"
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
  description = "Whether to create the logs bucket"
  type        = bool
  default     = true
}

variable "logs_bucket_name" {
  description = "Name of the logs bucket"
  type        = string
  default     = ""
}

variable "logs_bucket_lifecycle_rules" {
  description = "Lifecycle rules for the logs bucket"
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
  description = "KMS key ID for encryption"
  type        = string
  default     = ""
}

variable "block_public_acls" {
  description = "Whether to block public ACLs"
  type        = bool
  default     = true
}

variable "block_public_policy" {
  description = "Whether to block public policies"
  type        = bool
  default     = true
}

variable "ignore_public_acls" {
  description = "Whether to ignore public ACLs"
  type        = bool
  default     = true
}

variable "restrict_public_buckets" {
  description = "Whether to restrict public bucket access"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# -----------------------------------------------------------------------------
# Application Data Bucket
# -----------------------------------------------------------------------------

resource "aws_s3_bucket" "app" {
  count = var.create_app_bucket ? 1 : 0

  bucket = var.app_bucket_name

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-app-data"
  })
}

resource "aws_s3_bucket_versioning" "app" {
  count = var.create_app_bucket ? 1 : 0

  bucket = aws_s3_bucket.app[0].id

  versioning_configuration {
    status = var.app_bucket_versioning ? "Enabled" : "Disabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "app" {
  count = var.create_app_bucket ? 1 : 0

  bucket = aws_s3_bucket.app[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = var.kms_key_id != "" ? var.kms_key_id : null
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "app" {
  count = var.create_app_bucket ? 1 : 0

  bucket = aws_s3_bucket.app[0].id

  block_public_acls       = var.block_public_acls
  block_public_policy     = var.block_public_policy
  ignore_public_acls      = var.ignore_public_acls
  restrict_public_buckets = var.restrict_public_buckets
}

resource "aws_s3_bucket_lifecycle_configuration" "app" {
  count = var.create_app_bucket && length(var.app_bucket_lifecycle_rules) > 0 ? 1 : 0

  bucket = aws_s3_bucket.app[0].id

  dynamic "rule" {
    for_each = var.app_bucket_lifecycle_rules
    content {
      id     = rule.value.id
      status = rule.value.enabled ? "Enabled" : "Disabled"

      filter {
        prefix = rule.value.prefix
      }

      dynamic "transition" {
        for_each = rule.value.transitions
        content {
          days          = transition.value.days
          storage_class = transition.value.storage_class
        }
      }

      expiration {
        days = rule.value.expiration.days
      }
    }
  }
}

resource "aws_s3_bucket_cors_configuration" "app" {
  count = var.create_app_bucket && length(var.app_bucket_cors_rules) > 0 ? 1 : 0

  bucket = aws_s3_bucket.app[0].id

  dynamic "cors_rule" {
    for_each = var.app_bucket_cors_rules
    content {
      allowed_headers = cors_rule.value.allowed_headers
      allowed_methods = cors_rule.value.allowed_methods
      allowed_origins = cors_rule.value.allowed_origins
      expose_headers  = cors_rule.value.expose_headers
      max_age_seconds = cors_rule.value.max_age_seconds
    }
  }
}

# -----------------------------------------------------------------------------
# Media/Assets Bucket
# -----------------------------------------------------------------------------

resource "aws_s3_bucket" "media" {
  count = var.create_media_bucket ? 1 : 0

  bucket = var.media_bucket_name

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-media"
  })
}

resource "aws_s3_bucket_versioning" "media" {
  count = var.create_media_bucket ? 1 : 0

  bucket = aws_s3_bucket.media[0].id

  versioning_configuration {
    status = var.media_bucket_versioning ? "Enabled" : "Disabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "media" {
  count = var.create_media_bucket ? 1 : 0

  bucket = aws_s3_bucket.media[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = var.kms_key_id != "" ? var.kms_key_id : null
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "media" {
  count = var.create_media_bucket ? 1 : 0

  bucket = aws_s3_bucket.media[0].id

  block_public_acls       = var.block_public_acls
  block_public_policy     = var.block_public_policy
  ignore_public_acls      = var.ignore_public_acls
  restrict_public_buckets = var.restrict_public_buckets
}

resource "aws_s3_bucket_cors_configuration" "media" {
  count = var.create_media_bucket && length(var.media_bucket_cors_rules) > 0 ? 1 : 0

  bucket = aws_s3_bucket.media[0].id

  dynamic "cors_rule" {
    for_each = var.media_bucket_cors_rules
    content {
      allowed_headers = cors_rule.value.allowed_headers
      allowed_methods = cors_rule.value.allowed_methods
      allowed_origins = cors_rule.value.allowed_origins
      expose_headers  = cors_rule.value.expose_headers
      max_age_seconds = cors_rule.value.max_age_seconds
    }
  }
}

# -----------------------------------------------------------------------------
# Logs Bucket
# -----------------------------------------------------------------------------

resource "aws_s3_bucket" "logs" {
  count = var.create_logs_bucket ? 1 : 0

  bucket = var.logs_bucket_name

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-logs"
  })
}

resource "aws_s3_bucket_server_side_encryption_configuration" "logs" {
  count = var.create_logs_bucket ? 1 : 0

  bucket = aws_s3_bucket.logs[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "logs" {
  count = var.create_logs_bucket ? 1 : 0

  bucket = aws_s3_bucket.logs[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "logs" {
  count = var.create_logs_bucket && length(var.logs_bucket_lifecycle_rules) > 0 ? 1 : 0

  bucket = aws_s3_bucket.logs[0].id

  dynamic "rule" {
    for_each = var.logs_bucket_lifecycle_rules
    content {
      id     = rule.value.id
      status = rule.value.enabled ? "Enabled" : "Disabled"

      filter {
        prefix = rule.value.prefix
      }

      dynamic "transition" {
        for_each = rule.value.transitions
        content {
          days          = transition.value.days
          storage_class = transition.value.storage_class
        }
      }

      expiration {
        days = rule.value.expiration.days
      }
    }
  }
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------

output "app_bucket_id" {
  description = "ID of the application data bucket"
  value       = var.create_app_bucket ? aws_s3_bucket.app[0].id : null
}

output "app_bucket_arn" {
  description = "ARN of the application data bucket"
  value       = var.create_app_bucket ? aws_s3_bucket.app[0].arn : null
}

output "app_bucket_domain_name" {
  description = "Domain name of the application data bucket"
  value       = var.create_app_bucket ? aws_s3_bucket.app[0].bucket_domain_name : null
}

output "media_bucket_id" {
  description = "ID of the media bucket"
  value       = var.create_media_bucket ? aws_s3_bucket.media[0].id : null
}

output "media_bucket_arn" {
  description = "ARN of the media bucket"
  value       = var.create_media_bucket ? aws_s3_bucket.media[0].arn : null
}

output "media_bucket_domain_name" {
  description = "Domain name of the media bucket"
  value       = var.create_media_bucket ? aws_s3_bucket.media[0].bucket_domain_name : null
}

output "logs_bucket_id" {
  description = "ID of the logs bucket"
  value       = var.create_logs_bucket ? aws_s3_bucket.logs[0].id : null
}

output "logs_bucket_arn" {
  description = "ARN of the logs bucket"
  value       = var.create_logs_bucket ? aws_s3_bucket.logs[0].arn : null
}

output "logs_bucket_domain_name" {
  description = "Domain name of the logs bucket"
  value       = var.create_logs_bucket ? aws_s3_bucket.logs[0].bucket_domain_name : null
}
