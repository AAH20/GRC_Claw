# content-generator.tf
# Content Generator - AI-powered content generation
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
    key            = "content-generator/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "content-generator"
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

variable "content_types" {
  description = "Supported content types"
  type        = list(string)
}

variable "max_content_length" {
  description = "Maximum content length"
  type        = number
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_s3_bucket" "content_bucket" {
  bucket = "content-generator-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_versioning" "content_versioning" {
  bucket = "${aws_s3_bucket.content_bucket.id}"
  versioning_configuration = {"status": "Enabled"}
}

resource "aws_dynamodb_table" "content_metadata" {
  name = "content-metadata-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "content_id"
  attribute = [{"name": "content_id", "type": "S"}, {"name": "content_type", "type": "S"}]
}

resource "aws_lambda_function" "content_generator" {
  function_name = "content-generator-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "content_generator.zip"
}

resource "aws_api_gateway_rest_api" "content_api" {
  name = "content-generator-api-${var.environment}"
}

resource "aws_api_gateway_resource" "content_resource" {
  rest_api_id = "${aws_api_gateway_rest_api.content_api.id}"
  parent_id = "${aws_api_gateway_rest_api.content_api.root_resource_id}"
  path_part = "generate"
}

resource "aws_api_gateway_method" "content_method" {
  rest_api_id = "${aws_api_gateway_rest_api.content_api.id}"
  resource_id = "${aws_api_gateway_resource.content_resource.id}"
  http_method = "POST"
  authorization = "AWS_IAM"
}

resource "aws_api_gateway_integration" "content_integration" {
  rest_api_id = "${aws_api_gateway_rest_api.content_api.id}"
  resource_id = "${aws_api_gateway_resource.content_resource.id}"
  http_method = "${aws_api_gateway_method.content_method.http_method}"
  integration_http_method = "POST"
  type = "AWS_PROXY"
  uri = "${aws_lambda_function.content_generator.invoke_arn}"
}

resource "aws_iam_role" "lambda_role" {
  name = "content-generator-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "api_endpoint" {
  description = "API Gateway endpoint"
  value       = ${aws_api_gateway_rest_api.content_api.execution_arn}
}

output "bucket_name" {
  description = "S3 bucket name"
  value       = ${aws_s3_bucket.content_bucket.id}
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = ${aws_lambda_function.content_generator.function_name}
}
