# saas-marketing.tf
# SaaS Marketing - SaaS product marketing
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
    key            = "saas-marketing/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "saas-marketing"
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

variable "pricing_plans" {
  description = "Available pricing plans"
  type        = list(string)
}

variable "trial_duration_days" {
  description = "Trial duration in days"
  type        = number
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_dynamodb_table" "saas_trials" {
  name = "saas-trials-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "trial_id"
  attribute = [{"name": "trial_id", "type": "S"}, {"name": "status", "type": "S"}]
}

resource "aws_dynamodb_table" "saas_subscriptions" {
  name = "saas-subscriptions-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "subscription_id"
  attribute = [{"name": "subscription_id", "type": "S"}, {"name": "plan", "type": "S"}]
}

resource "aws_lambda_function" "trial_converter" {
  function_name = "trial-converter-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "trial_converter.zip"
}

resource "aws_lambda_function" "churn_predictor" {
  function_name = "churn-predictor-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "churn_predictor.zip"
}

resource "aws_s3_bucket" "saas_content" {
  bucket = "saas-content-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_iam_role" "lambda_role" {
  name = "saas-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "trials_table" {
  description = "Trials table name"
  value       = ${aws_dynamodb_table.saas_trials.name}
}

output "subscriptions_table" {
  description = "Subscriptions table name"
  value       = ${aws_dynamodb_table.saas_subscriptions.name}
}
