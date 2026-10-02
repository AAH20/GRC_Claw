# crm-enhancer.tf
# CRM Enhancer - CRM data enrichment and enhancement
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
    key            = "crm-enhancer/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "crm-enhancer"
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

variable "crm_provider" {
  description = "CRM provider (salesforce, hubspot, etc.)"
  type        = string
}

variable "enrichment_sources" {
  description = "Data enrichment sources"
  type        = list(string)
}

variable "sync_frequency" {
  description = "Sync frequency"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_dynamodb_table" "crm_contacts" {
  name = "crm-contacts-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "contact_id"
  attribute = [{"name": "contact_id", "type": "S"}, {"name": "email", "type": "S"}, {"name": "enriched", "type": "S"}]
}

resource "aws_dynamodb_table" "crm_companies" {
  name = "crm-companies-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "company_id"
  attribute = [{"name": "company_id", "type": "S"}, {"name": "domain", "type": "S"}]
}

resource "aws_lambda_function" "crm_enricher" {
  function_name = "crm-enricher-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "crm_enricher.zip"
}

resource "aws_lambda_function" "crm_sync" {
  function_name = "crm-sync-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "crm_sync.zip"
}

resource "aws_eventbridge_rule" "crm_sync_schedule" {
  name = "crm-sync-schedule"
  schedule_expression = "rate(1 hour)"
}

resource "aws_eventbridge_target" "crm_sync_target" {
  rule = "${aws_eventbridge_rule.crm_sync_schedule.name}"
  arn = "${aws_lambda_function.crm_sync.arn}"
}

resource "aws_sqs_queue" "crm_enrichment_queue" {
  name = "crm-enrichment-queue-${var.environment}"
  visibility_timeout_seconds = 300
}

resource "aws_iam_role" "lambda_role" {
  name = "crm-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "contacts_table" {
  description = "Contacts table name"
  value       = ${aws_dynamodb_table.crm_contacts.name}
}

output "companies_table" {
  description = "Companies table name"
  value       = ${aws_dynamodb_table.crm_companies.name}
}

output "enrichment_queue_url" {
  description = "Enrichment queue URL"
  value       = ${aws_sqs_queue.crm_enrichment_queue.url}
}
