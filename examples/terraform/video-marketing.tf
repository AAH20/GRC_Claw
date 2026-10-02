# video-marketing.tf
# Video Marketing - Video content management and distribution
# Generated for production use

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "terraform-state-${var.environment}"
    key            = "video-marketing/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "video-marketing"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Variables
variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "video_formats" {
  description = "Output video formats"
  type        = list(string)
}

variable "max_video_size_mb" {
  description = "Maximum video size in MB"
  type        = number
}

variable "thumbnail_interval_seconds" {
  description = "Thumbnail generation interval"
  type        = number
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_media_convert_queue" "video_queue" {
  name = "video-marketing-${var.environment}"
  status = "ACTIVE"
}

resource "aws_s3_bucket" "video_source" {
  bucket = "video-source-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket" "video_output" {
  bucket = "video-output-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_dynamodb_table" "video_assets" {
  name = "video-assets-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "video_id"
  attribute = [{"name": "video_id", "type": "S"}, {"name": "status", "type": "S"}]
}

resource "aws_lambda_function" "video_processor" {
  function_name = "video-processor-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "video_processor.zip"
}

resource "aws_lambda_function" "thumbnail_generator" {
  function_name = "thumbnail-generator-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "thumbnail_generator.zip"
}

resource "aws_cloudfront_distribution" "video_cdn" {
  enabled = true
  default_cache_behavior = {"target_origin_id": "video-origin", "viewer_protocol_policy": "redirect-to-https", "allowed_methods": ["GET", "HEAD"], "cached_methods": ["GET", "HEAD"], "forwarded_values": {"query_string": false, "cookies": {"forward": "none"}}}
  origins = [{"domain_name": "${aws_s3_bucket.video_output.bucket_regional_domain_name}", "origin_id": "video-origin", "s3_origin_config": {"origin_access_identity": "${aws_cloudfront_origin_access_identity.video_oai.cloudfront_access_identity_path}"}}]
  restrictions = {"geo_restriction": {"restriction_type": "none"}}
  viewer_certificate = {"cloudfront_default_certificate": true}
}

resource "aws_cloudfront_origin_access_identity" "video_oai" {
  comment = "Video CDN OAI"
}

resource "aws_iam_role" "lambda_role" {
  name = "video-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "queue_name" {
  description = "MediaConvert queue name"
  value       = ${aws_media_convert_queue.video_queue.name}
}

output "cdn_domain" {
  description = "Video CDN domain"
  value       = ${aws_cloudfront_distribution.video_cdn.domain_name}
}
