# marketing-attribution.tf
# Marketing Attribution - Multi-touch attribution modeling
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
    key            = "marketing-attribution/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "marketing-attribution"
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

variable "attribution_model" {
  description = "Attribution model type (first-touch, last-touch, linear)"
  type        = string
}

variable "lookback_window_days" {
  description = "Lookback window in days"
  type        = number
}

variable "conversion_events" {
  description = "Conversion event types"
  type        = list(string)
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_kinesis_stream" "attribution_events" {
  name = "attribution-events-${var.environment}"
  shard_count = 4
}

resource "aws_kinesis_firehose_delivery_stream" "attribution_firehose" {
  name = "attribution-firehose-${var.environment}"
  destination = "s3"
  s3_configuration = {"role_arn": "${aws_iam_role.firehose_role.arn}", "bucket_arn": "${aws_s3_bucket.attribution_data.arn}", "prefix": "raw/"}
}

resource "aws_s3_bucket" "attribution_data" {
  bucket = "attribution-data-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_dynamodb_table" "attribution_models" {
  name = "attribution-models-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "model_id"
  attribute = [{"name": "model_id", "type": "S"}, {"name": "model_type", "type": "S"}]
}

resource "aws_lambda_function" "attribution_processor" {
  function_name = "attribution-processor-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "attribution_processor.zip"
}

resource "aws_lambda_function" "attribution_model" {
  function_name = "attribution-model-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "attribution_model.zip"
}

resource "aws_iam_role" "firehose_role" {
  name = "attribution-firehose-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "firehose.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

resource "aws_iam_role" "lambda_role" {
  name = "attribution-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "kinesis_stream_arn" {
  description = "Kinesis stream ARN"
  value       = ${aws_kinesis_stream.attribution_events.arn}
}

output "models_table" {
  description = "Attribution models table"
  value       = ${aws_dynamodb_table.attribution_models.name}
}
