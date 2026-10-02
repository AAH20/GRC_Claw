# healthcare-marketing.tf
# Healthcare Marketing - Healthcare marketing compliance
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
    key            = "healthcare-marketing/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "healthcare-marketing"
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

variable "compliance_framework" {
  description = "Compliance framework (HIPAA, etc.)"
  type        = string
}

variable "content_approval_required" {
  description = "Require content approval"
  type        = bool
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_dynamodb_table" "healthcare_campaigns" {
  name = "healthcare-campaigns-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "campaign_id"
  attribute = [{"name": "campaign_id", "type": "S"}, {"name": "status", "type": "S"}]
}

resource "aws_dynamodb_table" "patient_segments" {
  name = "patient-segments-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "segment_id"
  attribute = [{"name": "segment_id", "type": "S"}, {"name": "condition", "type": "S"}]
}

resource "aws_lambda_function" "hipaa_compliance_checker" {
  function_name = "hipaa-compliance-checker-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "hipaa_compliance_checker.zip"
}

resource "aws_lambda_function" "healthcare_personalizer" {
  function_name = "healthcare-personalizer-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "healthcare_personalizer.zip"
}

resource "aws_s3_bucket" "healthcare_content" {
  bucket = "healthcare-content-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_iam_role" "lambda_role" {
  name = "healthcare-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "campaigns_table" {
  description = "Campaigns table name"
  value       = ${aws_dynamodb_table.healthcare_campaigns.name}
}

output "segments_table" {
  description = "Patient segments table"
  value       = ${aws_dynamodb_table.patient_segments.name}
}
