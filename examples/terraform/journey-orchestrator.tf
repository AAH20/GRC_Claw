# journey-orchestrator.tf
# Journey Orchestrator - Customer journey mapping and orchestration
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
    key            = "journey-orchestrator/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "journey-orchestrator"
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

variable "journey_timeout_hours" {
  description = "Journey timeout in hours"
  type        = number
}

variable "max_concurrent_journeys" {
  description = "Maximum concurrent journeys"
  type        = number
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_pinpoint_app" "journey_app" {
  name = "journey-orchestrator-${var.environment}"
}

resource "aws_pinpoint_event_stream" "journey_events" {
  application_id = "${aws_pinpoint_app.journey_app.application_id}"
  destination_stream_arn = "${aws_kinesis_stream.journey_stream.arn}"
  role_arn = "${aws_iam_role.pinpoint_role.arn}"
}

resource "aws_kinesis_stream" "journey_stream" {
  name = "journey-events-${var.environment}"
  shard_count = 2
}

resource "aws_dynamodb_table" "journey_states" {
  name = "journey-states-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "customer_id"
  range_key = "journey_id"
  attribute = [{"name": "customer_id", "type": "S"}, {"name": "journey_id", "type": "S"}, {"name": "current_state", "type": "S"}]
}

resource "aws_lambda_function" "journey_orchestrator" {
  function_name = "journey-orchestrator-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "journey_orchestrator.zip"
}

resource "aws_stepfunctions_state_machine" "journey_state_machine" {
  name = "journey-orchestrator-sm-${var.environment}"
  role_arn = "${aws_iam_role.step_functions_role.arn}"
  definition = "{"Comment": "Journey Orchestrator", "StartAt": "EvaluateState", "States": {"EvaluateState": {"Type": "Task", "Resource": "${aws_lambda_function.journey_orchestrator.arn}", "Next": "CheckTransition"}, "CheckTransition": {"Type": "Choice", "Choices": [{"Variable": "$.should_transition", "BooleanEquals": true, "Next": "TransitionState"}], "Default": "WaitState"}, "TransitionState": {"Type": "Task", "Resource": "${aws_lambda_function.journey_orchestrator.arn}", "Next": "EvaluateState"}, "WaitState": {"Type": "Wait", "Seconds": 3600, "Next": "EvaluateState"}}}"
}

resource "aws_iam_role" "pinpoint_role" {
  name = "pinpoint-journey-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "pinpoint.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

resource "aws_iam_role" "lambda_role" {
  name = "journey-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

resource "aws_iam_role" "step_functions_role" {
  name = "journey-step-functions-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "states.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "pinpoint_app_id" {
  description = "Pinpoint application ID"
  value       = ${aws_pinpoint_app.journey_app.application_id}
}

output "state_machine_arn" {
  description = "Step Functions state machine ARN"
  value       = ${aws_stepfunctions_state_machine.journey_state_machine.arn}
}

output "kinesis_stream_arn" {
  description = "Kinesis stream ARN"
  value       = ${aws_kinesis_stream.journey_stream.arn}
}
