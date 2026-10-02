# broker-enablement.tf
# Broker Enablement - Broker training and enablement platform
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
    key            = "broker-enablement/terraform.tfstate"
    region         = "${var.region}"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "broker-enablement"
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

variable "training_modules" {
  description = "Available training modules"
  type        = list(string)
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Resources
resource "aws_ecs_cluster" "broker_cluster" {
  name = "broker-enablement-${var.environment}"
}

resource "aws_ecs_task_definition" "broker_task" {
  family = "broker-enablement"
  network_mode = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu = "512"
  memory = "1024"
  container_definitions = "[{"name": "broker-enablement", "image": "${var.container_image}", "essential": true, "portMappings": [{"containerPort": 8080, "protocol": "tcp"}]}]"
  execution_role_arn = "${aws_iam_role.ecs_execution_role.arn}"
}

resource "aws_ecs_service" "broker_service" {
  name = "broker-enablement"
  cluster = "${aws_ecs_cluster.broker_cluster.id}"
  task_definition = "${aws_ecs_task_definition.broker_task.arn}"
  desired_count = 1
  launch_type = "FARGATE"
  network_configuration = {"subnets": "${var.subnet_ids}", "security_groups": ["${aws_security_group.broker_sg.id}"]}
}

resource "aws_security_group" "broker_sg" {
  name = "broker-enablement-sg"
  ingress = [{"from_port": 8080, "to_port": 8080, "protocol": "tcp", "cidr_blocks": ["0.0.0.0/0"]}]
}

resource "aws_dynamodb_table" "broker_training" {
  name = "broker-training-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "broker_id"
  attribute = [{"name": "broker_id", "type": "S"}, {"name": "training_module", "type": "S"}]
}

resource "aws_s3_bucket" "broker_materials" {
  bucket = "broker-materials-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_iam_role" "ecs_execution_role" {
  name = "broker-ecs-execution-role"
  assume_role_policy = "{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "ecs-tasks.amazonaws.com"}, "Action": "sts:AssumeRole"}]}"
}

# Outputs
output "cluster_name" {
  description = "ECS cluster name"
  value       = ${aws_ecs_cluster.broker_cluster.name}
}

output "training_table" {
  description = "Training table name"
  value       = ${aws_dynamodb_table.broker_training.name}
}

output "materials_bucket" {
  description = "Materials bucket name"
  value       = ${aws_s3_bucket.broker_materials.id}
}
