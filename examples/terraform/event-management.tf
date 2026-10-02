# event-management.tf
# Event Management - Marketing event planning and management
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
    key            = "event-management/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "event-management"
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

variable "event_types" {
  description = "Supported event types"
  type        = list(string)
}

variable "max_attendees" {
  description = "Maximum attendees per event"
  type        = number
}

variable "notification_email" {
  description = "Event notification email"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_dynamodb_table" "events" {
  name = "events-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "event_id"
  attribute = [{"name": "event_id", "type": "S"}, {"name": "event_type", "type": "S"}, {"name": "status", "type": "S"}]
}

resource "aws_dynamodb_table" "event_attendees" {
  name = "event-attendees-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "attendee_id"
  attribute = [{"name": "attendee_id", "type": "S"}, {"name": "event_id", "type": "S"}]
}

resource "aws_dynamodb_table" "event_sessions" {
  name = "event-sessions-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "session_id"
  attribute = [{"name": "session_id", "type": "S"}, {"name": "event_id", "type": "S"}]
}

resource "aws_lambda_function" "event_manager" {
  function_name = "event-manager-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "event_manager.zip"
}

resource "aws_lambda_function" "event_notifier" {
  function_name = "event-notifier-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "event_notifier.zip"
}

resource "aws_sns_topic" "event_alerts" {
  name = "event-alerts-${var.environment}"
}

resource "aws_iam_role" "lambda_role" {
  name = "event-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "events_table" {
  description = "Events table name"
  value       = ${aws_dynamodb_table.events.name}
}

output "attendees_table" {
  description = "Attendees table name"
  value       = ${aws_dynamodb_table.event_attendees.name}
}
