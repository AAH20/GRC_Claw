# feedback-management.tf
# Feedback Management - Customer feedback collection and analysis
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
    key            = "feedback-management/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "feedback-management"
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

variable "feedback_channels" {
  description = "Feedback collection channels"
  type        = list(string)
}

variable "sentiment_threshold" {
  description = "Sentiment analysis threshold"
  type        = number
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_kinesis_stream" "feedback_stream" {
  name = "feedback-stream-${var.environment}"
  shard_count = 2
}

resource "aws_kinesis_firehose_delivery_stream" "feedback_firehose" {
  name = "feedback-firehose-${var.environment}"
  destination = "s3"
  s3_configuration = {"role_arn": "${aws_iam_role.firehose_role.arn}", "bucket_arn": "${aws_s3_bucket.feedback_data.arn}", "prefix": "raw/"}
}

resource "aws_s3_bucket" "feedback_data" {
  bucket = "feedback-data-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_dynamodb_table" "feedback_items" {
  name = "feedback-items-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "feedback_id"
  attribute = [{"name": "feedback_id", "type": "S"}, {"name": "sentiment", "type": "S"}]
}

resource "aws_lambda_function" "feedback_analyzer" {
  function_name = "feedback-analyzer-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "feedback_analyzer.zip"
}

resource "aws_lambda_function" "sentiment_processor" {
  function_name = "sentiment-processor-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "sentiment_processor.zip"
}

resource "aws_iam_role" "firehose_role" {
  name = "feedback-firehose-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "firehose.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

resource "aws_iam_role" "lambda_role" {
  name = "feedback-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "stream_arn" {
  description = "Kinesis stream ARN"
  value       = ${aws_kinesis_stream.feedback_stream.arn}
}

output "feedback_table" {
  description = "Feedback items table"
  value       = ${aws_dynamodb_table.feedback_items.name}
}
