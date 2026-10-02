# brand-monitoring.tf
# Brand Monitoring - Brand mention tracking and analysis
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
    key            = "brand-monitoring/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "brand-monitoring"
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

variable "brand_keywords" {
  description = "Brand keywords to monitor"
  type        = list(string)
}

variable "platforms" {
  description = "Platforms to monitor"
  type        = list(string)
}

variable "alert_threshold" {
  description = "Alert threshold for negative sentiment"
  type        = number
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_kinesis_stream" "brand_mentions" {
  name = "brand-mentions-${var.environment}"
  shard_count = 2
}

resource "aws_kinesis_firehose_delivery_stream" "brand_firehose" {
  name = "brand-firehose-${var.environment}"
  destination = "s3"
  s3_configuration = {"role_arn": "${aws_iam_role.firehose_role.arn}", "bucket_arn": "${aws_s3_bucket.brand_data.arn}", "prefix": "raw/"}
}

resource "aws_s3_bucket" "brand_data" {
  bucket = "brand-data-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_dynamodb_table" "brand_mentions_table" {
  name = "brand-mentions-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "mention_id"
  attribute = [{"name": "mention_id", "type": "S"}, {"name": "platform", "type": "S"}, {"name": "sentiment", "type": "S"}]
}

resource "aws_lambda_function" "brand_analyzer" {
  function_name = "brand-analyzer-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "brand_analyzer.zip"
}

resource "aws_lambda_function" "sentiment_tracker" {
  function_name = "sentiment-tracker-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "sentiment_tracker.zip"
}

resource "aws_cloudwatch_event_rule" "brand_alert_schedule" {
  name = "brand-alert-schedule"
  schedule_expression = "rate(15 minutes)"
}

resource "aws_cloudwatch_event_target" "brand_alert_target" {
  rule = "${aws_cloudwatch_event_rule.brand_alert_schedule.name}"
  arn = "${aws_lambda_function.brand_analyzer.arn}"
}

resource "aws_iam_role" "firehose_role" {
  name = "brand-firehose-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "firehose.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

resource "aws_iam_role" "lambda_role" {
  name = "brand-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "stream_arn" {
  description = "Kinesis stream ARN"
  value       = ${aws_kinesis_stream.brand_mentions.arn}
}

output "mentions_table" {
  description = "Brand mentions table"
  value       = ${aws_dynamodb_table.brand_mentions_table.name}
}
