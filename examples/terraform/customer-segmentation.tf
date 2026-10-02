# customer-segmentation.tf
# Customer Segmentation - AI-powered customer segmentation
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
    key            = "customer-segmentation/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "customer-segmentation"
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

variable "num_segments" {
  description = "Number of customer segments"
  type        = number
}

variable "segmentation_attributes" {
  description = "Attributes used for segmentation"
  type        = list(string)
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_sagemaker_endpoint" "segmentation_endpoint" {
  name = "segmentation-endpoint"
  endpoint_config_name = "${aws_sagemaker_endpoint_configuration.segmentation_config.name}"
}

resource "aws_sagemaker_endpoint_configuration" "segmentation_config" {
  name = "segmentation-config"
  production_variants = [{"variant_name": "primary", "model_name": "${aws_sagemaker_model.segmentation_model.name}", "initial_instance_count": 1, "instance_type": "ml.m5.large"}]
}

resource "aws_sagemaker_model" "segmentation_model" {
  name = "segmentation-model"
  primary_container = {"image": "${var.sagemaker_image_uri}", "model_data_arn": "${aws_s3_object.segmentation_artifact.arn}"}
  execution_role_arn = "${aws_iam_role.sagemaker_role.arn}"
}

resource "aws_s3_bucket" "segmentation_artifacts" {
  bucket = "segmentation-artifacts-${var.environment}"
}

resource "aws_s3_object" "segmentation_artifact" {
  bucket = "${aws_s3_bucket.segmentation_artifacts.id}"
  key = "model.tar.gz"
  source = "./artifacts/segmentation_model.tar.gz"
}

resource "aws_dynamodb_table" "customer_segments" {
  name = "customer-segments-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "customer_id"
  attribute = [{"name": "customer_id", "type": "S"}, {"name": "segment", "type": "S"}]
}

resource "aws_lambda_function" "segmentation_processor" {
  function_name = "segmentation-processor-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "segmentation_processor.zip"
}

resource "aws_iam_role" "sagemaker_role" {
  name = "segmentation-sagemaker-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "sagemaker.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

resource "aws_iam_role" "lambda_role" {
  name = "segmentation-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "endpoint_name" {
  description = "SageMaker endpoint name"
  value       = ${aws_sagemaker_endpoint.segmentation_endpoint.name}
}

output "segments_table" {
  description = "Customer segments table"
  value       = ${aws_dynamodb_table.customer_segments.name}
}
