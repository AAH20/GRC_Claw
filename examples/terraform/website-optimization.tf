# website-optimization.tf
# Website Optimization - Website performance and conversion optimization
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
    key            = "website-optimization/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "website-optimization"
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

variable "website_domain" {
  description = "Website domain name"
  type        = string
}

variable "test_types" {
  description = "Types of optimization tests"
  type        = list(string)
}

variable "performance_threshold_ms" {
  description = "Performance threshold in milliseconds"
  type        = number
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_cloudfront_distribution" "website_cdn" {
  enabled = true
  default_cache_behavior = {"target_origin_id": "website-origin", "viewer_protocol_policy": "redirect-to-https", "allowed_methods": ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"], "cached_methods": ["GET", "HEAD"], "forwarded_values": {"query_string": true, "cookies": {"forward": "all"}}}
  origins = [{"domain_name": "${var.website_domain}", "origin_id": "website-origin", "custom_origin_config": {"http_port": 80, "https_port": 443, "origin_protocol_policy": "https-only"}}]
  restrictions = {"geo_restriction": {"restriction_type": "none"}}
  viewer_certificate = {"cloudfront_default_certificate": true}
}

resource "aws_s3_bucket" "website_assets" {
  bucket = "website-assets-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_dynamodb_table" "optimization_tests" {
  name = "optimization-tests-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "test_id"
  attribute = [{"name": "test_id", "type": "S"}, {"name": "test_type", "type": "S"}]
}

resource "aws_lambda_function" "ab_test_manager" {
  function_name = "ab-test-manager-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "ab_test_manager.zip"
}

resource "aws_lambda_function" "performance_monitor" {
  function_name = "performance-monitor-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "performance_monitor.zip"
}

resource "aws_iam_role" "lambda_role" {
  name = "website-optimization-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "cdn_domain" {
  description = "CloudFront domain name"
  value       = ${aws_cloudfront_distribution.website_cdn.domain_name}
}

output "tests_table" {
  description = "Optimization tests table"
  value       = ${aws_dynamodb_table.optimization_tests.name}
}
