# customer-retention.tf
# Customer Retention - Churn prediction and retention campaigns
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
    key            = "customer-retention/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "customer-retention"
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

variable "sagemaker_image_uri" {
  description = "SageMaker Docker image URI"
  type        = string
}

variable "churn_threshold" {
  description = "Churn risk threshold"
  type        = number
}

variable "retention_offers" {
  description = "Available retention offers"
  type        = list(string)
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_sagemaker_endpoint" "churn_endpoint" {
  name = "churn-predictor-endpoint"
  endpoint_config_name = "${aws_sagemaker_endpoint_configuration.churn_config.name}"
}

resource "aws_sagemaker_endpoint_configuration" "churn_config" {
  name = "churn-predictor-config"
  production_variants = [{"variant_name": "primary", "model_name": "${aws_sagemaker_model.churn_model.name}", "initial_instance_count": 1, "instance_type": "ml.m5.large"}]
}

resource "aws_sagemaker_model" "churn_model" {
  name = "churn-predictor-model"
  primary_container = {"image": "${var.sagemaker_image_uri}", "model_data_arn": "${aws_s3_object.churn_artifact.arn}"}
  execution_role_arn = "${aws_iam_role.sagemaker_role.arn}"
}

resource "aws_s3_bucket" "churn_artifacts" {
  bucket = "churn-artifacts-${var.environment}"
}

resource "aws_s3_object" "churn_artifact" {
  bucket = "${aws_s3_bucket.churn_artifacts.id}"
  key = "model.tar.gz"
  source = "./artifacts/churn_model.tar.gz"
}

resource "aws_dynamodb_table" "retention_campaigns" {
  name = "retention-campaigns-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "customer_id"
  attribute = [{"name": "customer_id", "type": "S"}, {"name": "risk_level", "type": "S"}]
}

resource "aws_lambda_function" "retention_processor" {
  function_name = "retention-processor-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "retention_processor.zip"
}

resource "aws_iam_role" "sagemaker_role" {
  name = "churn-sagemaker-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "sagemaker.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

resource "aws_iam_role" "lambda_role" {
  name = "retention-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "endpoint_name" {
  description = "SageMaker endpoint name"
  value       = ${aws_sagemaker_endpoint.churn_endpoint.name}
}

output "campaigns_table" {
  description = "Retention campaigns table"
  value       = ${aws_dynamodb_table.retention_campaigns.name}
}
