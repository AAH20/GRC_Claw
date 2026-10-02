# pricing-optimizer.tf
# Pricing Optimizer - Dynamic pricing optimization
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
    key            = "pricing-optimizer/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "pricing-optimizer"
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

variable "pricing_strategy" {
  description = "Pricing strategy (dynamic, competitive, etc.)"
  type        = string
}

variable "min_margin_percent" {
  description = "Minimum margin percentage"
  type        = number
}

variable "max_discount_percent" {
  description = "Maximum discount percentage"
  type        = number
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_dynamodb_table" "pricing_rules" {
  name = "pricing-rules-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "product_id"
  attribute = [{"name": "product_id", "type": "S"}, {"name": "rule_type", "type": "S"}]
}

resource "aws_dynamodb_table" "price_history" {
  name = "price-history-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "product_id"
  range_key = "timestamp"
  attribute = [{"name": "product_id", "type": "S"}, {"name": "timestamp", "type": "S"}]
}

resource "aws_lambda_function" "pricing_engine" {
  function_name = "pricing-engine-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "pricing_engine.zip"
}

resource "aws_lambda_function" "price_optimizer" {
  function_name = "price-optimizer-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "price_optimizer.zip"
}

resource "aws_api_gateway_rest_api" "pricing_api" {
  name = "pricing-api-${var.environment}"
}

resource "aws_cloudwatch_event_rule" "price_update_schedule" {
  name = "price-update-schedule"
  schedule_expression = "rate(1 hour)"
}

resource "aws_cloudwatch_event_target" "price_update_target" {
  rule = "${aws_cloudwatch_event_rule.price_update_schedule.name}"
  arn = "${aws_lambda_function.price_optimizer.arn}"
}

resource "aws_iam_role" "lambda_role" {
  name = "pricing-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "pricing_rules_table" {
  description = "Pricing rules table"
  value       = ${aws_dynamodb_table.pricing_rules.name}
}

output "api_endpoint" {
  description = "API endpoint"
  value       = ${aws_api_gateway_rest_api.pricing_api.execution_arn}
}
