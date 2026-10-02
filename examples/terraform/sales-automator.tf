# sales-automator.tf
# Sales Automator - Sales process automation
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
    key            = "sales-automator/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "sales-automator"
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

variable "qualification_criteria" {
  description = "Lead qualification criteria"
  type        = map(string)
}

variable "pipeline_stages" {
  description = "Sales pipeline stages"
  type        = list(string)
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_stepfunctions_state_machine" "sales_automation" {
  name = "sales-automator-${var.environment}"
  role_arn = "${aws_iam_role.step_functions_role.arn}"
  definition = "{"Comment": "Sales Automation Workflow", "StartAt": "QualifyLead", "States": {"QualifyLead": {"Type": "Task", "Resource": "${aws_lambda_function.qualify_lead.arn}", "Next": "CheckQualified"}, "CheckQualified": {"Type": "Choice", "Choices": [{"Variable": "$.qualified", "BooleanEquals": true, "Next": "CreateOpportunity"}], "Default": "NurtureLead"}, "CreateOpportunity": {"Type": "Task", "Resource": "${aws_lambda_function.create_opportunity.arn}", "Next": "SendWelcome"}, "SendWelcome": {"Type": "Task", "Resource": "${aws_lambda_function.send_welcome.arn}", "Next": "Done"}, "NurtureLead": {"Type": "Task", "Resource": "${aws_lambda_function.nurture_lead.arn}", "Next": "Done"}, "Done": {"Type": "Succeed"}}}"
}

resource "aws_lambda_function" "qualify_lead" {
  function_name = "qualify-lead-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "qualify_lead.zip"
}

resource "aws_lambda_function" "create_opportunity" {
  function_name = "create-opportunity-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "create_opportunity.zip"
}

resource "aws_lambda_function" "send_welcome" {
  function_name = "send-welcome-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "send_welcome.zip"
}

resource "aws_lambda_function" "nurture_lead" {
  function_name = "nurture-lead-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "nurture_lead.zip"
}

resource "aws_dynamodb_table" "sales_pipeline" {
  name = "sales-pipeline-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "opportunity_id"
  attribute = [{"name": "opportunity_id", "type": "S"}, {"name": "stage", "type": "S"}]
}

resource "aws_iam_role" "step_functions_role" {
  name = "sales-automator-step-functions-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "states.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

resource "aws_iam_role" "lambda_role" {
  name = "sales-automator-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "state_machine_arn" {
  description = "State machine ARN"
  value       = ${aws_stepfunctions_state_machine.sales_automation.arn}
}

output "pipeline_table" {
  description = "Pipeline table name"
  value       = ${aws_dynamodb_table.sales_pipeline.name}
}
