# marketing-personalization.tf
# Marketing Personalization - Real-time personalization engine
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
    key            = "marketing-personalization/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "marketing-personalization"
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

variable "cache_ttl_seconds" {
  description = "Cache TTL in seconds"
  type        = number
}

variable "personalization_rules" {
  description = "Personalization rules"
  type        = map(string)
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_elasticache_replication_group" "personalization_cache" {
  replication_group_id = "personalization-${var.environment}"
  description = "Personalization cache"
  node_type = "cache.r6g.large"
  num_cache_clusters = 2
  automatic_failover_enabled = true
  engine = "redis"
}

resource "aws_dynamodb_table" "personalization_profiles" {
  name = "personalization-profiles-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "user_id"
  attribute = [{"name": "user_id", "type": "S"}, {"name": "segment", "type": "S"}]
}

resource "aws_lambda_function" "personalization_engine" {
  function_name = "personalization-engine-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "personalization_engine.zip"
}

resource "aws_api_gateway_rest_api" "personalization_api" {
  name = "personalization-api-${var.environment}"
}

resource "aws_api_gateway_resource" "personalization_resource" {
  rest_api_id = "${aws_api_gateway_rest_api.personalization_api.id}"
  parent_id = "${aws_api_gateway_rest_api.personalization_api.root_resource_id}"
  path_part = "personalize"
}

resource "aws_api_gateway_method" "personalization_method" {
  rest_api_id = "${aws_api_gateway_rest_api.personalization_api.id}"
  resource_id = "${aws_api_gateway_resource.personalization_resource.id}"
  http_method = "POST"
  authorization = "AWS_IAM"
}

resource "aws_api_gateway_integration" "personalization_integration" {
  rest_api_id = "${aws_api_gateway_rest_api.personalization_api.id}"
  resource_id = "${aws_api_gateway_resource.personalization_resource.id}"
  http_method = "${aws_api_gateway_method.personalization_method.http_method}"
  integration_http_method = "POST"
  type = "AWS_PROXY"
  uri = "${aws_lambda_function.personalization_engine.invoke_arn}"
}

resource "aws_iam_role" "lambda_role" {
  name = "personalization-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "cache_endpoint" {
  description = "Cache endpoint"
  value       = ${aws_elasticache_replication_group.personalization_cache.primary_endpoint_address}
}

output "api_endpoint" {
  description = "API endpoint"
  value       = ${aws_api_gateway_rest_api.personalization_api.execution_arn}
}
