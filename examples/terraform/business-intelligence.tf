# business-intelligence.tf
# Business Intelligence - Marketing BI and insights
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
    key            = "business-intelligence/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "business-intelligence"
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

variable "data_sources" {
  description = "Data source connections"
  type        = list(string)
}

variable "refresh_schedule" {
  description = "Data refresh schedule"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_quicksight_account_subscription" "bi_subscription" {
  account_name = "marketing-bi-${var.environment}"
  authentication_method = "IAM_AND_QUICKSIGHT"
  edition = "ENTERPRISE"
}

resource "aws_athena_workgroup" "bi_workgroup" {
  name = "marketing-bi-${var.environment}"
  configuration = {"result_configuration": {"output_location": "s3://${aws_s3_bucket.bi_results.id}/athena/"}}
}

resource "aws_s3_bucket" "bi_results" {
  bucket = "bi-results-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_glue_catalog_database" "bi_database" {
  name = "marketing_bi_${var.environment}"
}

resource "aws_glue_crawler" "bi_crawler" {
  name = "marketing-bi-crawler"
  database_name = "${aws_glue_catalog_database.bi_database.name}"
  role = "${aws_iam_role.glue_role.arn}"
  s3_targets = [{"path": "s3://${aws_s3_bucket.bi_results.id}/data/"}]
}

resource "aws_lambda_function" "bi_processor" {
  function_name = "bi-processor-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "bi_processor.zip"
}

resource "aws_dynamodb_table" "bi_metrics" {
  name = "bi-metrics-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "metric_id"
  attribute = [{"name": "metric_id", "type": "S"}, {"name": "metric_type", "type": "S"}]
}

resource "aws_iam_role" "glue_role" {
  name = "bi-glue-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "glue.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

resource "aws_iam_role" "lambda_role" {
  name = "bi-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "athena_workgroup" {
  description = "Athena workgroup"
  value       = ${aws_athena_workgroup.bi_workgroup.name}
}

output "glue_database" {
  description = "Glue database"
  value       = ${aws_glue_catalog_database.bi_database.name}
}

output "metrics_table" {
  description = "Metrics table"
  value       = ${aws_dynamodb_table.bi_metrics.name}
}
