# social-media-manager.tf
# Social Media Manager - Multi-platform social media management
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
    key            = "social-media-manager/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "social-media-manager"
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

variable "platforms" {
  description = "Social media platforms to manage"
  type        = list(string)
}

variable "subnet_ids" {
  description = "Subnet IDs for ECS service"
  type        = list(string)
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_ecs_cluster" "social_media_cluster" {
  name = "social-media-manager-${var.environment}"
}

resource "aws_ecs_task_definition" "social_media_task" {
  family = "social-media-manager"
  network_mode = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu = "512"
  memory = "1024"
  container_definitions = "[{"name": "social-media-manager", "image": "${var.container_image}", "essential": true, "portMappings": [{"containerPort": 8080, "protocol": "tcp"}], "environment": [{"name": "ENVIRONMENT", "value": "${var.environment}"}, {"name": "PLATFORMS", "value": "${join(\",\", var.platforms)}"}]}]"
  execution_role_arn = "${aws_iam_role.ecs_execution_role.arn}"
  task_role_arn = "${aws_iam_role.ecs_task_role.arn}"
}

resource "aws_ecs_service" "social_media_service" {
  name = "social-media-manager"
  cluster = "${aws_ecs_cluster.social_media_cluster.id}"
  task_definition = "${aws_ecs_task_definition.social_media_task.arn}"
  desired_count = 1
  launch_type = "FARGATE"
  network_configuration = {"subnets": "${var.subnet_ids}", "security_groups": ["${aws_security_group.social_media_sg.id}"]}
}

resource "aws_security_group" "social_media_sg" {
  name = "social-media-manager-sg"
  description = "Security group for social media manager"
  ingress = [{"from_port": 8080, "to_port": 8080, "protocol": "tcp", "cidr_blocks": ["0.0.0.0/0"]}]
}

resource "aws_dynamodb_table" "social_media_posts" {
  name = "social-media-posts-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "post_id"
  attribute = [{"name": "post_id", "type": "S"}, {"name": "platform", "type": "S"}, {"name": "scheduled_time", "type": "S"}]
}

resource "aws_cloudwatch_event_rule" "post_scheduler" {
  name = "social-media-post-scheduler"
  schedule_expression = "rate(5 minutes)"
}

resource "aws_iam_role" "ecs_execution_role" {
  name = "social-media-ecs-execution-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "ecs-tasks.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

resource "aws_iam_role" "ecs_task_role" {
  name = "social-media-ecs-task-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "ecs-tasks.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "cluster_name" {
  description = "ECS cluster name"
  value       = ${aws_ecs_cluster.social_media_cluster.name}
}

output "service_name" {
  description = "ECS service name"
  value       = ${aws_ecs_service.social_media_service.name}
}

output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = ${aws_dynamodb_table.social_media_posts.name}
}
