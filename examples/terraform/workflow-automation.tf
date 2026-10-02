# workflow-automation.tf
# Workflow Automation - Marketing workflow automation
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
    key            = "workflow-automation/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "workflow-automation"
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

variable "workflow_types" {
  description = "Supported workflow types"
  type        = list(string)
}

variable "max_retries" {
  description = "Maximum retry attempts"
  type        = number
}

variable "timeout_seconds" {
  description = "Workflow timeout in seconds"
  type        = number
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_stepfunctions_state_machine" "marketing_workflow" {
  name = "marketing-workflow-${var.environment}"
  role_arn = "${aws_iam_role.step_functions_role.arn}"
  definition = "{"Comment": "Marketing Workflow Automation", "StartAt": "ValidateInput", "States": {"ValidateInput": {"Type": "Task", "Resource": "${aws_lambda_function.validate_input.arn}", "Next": "ProcessWorkflow"}, "ProcessWorkflow": {"Type": "Map", "ItemsPath": "$.tasks", "Iterator": {"StartAt": "ExecuteTask", "States": {"ExecuteTask": {"Type": "Task", "Resource": "${aws_lambda_function.execute_task.arn}", "Next": "CheckResult"}, "CheckResult": {"Type": "Choice", "Choices": [{"Variable": "$.success", "BooleanEquals": true, "Next": "TaskComplete"}], "Default": "TaskFailed"}, "TaskComplete": {"Type": "Succeed"}, "TaskFailed": {"Type": "Fail", "Error": "TaskExecutionFailed"}}}, "Next": "WorkflowComplete"}, "WorkflowComplete": {"Type": "Succeed"}}}"
}

resource "aws_lambda_function" "validate_input" {
  function_name = "validate-input-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "validate_input.zip"
}

resource "aws_lambda_function" "execute_task" {
  function_name = "execute-task-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "execute_task.zip"
}

resource "aws_dynamodb_table" "workflow_executions" {
  name = "workflow-executions-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "execution_id"
  attribute = [{"name": "execution_id", "type": "S"}, {"name": "status", "type": "S"}]
}

resource "aws_eventbridge_rule" "workflow_trigger" {
  name = "workflow-trigger"
  event_pattern = "{"source": ["marketing.workflow"], "detail-type": ["WorkflowRequest"]}"
}

resource "aws_eventbridge_target" "workflow_target" {
  rule = "${aws_eventbridge_rule.workflow_trigger.name}"
  arn = "${aws_stepfunctions_state_machine.marketing_workflow.arn}"
}

resource "aws_iam_role" "step_functions_role" {
  name = "workflow-step-functions-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "states.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

resource "aws_iam_role" "lambda_role" {
  name = "workflow-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "state_machine_arn" {
  description = "State machine ARN"
  value       = ${aws_stepfunctions_state_machine.marketing_workflow.arn}
}

output "executions_table" {
  description = "Executions table name"
  value       = ${aws_dynamodb_table.workflow_executions.name}
}
