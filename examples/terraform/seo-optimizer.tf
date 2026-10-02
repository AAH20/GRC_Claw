# seo-optimizer.tf
# SEO Optimizer - Search engine optimization management
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
    key            = "seo-optimizer/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "seo-optimizer"
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

variable "target_domains" {
  description = "Domains to optimize"
  type        = list(string)
}

variable "crawl_depth" {
  description = "Maximum crawl depth"
  type        = number
}

variable "audit_frequency" {
  description = "Audit frequency (daily, weekly)"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_s3_bucket" "seo_reports" {
  bucket = "seo-reports-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_dynamodb_table" "seo_keywords" {
  name = "seo-keywords-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "keyword"
  attribute = [{"name": "keyword", "type": "S"}, {"name": "url", "type": "S"}]
}

resource "aws_dynamodb_table" "seo_audit" {
  name = "seo-audit-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "audit_id"
  attribute = [{"name": "audit_id", "type": "S"}, {"name": "url", "type": "S"}]
}

resource "aws_lambda_function" "seo_crawler" {
  function_name = "seo-crawler-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "seo_crawler.zip"
}

resource "aws_lambda_function" "seo_analyzer" {
  function_name = "seo-analyzer-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "seo_analyzer.zip"
}

resource "aws_cloudwatch_event_rule" "seo_audit_schedule" {
  name = "seo-audit-schedule"
  schedule_expression = "rate(1 day)"
}

resource "aws_cloudwatch_event_target" "seo_audit_target" {
  rule = "${aws_cloudwatch_event_rule.seo_audit_schedule.name}"
  arn = "${aws_lambda_function.seo_crawler.arn}"
}

resource "aws_iam_role" "lambda_role" {
  name = "seo-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "keywords_table" {
  description = "Keywords table name"
  value       = ${aws_dynamodb_table.seo_keywords.name}
}

output "audit_table" {
  description = "Audit table name"
  value       = ${aws_dynamodb_table.seo_audit.name}
}

output "reports_bucket" {
  description = "Reports bucket name"
  value       = ${aws_s3_bucket.seo_reports.id}
}
