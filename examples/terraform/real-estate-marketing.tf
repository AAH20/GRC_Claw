# real-estate-marketing.tf
# Real Estate Marketing - Property marketing automation
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
    key            = "real-estate-marketing/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "real-estate-marketing"
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

variable "property_types" {
  description = "Property types (residential, commercial)"
  type        = list(string)
}

variable "mls_integration" {
  description = "Enable MLS integration"
  type        = bool
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_dynamodb_table" "properties" {
  name = "properties-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "property_id"
  attribute = [{"name": "property_id", "type": "S"}, {"name": "status", "type": "S"}, {"name": "property_type", "type": "S"}]
}

resource "aws_dynamodb_table" "property_leads" {
  name = "property-leads-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "lead_id"
  attribute = [{"name": "lead_id", "type": "S"}, {"name": "property_id", "type": "S"}]
}

resource "aws_lambda_function" "property_recommender" {
  function_name = "property-recommender-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "property_recommender.zip"
}

resource "aws_lambda_function" "tour_scheduler" {
  function_name = "tour-scheduler-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "tour_scheduler.zip"
}

resource "aws_s3_bucket" "property_photos" {
  bucket = "property-photos-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_iam_role" "lambda_role" {
  name = "real-estate-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "properties_table" {
  description = "Properties table name"
  value       = ${aws_dynamodb_table.properties.name}
}

output "leads_table" {
  description = "Leads table name"
  value       = ${aws_dynamodb_table.property_leads.name}
}
