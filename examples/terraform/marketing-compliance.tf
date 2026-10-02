# marketing-compliance.tf
# Marketing Compliance - Compliance monitoring and enforcement
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
    key            = "marketing-compliance/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "marketing-compliance"
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

variable "compliance_frameworks" {
  description = "Compliance frameworks (GDPR, CCPA, etc.)"
  type        = list(string)
}

variable "data_retention_days" {
  description = "Data retention period"
  type        = number
}

variable "alert_email" {
  description = "Compliance alert email"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_config_configuration_recorder" "compliance_recorder" {
  name = "marketing-compliance-recorder"
  role_arn = "${aws_iam_role.config_role.arn}"
  recording_group = {"all_supported": true, "include_global_resource_types": true}
}

resource "aws_config_delivery_channel" "compliance_delivery" {
  name = "marketing-compliance-delivery"
  s3_bucket_name = "${aws_s3_bucket.compliance_reports.id}"
  sns_topic_arn = "${aws_sns_topic.compliance_alerts.arn}"
}

resource "aws_config_config_rule" "gdpr_compliance" {
  name = "gdpr-compliance-rule"
  source = {"owner": "AWS", "source_identifier": "REQUIRED_TAGS"}
  input_parameters = "{"tag1Key": "data_classification", "tag2Key": "retention_policy"}"
}

resource "aws_s3_bucket" "compliance_reports" {
  bucket = "compliance-reports-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_sns_topic" "compliance_alerts" {
  name = "compliance-alerts-${var.environment}"
}

resource "aws_lambda_function" "compliance_checker" {
  function_name = "compliance-checker-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "compliance_checker.zip"
}

resource "aws_iam_role" "config_role" {
  name = "compliance-config-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "config.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

resource "aws_iam_role" "lambda_role" {
  name = "compliance-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "config_recorder_name" {
  description = "Config recorder name"
  value       = ${aws_config_configuration_recorder.compliance_recorder.name}
}

output "compliance_reports_bucket" {
  description = "Compliance reports bucket"
  value       = ${aws_s3_bucket.compliance_reports.id}
}
