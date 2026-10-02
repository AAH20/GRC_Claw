# sales-forecaster.tf
# Sales Forecaster - AI-powered sales forecasting
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
    key            = "sales-forecaster/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "sales-forecaster"
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

variable "forecast_horizon" {
  description = "Forecast horizon in days"
  type        = number
}

variable "forecast_frequency" {
  description = "Forecast frequency (daily, weekly)"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_forecast_dataset_group" "sales_forecast" {
  name = "sales-forecast-${var.environment}"
  domain = "RETAIL"
}

resource "aws_forecast_dataset" "sales_data" {
  name = "sales-data-${var.environment}"
  dataset_group_arn = "${aws_forecast_dataset_group.sales_forecast.arn}"
  dataset_type = "TARGET_TIME_SERIES"
  schema = "{"Attributes": [{"AttributeName": "item_id", "AttributeType": "string"}, {"AttributeName": "timestamp", "AttributeType": "timestamp"}, {"AttributeName": "demand", "AttributeType": "float"}]}"
}

resource "aws_forecast_predictor" "sales_predictor" {
  name = "sales-predictor-${var.environment}"
  forecast_horizon = 30
  dataset_group_arn = "${aws_forecast_dataset_group.sales_forecast.arn}"
}

resource "aws_forecast_forecast" "sales_forecast_output" {
  name = "sales-forecast-output-${var.environment}"
  predictor_arn = "${aws_forecast_predictor.sales_predictor.arn}"
}

resource "aws_s3_bucket" "forecast_data" {
  bucket = "forecast-data-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_lambda_function" "forecast_processor" {
  function_name = "forecast-processor-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "forecast_processor.zip"
}

resource "aws_iam_role" "lambda_role" {
  name = "forecast-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "dataset_group_arn" {
  description = "Forecast dataset group ARN"
  value       = ${aws_forecast_dataset_group.sales_forecast.arn}
}

output "predictor_arn" {
  description = "Predictor ARN"
  value       = ${aws_forecast_predictor.sales_predictor.arn}
}
