# agency-marketing.tf
# Agency Marketing - Marketing agency management
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
    key            = "agency-marketing/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "agency-marketing"
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

variable "service_types" {
  description = "Agency service types"
  type        = list(string)
}

variable "billing_frequency" {
  description = "Billing frequency (monthly, quarterly)"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_dynamodb_table" "agency_clients" {
  name = "agency-clients-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "client_id"
  attribute = [{"name": "client_id", "type": "S"}, {"name": "status", "type": "S"}]
}

resource "aws_dynamodb_table" "agency_campaigns" {
  name = "agency-campaigns-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "campaign_id"
  attribute = [{"name": "campaign_id", "type": "S"}, {"name": "client_id", "type": "S"}]
}

resource "aws_dynamodb_table" "agency_invoices" {
  name = "agency-invoices-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "invoice_id"
  attribute = [{"name": "invoice_id", "type": "S"}, {"name": "client_id", "type": "S"}]
}

resource "aws_lambda_function" "agency_manager" {
  function_name = "agency-manager-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "agency_manager.zip"
}

resource "aws_lambda_function" "billing_processor" {
  function_name = "billing-processor-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "billing_processor.zip"
}

resource "aws_s3_bucket" "agency_assets" {
  bucket = "agency-assets-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_iam_role" "lambda_role" {
  name = "agency-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "clients_table" {
  description = "Clients table name"
  value       = ${aws_dynamodb_table.agency_clients.name}
}

output "campaigns_table" {
  description = "Campaigns table name"
  value       = ${aws_dynamodb_table.agency_campaigns.name}
}
