# smb-marketing.tf
# SMB Marketing - Small and medium business marketing
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
    key            = "smb-marketing/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "smb-marketing"
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

variable "container_image" {
  description = "Docker image URI"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs"
  type        = list(string)
}

variable "business_segments" {
  description = "SMB business segments"
  type        = list(string)
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_ecs_cluster" "smb_cluster" {
  name = "smb-marketing-${var.environment}"
}

resource "aws_ecs_task_definition" "smb_task" {
  family = "smb-marketing"
  network_mode = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu = "256"
  memory = "512"
  container_definitions = "[{"name": "smb-marketing", "image": "${var.container_image}", "essential": true, "portMappings": [{"containerPort": 8080, "protocol": "tcp"}]}]"
  execution_role_arn = "${aws_iam_role.ecs_execution_role.arn}"
}

resource "aws_ecs_service" "smb_service" {
  name = "smb-marketing"
  cluster = "${aws_ecs_cluster.smb_cluster.id}"
  task_definition = "${aws_ecs_task_definition.smb_task.arn}"
  desired_count = 1
  launch_type = "FARGATE"
  network_configuration = {"subnets": "${var.subnet_ids}", "security_groups": ["${aws_security_group.smb_sg.id}"]}
}

resource "aws_security_group" "smb_sg" {
  name = "smb-marketing-sg"
  ingress = [{"from_port": 8080, "to_port": 8080, "protocol": "tcp", "cidr_blocks": ["0.0.0.0/0"]}]
}

resource "aws_dynamodb_table" "smb_campaigns" {
  name = "smb-campaigns-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "campaign_id"
  attribute = [{"name": "campaign_id", "type": "S"}, {"name": "business_id", "type": "S"}]
}

resource "aws_lambda_function" "smb_optimizer" {
  function_name = "smb-optimizer-${var.environment}"
  runtime = "python3.11"
  handler = "index.handler"
  role = "${aws_iam_role.lambda_role.arn}"
  filename = "smb_optimizer.zip"
}

resource "aws_iam_role" "ecs_execution_role" {
  name = "smb-ecs-execution-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "ecs-tasks.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

resource "aws_iam_role" "lambda_role" {
  name = "smb-lambda-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "cluster_name" {
  description = "ECS cluster name"
  value       = ${aws_ecs_cluster.smb_cluster.name}
}

output "campaigns_table" {
  description = "Campaigns table name"
  value       = ${aws_dynamodb_table.smb_campaigns.name}
}
