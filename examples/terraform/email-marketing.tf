# email-marketing.tf
# Email Marketing - Email campaign management and delivery
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
    key            = "email-marketing/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "email-marketing"
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

variable "domain_name" {
  description = "Email domain name"
  type        = string
}

variable "sender_email" {
  description = "Sender email address"
  type        = string
}

variable "max_send_rate" {
  description = "Maximum emails per second"
  type        = number
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_ses_domain_identity" "email_domain" {
  domain = "${var.domain_name}"
}

resource "aws_ses_domain_dkim" "email_dkim" {
  domain = "${aws_ses_domain_identity.email_domain.domain}"
}

resource "aws_ses_configuration_set" "email_config_set" {
  name = "email-marketing-${var.environment}"
}

resource "aws_s3_bucket" "email_templates" {
  bucket = "email-templates-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_dynamodb_table" "email_campaigns" {
  name = "email-campaigns-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "campaign_id"
  attribute = [{"name": "campaign_id", "type": "S"}, {"name": "status", "type": "S"}]
}

resource "aws_lambda_function" "email_sender" {
  function_name = "email-sender-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "email_sender.zip"
}

resource "aws_sns_topic" "email_notifications" {
  name = "email-notifications-${var.environment}"
}

resource "aws_iam_role" "lambda_role" {
  name = "email-sender-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "ses_domain_arn" {
  description = "SES domain ARN"
  value       = ${aws_ses_domain_identity.email_domain.arn}
}

output "configuration_set_name" {
  description = "Configuration set name"
  value       = ${aws_ses_configuration_set.email_config_set.name}
}

output "lambda_function_arn" {
  description = "Lambda function ARN"
  value       = ${aws_lambda_function.email_sender.arn}
}
