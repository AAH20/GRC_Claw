# product-recommendations.tf
# Product Recommendations - AI-powered product recommendation engine
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
    key            = "product-recommendations/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "product-recommendations"
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

variable "recommendation_strategy" {
  description = "Recommendation strategy"
  type        = string
}

variable "max_recommendations" {
  description = "Maximum recommendations per request"
  type        = number
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_personalize_dataset_group" "product_recommendations" {
  name = "product-recommendations-dataset-group"
}

resource "aws_personalize_schema" "interactions_schema" {
  name = "interactions-schema"
  schema = "{"type": "record", "name": "Interactions", "namespace": "com.amazonaws.personalize.schema", "fields": [{"name": "USER_ID", "type": "string"}, {"name": "ITEM_ID", "type": "string"}, {"name": "TIMESTAMP", "type": "long"}, {"name": "EVENT_TYPE", "type": "string"}, {"name": "EVENT_VALUE", "type": "float", "optional": true}], "version": "1.0"}"
}

resource "aws_personalize_dataset" "interactions_dataset" {
  dataset_group_arn = "${aws_personalize_dataset_group.product_recommendations.arn}"
  dataset_type = "INTERACTIONS"
  schema_arn = "${aws_personalize_schema.interactions_schema.arn}"
}

resource "aws_personalize_solution" "recommendation_solution" {
  dataset_group_arn = "${aws_personalize_dataset_group.product_recommendations.arn}"
  name = "product-recommendations-solution"
}

resource "aws_personalize_solution_version" "recommendation_solution_version" {
  solution_arn = "${aws_personalize_solution.recommendation_solution.arn}"
}

resource "aws_personalize_campaign" "recommendation_campaign" {
  solution_version_arn = "${aws_personalize_solution_version.recommendation_solution_version.arn}"
  name = "product-recommendations-campaign"
}

resource "aws_lambda_function" "recommendation_api" {
  function_name = "recommendation-api-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "recommendation_api.zip"
}

resource "aws_api_gateway_rest_api" "recommendation_api_gw" {
  name = "recommendation-api-${var.environment}"
}

resource "aws_iam_role" "lambda_role" {
  name = "recommendation-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "campaign_arn" {
  description = "Personalize campaign ARN"
  value       = ${aws_personalize_campaign.recommendation_campaign.arn}
}

output "api_endpoint" {
  description = "API endpoint"
  value       = ${aws_api_gateway_rest_api.recommendation_api_gw.execution_arn}
}
