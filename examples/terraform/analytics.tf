# analytics.tf
# Analytics - Marketing analytics and reporting
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
    key            = "analytics/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "analytics"
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

variable "data_retention_days" {
  description = "Data retention period in days"
  type        = number
}

variable "report_schedule" {
  description = "Report generation schedule"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_quicksight_account_subscription" "analytics_subscription" {
  account_name = "marketing-analytics-${var.environment}"
  authentication_method = "IAM_AND_QUICKSIGHT"
  edition = "ENTERPRISE"
}

resource "aws_athena_workgroup" "analytics_workgroup" {
  name = "marketing-analytics-${var.environment}"
  configuration = {"result_configuration": {"output_location": "s3://${aws_s3_bucket.analytics_results.id}/athena/"}}
}

resource "aws_s3_bucket" "analytics_results" {
  bucket = "analytics-results-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_glue_catalog_database" "analytics_db" {
  name = "marketing_analytics_${var.environment}"
}

resource "aws_glue_crawler" "analytics_crawler" {
  name = "marketing-analytics-crawler"
  database_name = "${aws_glue_catalog_database.analytics_db.name}"
  role = "${aws_iam_role.glue_role.arn}"
  s3_targets = [{"path": "s3://${aws_s3_bucket.analytics_results.id}/data/"}]
}

resource "aws_lambda_function" "analytics_processor" {
  function_name = "analytics-processor-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "analytics_processor.zip"
}

resource "aws_cloudwatch_event_rule" "analytics_schedule" {
  name = "analytics-processing-schedule"
  schedule_expression = "rate(6 hours)"
}

resource "aws_cloudwatch_event_target" "analytics_target" {
  rule = "${aws_cloudwatch_event_rule.analytics_schedule.name}"
  arn = "${aws_lambda_function.analytics_processor.arn}"
}

resource "aws_iam_role" "glue_role" {
  name = "analytics-glue-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "glue.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

resource "aws_iam_role" "lambda_role" {
  name = "analytics-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "athena_workgroup" {
  description = "Athena workgroup name"
  value       = ${aws_athena_workgroup.analytics_workgroup.name}
}

output "glue_database" {
  description = "Glue database name"
  value       = ${aws_glue_catalog_database.analytics_db.name}
}

output "results_bucket" {
  description = "Results bucket name"
  value       = ${aws_s3_bucket.analytics_results.id}
}
