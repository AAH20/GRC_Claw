# ecommerce-marketing.tf
# E-commerce Marketing - E-commerce marketing automation
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
    key            = "ecommerce-marketing/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "ecommerce-marketing"
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

variable "store_url" {
  description = "E-commerce store URL"
  type        = string
}

variable "abandoned_cart_timeout" {
  description = "Abandoned cart timeout in minutes"
  type        = number
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_personalize_dataset_group" "ecommerce_recommendations" {
  name = "ecommerce-recommendations-dataset-group"
}

resource "aws_personalize_schema" "ecommerce_schema" {
  name = "ecommerce-interactions-schema"
  schema = "{"type": "record", "name": "Interactions", "namespace": "com.amazonaws.personalize.schema", "fields": [{"name": "USER_ID", "type": "string"}, {"name": "ITEM_ID", "type": "string"}, {"name": "TIMESTAMP", "type": "long"}, {"name": "EVENT_TYPE", "type": "string"}, {"name": "EVENT_VALUE", "type": "float", "optional": true}], "version": "1.0"}"
}

resource "aws_personalize_dataset" "ecommerce_interactions" {
  dataset_group_arn = "${aws_personalize_dataset_group.ecommerce_recommendations.arn}"
  dataset_type = "INTERACTIONS"
  schema_arn = "${aws_personalize_schema.ecommerce_schema.arn}"
}

resource "aws_personalize_solution" "ecommerce_solution" {
  dataset_group_arn = "${aws_personalize_dataset_group.ecommerce_recommendations.arn}"
  name = "ecommerce-recommendations-solution"
}

resource "aws_personalize_solution_version" "ecommerce_solution_version" {
  solution_arn = "${aws_personalize_solution.ecommerce_solution.arn}"
}

resource "aws_personalize_campaign" "ecommerce_campaign" {
  solution_version_arn = "${aws_personalize_solution_version.ecommerce_solution_version.arn}"
  name = "ecommerce-recommendations-campaign"
}

resource "aws_dynamodb_table" "ecommerce_products" {
  name = "ecommerce-products-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "product_id"
  attribute = [{"name": "product_id", "type": "S"}, {"name": "category", "type": "S"}]
}

resource "aws_lambda_function" "cart_abandoner" {
  function_name = "cart-abandoner-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "cart_abandoner.zip"
}

resource "aws_iam_role" "lambda_role" {
  name = "ecommerce-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "campaign_arn" {
  description = "Personalize campaign ARN"
  value       = ${aws_personalize_campaign.ecommerce_campaign.arn}
}

output "products_table" {
  description = "Products table name"
  value       = ${aws_dynamodb_table.ecommerce_products.name}
}
