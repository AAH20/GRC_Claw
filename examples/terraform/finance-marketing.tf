# finance-marketing.tf
# Finance Marketing - Financial services marketing
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
    key            = "finance-marketing/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "finance-marketing"
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

variable "product_types" {
  description = "Financial product types"
  type        = list(string)
}

variable "regulatory_framework" {
  description = "Regulatory framework (SOX, GDPR, etc.)"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_dynamodb_table" "financial_campaigns" {
  name = "financial-campaigns-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "campaign_id"
  attribute = [{"name": "campaign_id", "type": "S"}, {"name": "product_type", "type": "S"}]
}

resource "aws_dynamodb_table" "financial_leads" {
  name = "financial-leads-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "lead_id"
  attribute = [{"name": "lead_id", "type": "S"}, {"name": "product_interest", "type": "S"}]
}

resource "aws_lambda_function" "compliance_validator" {
  function_name = "compliance-validator-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "compliance_validator.zip"
}

resource "aws_lambda_function" "lead_scorer" {
  function_name = "financial-lead-scorer-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "financial_lead_scorer.zip"
}

resource "aws_s3_bucket" "financial_content" {
  bucket = "financial-content-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_iam_role" "lambda_role" {
  name = "finance-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "campaigns_table" {
  description = "Campaigns table name"
  value       = ${aws_dynamodb_table.financial_campaigns.name}
}

output "leads_table" {
  description = "Leads table name"
  value       = ${aws_dynamodb_table.financial_leads.name}
}
