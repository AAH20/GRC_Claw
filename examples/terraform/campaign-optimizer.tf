# campaign-optimizer.tf
# Campaign Optimizer - AI-driven marketing campaign optimization
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
    key            = "campaign-optimizer/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "campaign-optimizer"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Variables
variable "campaign_name" {
  description = "Name of the marketing campaign"
  type        = string
}

variable "optimization_strategy" {
  description = "Optimization strategy (e.g., ROAS, CPA, CTR)"
  type        = string
}

variable "budget" {
  description = "Campaign budget in USD"
  type        = number
}

variable "target_audience" {
  description = "Target audience segment"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
}

# Resources
resource "aws_personalize_dataset_group" "campaign_dataset_group" {
  name = "campaign-optimizer-dataset-group"
}

resource "aws_personalize_schema" "campaign_schema" {
  name = "campaign-interactions-schema"
  schema = "{"type": "record", "name": "Interactions", "namespace": "com.amazonaws.personalize.schema", "fields": [{"name": "USER_ID", "type": "string"}, {"name": "ITEM_ID", "type": "string"}, {"name": "TIMESTAMP", "type": "long"}, {"name": "EVENT_TYPE", "type": "string"}], "version": "1.0"}"
}

resource "aws_personalize_dataset" "campaign_dataset" {
  dataset_group_arn = "${aws_personalize_dataset_group.campaign_dataset_group.arn}"
  dataset_type = "INTERACTIONS"
  schema_arn = "${aws_personalize_schema.campaign_schema.arn}"
}

resource "aws_personalize_solution" "campaign_solution" {
  dataset_group_arn = "${aws_personalize_dataset_group.campaign_dataset_group.arn}"
  name = "campaign-optimizer-solution"
}

resource "aws_personalize_solution_version" "campaign_solution_version" {
  solution_arn = "${aws_personalize_solution.campaign_solution.arn}"
}

resource "aws_personalize_campaign" "campaign_campaign" {
  solution_version_arn = "${aws_personalize_solution_version.campaign_solution_version.arn}"
  name = "campaign-optimizer-campaign"
}

resource "aws_lambda_function" "campaign_optimizer" {
  function_name = "campaign-optimizer"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.campaign_optimizer_role.arn}"
  filename = "campaign_optimizer.zip"
}

resource "aws_iam_role" "campaign_optimizer_role" {
  name = "campaign-optimizer-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

resource "aws_cloudwatch_event_rule" "campaign_schedule" {
  name = "campaign-optimizer-schedule"
  schedule_expression = "rate(1 hour)"
}

resource "aws_cloudwatch_event_target" "campaign_target" {
  rule = "${aws_cloudwatch_event_rule.campaign_schedule.name}"
  arn = "${aws_lambda_function.campaign_optimizer.arn}"
}

# Outputs
output "campaign_arn" {
  description = "ARN of the Personalize campaign"
  value       = ${aws_personalize_campaign.campaign_campaign.arn}
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = ${aws_lambda_function.campaign_optimizer.function_name}
}

output "dataset_group_arn" {
  description = "ARN of the dataset group"
  value       = ${aws_personalize_dataset_group.campaign_dataset_group.arn}
}
