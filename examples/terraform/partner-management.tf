# partner-management.tf
# Partner Management - Partner relationship management
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
    key            = "partner-management/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "partner-management"
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

variable "partner_tiers" {
  description = "Partner tier definitions"
  type        = list(string)
}

variable "deal_stages" {
  description = "Deal pipeline stages"
  type        = list(string)
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_dynamodb_table" "partners" {
  name = "partners-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "partner_id"
  attribute = [{"name": "partner_id", "type": "S"}, {"name": "tier", "type": "S"}, {"name": "status", "type": "S"}]
}

resource "aws_dynamodb_table" "partner_deals" {
  name = "partner-deals-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "deal_id"
  attribute = [{"name": "deal_id", "type": "S"}, {"name": "partner_id", "type": "S"}]
}

resource "aws_dynamodb_table" "partner_activities" {
  name = "partner-activities-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "activity_id"
  attribute = [{"name": "activity_id", "type": "S"}, {"name": "partner_id", "type": "S"}]
}

resource "aws_lambda_function" "partner_portal" {
  function_name = "partner-portal-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "partner_portal.zip"
}

resource "aws_lambda_function" "deal_tracker" {
  function_name = "deal-tracker-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "deal_tracker.zip"
}

resource "aws_s3_bucket" "partner_assets" {
  bucket = "partner-assets-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_iam_role" "lambda_role" {
  name = "partner-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "partners_table" {
  description = "Partners table name"
  value       = ${aws_dynamodb_table.partners.name}
}

output "deals_table" {
  description = "Deals table name"
  value       = ${aws_dynamodb_table.partner_deals.name}
}
