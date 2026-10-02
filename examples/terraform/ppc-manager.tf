# ppc-manager.tf
# PPC Manager - Pay-per-click advertising management
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
    key            = "ppc-manager/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "ppc-manager"
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

variable "platforms" {
  description = "PPC platforms (google, bing, etc.)"
  type        = list(string)
}

variable "daily_budget" {
  description = "Daily budget across all campaigns"
  type        = number
}

variable "target_cpa" {
  description = "Target cost per acquisition"
  type        = number
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_dynamodb_table" "ppc_campaigns" {
  name = "ppc-campaigns-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "campaign_id"
  attribute = [{"name": "campaign_id", "type": "S"}, {"name": "platform", "type": "S"}, {"name": "status", "type": "S"}]
}

resource "aws_dynamodb_table" "ppc_keywords" {
  name = "ppc-keywords-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "keyword_id"
  attribute = [{"name": "keyword_id", "type": "S"}, {"name": "campaign_id", "type": "S"}]
}

resource "aws_lambda_function" "ppc_optimizer" {
  function_name = "ppc-optimizer-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "ppc_optimizer.zip"
}

resource "aws_cloudwatch_event_rule" "ppc_sync" {
  name = "ppc-data-sync"
  schedule_expression = "rate(15 minutes)"
}

resource "aws_cloudwatch_event_target" "ppc_sync_target" {
  rule = "${aws_cloudwatch_event_rule.ppc_sync.name}"
  arn = "${aws_lambda_function.ppc_optimizer.arn}"
}

resource "aws_s3_bucket" "ppc_reports" {
  bucket = "ppc-reports-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_iam_role" "lambda_role" {
  name = "ppc-optimizer-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "campaigns_table" {
  description = "Campaigns table name"
  value       = ${aws_dynamodb_table.ppc_campaigns.name}
}

output "keywords_table" {
  description = "Keywords table name"
  value       = ${aws_dynamodb_table.ppc_keywords.name}
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = ${aws_lambda_function.ppc_optimizer.function_name}
}
