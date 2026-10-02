# influencer-marketing.tf
# Influencer Marketing - Influencer campaign management
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
    key            = "influencer-marketing/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "influencer-marketing"
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

variable "platforms" {
  description = "Social media platforms"
  type        = list(string)
}

variable "min_followers" {
  description = "Minimum follower count"
  type        = number
}

variable "engagement_rate_threshold" {
  description = "Minimum engagement rate"
  type        = number
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_dynamodb_table" "influencers" {
  name = "influencers-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "influencer_id"
  attribute = [{"name": "influencer_id", "type": "S"}, {"name": "platform", "type": "S"}, {"name": "tier", "type": "S"}]
}

resource "aws_dynamodb_table" "influencer_campaigns" {
  name = "influencer-campaigns-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "campaign_id"
  attribute = [{"name": "campaign_id", "type": "S"}, {"name": "influencer_id", "type": "S"}]
}

resource "aws_dynamodb_table" "influencer_content" {
  name = "influencer-content-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "content_id"
  attribute = [{"name": "content_id", "type": "S"}, {"name": "campaign_id", "type": "S"}]
}

resource "aws_lambda_function" "influencer_matcher" {
  function_name = "influencer-matcher-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "influencer_matcher.zip"
}

resource "aws_lambda_function" "influencer_analytics" {
  function_name = "influencer-analytics-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "influencer_analytics.zip"
}

resource "aws_s3_bucket" "influencer_assets" {
  bucket = "influencer-assets-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_iam_role" "lambda_role" {
  name = "influencer-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "influencers_table" {
  description = "Influencers table name"
  value       = ${aws_dynamodb_table.influencers.name}
}

output "campaigns_table" {
  description = "Campaigns table name"
  value       = ${aws_dynamodb_table.influencer_campaigns.name}
}
