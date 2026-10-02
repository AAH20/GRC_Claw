# lead-scorer.tf
# Lead Scorer - AI-powered lead scoring and qualification
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
    key            = "lead-scorer/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "lead-scorer"
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

variable "scoring_threshold" {
  description = "Minimum score threshold for qualification"
  type        = number
}

variable "model_version" {
  description = "Model version identifier"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_sagemaker_endpoint" "lead_scorer_endpoint" {
  name = "lead-scorer-endpoint"
  endpoint_config_name = "${aws_sagemaker_endpoint_configuration.lead_scorer_config.name}"
}

resource "aws_sagemaker_endpoint_configuration" "lead_scorer_config" {
  name = "lead-scorer-config"
  production_variants = [{"variant_name": "primary", "model_name": "${aws_sagemaker_model.lead_scorer_model.name}", "initial_instance_count": 1, "instance_type": "ml.m5.large"}]
}

resource "aws_sagemaker_model" "lead_scorer_model" {
  name = "lead-scorer-model"
  primary_container = {"image": "${var.sagemaker_image_uri}", "model_data_arn": "${aws_s3_object.lead_scorer_artifact.arn}"}
  execution_role_arn = "${aws_iam_role.sagemaker_role.arn}"
}

resource "aws_s3_bucket" "lead_scorer_artifacts" {
  bucket = "lead-scorer-artifacts-${var.environment}"
}

resource "aws_s3_object" "lead_scorer_artifact" {
  bucket = "${aws_s3_bucket.lead_scorer_artifacts.id}"
  key = "model.tar.gz"
  source = "./artifacts/model.tar.gz"
}

resource "aws_dynamodb_table" "lead_scores" {
  name = "lead-scores-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "lead_id"
  attribute = [{"name": "lead_id", "type": "S"}, {"name": "score", "type": "N"}]
}

resource "aws_lambda_function" "lead_scorer" {
  function_name = "lead-scorer-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "lead_scorer.zip"
}

resource "aws_iam_role" "sagemaker_role" {
  name = "sagemaker-lead-scorer-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "sagemaker.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

resource "aws_iam_role" "lambda_role" {
  name = "lead-scorer-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "endpoint_name" {
  description = "Name of the SageMaker endpoint"
  value       = ${aws_sagemaker_endpoint.lead_scorer_endpoint.name}
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  value       = ${aws_dynamodb_table.lead_scores.name}
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = ${aws_lambda_function.lead_scorer.arn}
}
