# affiliate-marketing.tf
# Affiliate Marketing - Affiliate program management
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
    key            = "affiliate-marketing/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "affiliate-marketing"
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

variable "commission_rate" {
  description = "Commission rate percentage"
  type        = number
}

variable "cookie_duration_days" {
  description = "Cookie duration in days"
  type        = number
}

variable "payout_threshold" {
  description = "Minimum payout threshold"
  type        = number
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_dynamodb_table" "affiliates" {
  name = "affiliates-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "affiliate_id"
  attribute = [{"name": "affiliate_id", "type": "S"}, {"name": "status", "type": "S"}]
}

resource "aws_dynamodb_table" "affiliate_links" {
  name = "affiliate-links-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "link_id"
  attribute = [{"name": "link_id", "type": "S"}, {"name": "affiliate_id", "type": "S"}]
}

resource "aws_dynamodb_table" "affiliate_commissions" {
  name = "affiliate-commissions-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "commission_id"
  attribute = [{"name": "commission_id", "type": "S"}, {"name": "affiliate_id", "type": "S"}]
}

resource "aws_lambda_function" "affiliate_tracker" {
  function_name = "affiliate-tracker-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "affiliate_tracker.zip"
}

resource "aws_lambda_function" "commission_calculator" {
  function_name = "commission-calculator-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "commission_calculator.zip"
}

resource "aws_api_gateway_rest_api" "affiliate_api" {
  name = "affiliate-api-${var.environment}"
}

resource "aws_iam_role" "lambda_role" {
  name = "affiliate-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "affiliates_table" {
  description = "Affiliates table name"
  value       = ${aws_dynamodb_table.affiliates.name}
}

output "api_endpoint" {
  description = "API endpoint"
  value       = ${aws_api_gateway_rest_api.affiliate_api.execution_arn}
}
