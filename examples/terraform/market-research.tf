# market-research.tf
# Market Research - Market analysis and research
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
    key            = "market-research/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "market-research"
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

variable "research_types" {
  description = "Types of research"
  type        = list(string)
}

variable "survey_platforms" {
  description = "Survey platform integrations"
  type        = list(string)
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_s3_bucket" "research_data" {
  bucket = "research-data-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_dynamodb_table" "research_projects" {
  name = "research-projects-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "project_id"
  attribute = [{"name": "project_id", "type": "S"}, {"name": "status", "type": "S"}]
}

resource "aws_dynamodb_table" "research_surveys" {
  name = "research-surveys-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "survey_id"
  attribute = [{"name": "survey_id", "type": "S"}, {"name": "project_id", "type": "S"}]
}

resource "aws_lambda_function" "research_analyzer" {
  function_name = "research-analyzer-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "research_analyzer.zip"
}

resource "aws_lambda_function" "survey_processor" {
  function_name = "survey-processor-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "survey_processor.zip"
}

resource "aws_glue_catalog_database" "research_db" {
  name = "market_research_${var.environment}"
}

resource "aws_iam_role" "lambda_role" {
  name = "research-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "projects_table" {
  description = "Research projects table"
  value       = ${aws_dynamodb_table.research_projects.name}
}

output "data_bucket" {
  description = "Research data bucket"
  value       = ${aws_s3_bucket.research_data.id}
}
