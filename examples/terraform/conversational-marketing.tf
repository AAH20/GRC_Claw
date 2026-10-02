# conversational-marketing.tf
# Conversational Marketing - Chatbot and conversational AI
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
    key            = "conversational-marketing/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "conversational-marketing"
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

variable "bot_locale" {
  description = "Bot locale (en-US, etc.)"
  type        = string
}

variable "conversation_timeout" {
  description = "Conversation timeout in seconds"
  type        = number
}

variable "lead_qualification_rules" {
  description = "Lead qualification rules"
  type        = map(string)
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_lex_bot" "conversational_bot" {
  name = "conversational-marketing-${var.environment}"
  child_directed = false
  idle_session_ttl_in_seconds = 300
  voice_id = "Joanna"
}

resource "aws_lambda_function" "lead_handler" {
  function_name = "lead-handler-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "lead_handler.zip"
}

resource "aws_lambda_function" "conversation_handler" {
  function_name = "conversation-handler-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "conversation_handler.zip"
}

resource "aws_dynamodb_table" "conversations" {
  name = "conversations-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "conversation_id"
  attribute = [{"name": "conversation_id", "type": "S"}, {"name": "status", "type": "S"}]
}

resource "aws_dynamodb_table" "chat_leads" {
  name = "chat-leads-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "lead_id"
  attribute = [{"name": "lead_id", "type": "S"}, {"name": "score", "type": "N"}]
}

resource "aws_iam_role" "lambda_role" {
  name = "conversational-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "bot_name" {
  description = "Lex bot name"
  value       = ${aws_lex_bot.conversational_bot.name}
}

output "conversations_table" {
  description = "Conversations table"
  value       = ${aws_dynamodb_table.conversations.name}
}
