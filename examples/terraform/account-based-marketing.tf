# account-based-marketing.tf
# Account-Based Marketing - ABM campaign management
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
    key            = "account-based-marketing/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "account-based-marketing"
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

variable "account_tiers" {
  description = "Account tier definitions"
  type        = list(string)
}

variable "target_industries" {
  description = "Target industries"
  type        = list(string)
}

variable "engagement_threshold" {
  description = "Engagement threshold for intent"
  type        = number
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_dynamodb_table" "abm_accounts" {
  name = "abm-accounts-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "account_id"
  attribute = [{"name": "account_id", "type": "S"}, {"name": "tier", "type": "S"}]
}

resource "aws_dynamodb_table" "abm_contacts" {
  name = "abm-contacts-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "contact_id"
  attribute = [{"name": "contact_id", "type": "S"}, {"name": "account_id", "type": "S"}]
}

resource "aws_dynamodb_table" "abm_campaigns" {
  name = "abm-campaigns-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "campaign_id"
  attribute = [{"name": "campaign_id", "type": "S"}, {"name": "account_id", "type": "S"}]
}

resource "aws_lambda_function" "abm_orchestrator" {
  function_name = "abm-orchestrator-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "abm_orchestrator.zip"
}

resource "aws_lambda_function" "abm_personalizer" {
  function_name = "abm-personalizer-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "abm_personalizer.zip"
}

resource "aws_eventbridge_rule" "abm_schedule" {
  name = "abm-campaign-schedule"
  schedule_expression = "rate(1 day)"
}

resource "aws_eventbridge_target" "abm_target" {
  rule = "${aws_eventbridge_rule.abm_schedule.name}"
  arn = "${aws_lambda_function.abm_orchestrator.arn}"
}

resource "aws_iam_role" "lambda_role" {
  name = "abm-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "accounts_table" {
  description = "Accounts table name"
  value       = ${aws_dynamodb_table.abm_accounts.name}
}

output "campaigns_table" {
  description = "Campaigns table name"
  value       = ${aws_dynamodb_table.abm_campaigns.name}
}
