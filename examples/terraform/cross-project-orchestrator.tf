# cross-project-orchestrator.tf
# Cross-Project Orchestrator - Orchestrates all 42 marketing projects
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
    key            = "cross-project-orchestrator/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "cross-project-orchestrator"
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

variable "project_count" {
  description = "Number of projects to orchestrate"
  type        = number
}

variable "max_parallel_executions" {
  description = "Maximum parallel project executions"
  type        = number
}

variable "failure_threshold" {
  description = "Failure threshold before alerting"
  type        = number
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_stepfunctions_state_machine" "cross_project_orchestrator" {
  name = "cross-project-orchestrator-${var.environment}"
  role_arn = "${aws_iam_role.step_functions_role.arn}"
  definition = "{"Comment": "Cross-Project Marketing Orchestrator", "StartAt": "DiscoverProjects", "States": {"DiscoverProjects": {"Type": "Task", "Resource": "${aws_lambda_function.discover_projects.arn}", "Next": "ValidateDependencies"}, "ValidateDependencies": {"Type": "Task", "Resource": "${aws_lambda_function.validate_dependencies.arn}", "Next": "OrchestrateProjects"}, "OrchestrateProjects": {"Type": "Map", "ItemsPath": "$.projects", "Iterator": {"StartAt": "ExecuteProject", "States": {"ExecuteProject": {"Type": "Task", "Resource": "${aws_lambda_function.execute_project.arn}", "Next": "CheckProjectResult"}, "CheckProjectResult": {"Type": "Choice", "Choices": [{"Variable": "$.success", "BooleanEquals": true, "Next": "ProjectComplete"}], "Default": "ProjectFailed"}, "ProjectComplete": {"Type": "Succeed"}, "ProjectFailed": {"Type": "Task", "Resource": "${aws_lambda_function.handle_failure.arn}", "Next": "ProjectComplete"}}}, "Next": "AggregateResults"}, "AggregateResults": {"Type": "Task", "Resource": "${aws_lambda_function.aggregate_results.arn}", "Next": "NotifyStakeholders"}, "NotifyStakeholders": {"Type": "Task", "Resource": "${aws_lambda_function.notify_stakeholders.arn}", "Next": "OrchestrationComplete"}, "OrchestrationComplete": {"Type": "Succeed"}}}"
}

resource "aws_lambda_function" "discover_projects" {
  function_name = "discover-projects-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "discover_projects.zip"
}

resource "aws_lambda_function" "validate_dependencies" {
  function_name = "validate-dependencies-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "validate_dependencies.zip"
}

resource "aws_lambda_function" "execute_project" {
  function_name = "execute-project-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "execute_project.zip"
}

resource "aws_lambda_function" "handle_failure" {
  function_name = "handle-failure-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "handle_failure.zip"
}

resource "aws_lambda_function" "aggregate_results" {
  function_name = "aggregate-results-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "aggregate_results.zip"
}

resource "aws_lambda_function" "notify_stakeholders" {
  function_name = "notify-stakeholders-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "notify_stakeholders.zip"
}

resource "aws_dynamodb_table" "orchestration_state" {
  name = "orchestration-state-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "orchestration_id"
  attribute = [{"name": "orchestration_id", "type": "S"}, {"name": "status", "type": "S"}]
}

resource "aws_dynamodb_table" "project_registry" {
  name = "project-registry-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "project_id"
  attribute = [{"name": "project_id", "type": "S"}, {"name": "project_name", "type": "S"}, {"name": "status", "type": "S"}]
}

resource "aws_eventbridge_rule" "orchestration_schedule" {
  name = "orchestration-schedule"
  schedule_expression = "rate(1 hour)"
}

resource "aws_eventbridge_target" "orchestration_target" {
  rule = "${aws_eventbridge_rule.orchestration_schedule.name}"
  arn = "${aws_stepfunctions_state_machine.cross_project_orchestrator.arn}"
}

resource "aws_sns_topic" "orchestration_alerts" {
  name = "orchestration-alerts-${var.environment}"
}

resource "aws_iam_role" "step_functions_role" {
  name = "orchestrator-step-functions-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "states.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

resource "aws_iam_role" "lambda_role" {
  name = "orchestrator-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "state_machine_arn" {
  description = "State machine ARN"
  value       = ${aws_stepfunctions_state_machine.cross_project_orchestrator.arn}
}

output "project_registry_table" {
  description = "Project registry table"
  value       = ${aws_dynamodb_table.project_registry.name}
}

output "orchestration_state_table" {
  description = "Orchestration state table"
  value       = ${aws_dynamodb_table.orchestration_state.name}
}
