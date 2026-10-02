# customer-service.tf
# Customer Service - AI-powered customer support
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
    key            = "customer-service/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "customer-service"
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

variable "support_email" {
  description = "Support email address"
  type        = string
}

variable "business_hours" {
  description = "Business hours timezone"
  type        = string
}

variable "max_queue_size" {
  description = "Maximum queue size"
  type        = number
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_connect_instance" "customer_service" {
  instance_alias = "customer-service-${var.environment}"
  identity_management_type = "CONNECT_MANAGED"
  inbound_calls_enabled = true
  outbound_calls_enabled = true
}

resource "aws_connect_queue" "support_queue" {
  instance_id = "${aws_connect_instance.customer_service.id}"
  name = "Support Queue"
  description = "Main support queue"
}

resource "aws_lambda_function" "intent_classifier" {
  function_name = "intent-classifier-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "intent_classifier.zip"
}

resource "aws_dynamodb_table" "support_tickets" {
  name = "support-tickets-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "ticket_id"
  attribute = [{"name": "ticket_id", "type": "S"}, {"name": "status", "type": "S"}]
}

resource "aws_iam_role" "lambda_role" {
  name = "customer-service-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "connect_instance_id" {
  description = "Connect instance ID"
  value       = ${aws_connect_instance.customer_service.id}
}

output "queue_id" {
  description = "Support queue ID"
  value       = ${aws_connect_queue.support_queue.id}
}

output "tickets_table" {
  description = "Tickets table name"
  value       = ${aws_dynamodb_table.support_tickets.name}
}
