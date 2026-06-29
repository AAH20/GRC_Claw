# GRC Claw Sovereign Deployment — Terraform
# Supports AWS (primary), Azure, GCP

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "cloud_provider" { default = "aws" }
variable "region" { default = "me-south-1" }
variable "environment" { default = "production" }
variable "domain" { type = string }
variable "instance_type" { default = "t3.xlarge" }
variable "disk_size_gb" { default = 100 }
variable "ollama_model" { default = "llama3.1:8b" }
variable "backup_bucket" { type = string }
variable "backup_region" { default = "" }
variable "smtp_host" { default = "" }
variable "smtp_port" { default = 587 }
variable "smtp_user" { default = "" }

provider "aws" {
  region = var.region
}

# VPC + networking
resource "aws_vpc" "grc_vpc" {
  cidr_block           = "10.10.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = { Name = "grc-claw-sovereign-${var.environment}", Environment = var.environment }
}

resource "aws_subnet" "grc_public" {
  vpc_id                  = aws_vpc.grc_vpc.id
  cidr_block              = "10.10.1.0/24"
  availability_zone       = "${var.region}a"
  map_public_ip_on_launch = true
  tags = { Name = "grc-claw-public" }
}

resource "aws_internet_gateway" "grc_igw" {
  vpc_id = aws_vpc.grc_vpc.id
  tags   = { Name = "grc-claw-igw" }
}

resource "aws_route_table" "grc_rt" {
  vpc_id = aws_vpc.grc_vpc.id
  route { cidr_block = "0.0.0.0/0"; gateway_id = aws_internet_gateway.grc_igw.id }
}

resource "aws_route_table_association" "grc_rta" {
  subnet_id      = aws_subnet.grc_public.id
  route_table_id = aws_route_table.grc_rt.id
}

# Security group
resource "aws_security_group" "grc_sg" {
  name        = "grc-claw-sg"
  description = "GRC Claw sovereign deployment"
  vpc_id      = aws_vpc.grc_vpc.id

  ingress { from_port = 443; to_port = 443; protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"] }
  ingress { from_port = 80;  to_port = 80;  protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"] }
  ingress { from_port = 22;  to_port = 22;  protocol = "tcp"; cidr_blocks = ["10.0.0.0/8"] }
  egress  { from_port = 0;   to_port = 0;   protocol = "-1";  cidr_blocks = ["0.0.0.0/0"] }
  tags = { Name = "grc-claw-sg" }
}

# Key pair
resource "aws_key_pair" "grc_key" {
  key_name   = "grc-claw-${var.environment}"
  public_key = file("~/.ssh/id_rsa.pub")
}

# EC2 instance (Ubuntu 24.04 LTS)
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  filter { name = "name";                values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"] }
  filter { name = "virtualization-type"; values = ["hvm"] }
}

resource "aws_instance" "grc_sovereign" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.grc_public.id
  vpc_security_group_ids = [aws_security_group.grc_sg.id]
  key_name               = aws_key_pair.grc_key.key_name
  iam_instance_profile   = aws_iam_instance_profile.grc_profile.name

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.disk_size_gb
    encrypted             = true
    delete_on_termination = false
  }

  user_data = base64encode(templatefile("${path.module}/scripts/cloud-init.sh.tpl", {
    ollama_model = var.ollama_model
    domain       = var.domain
    environment  = var.environment
  }))

  tags = { Name = "grc-claw-sovereign-${var.environment}", Environment = var.environment, ManagedBy = "terraform" }
}

# Elastic IP
resource "aws_eip" "grc_eip" {
  instance = aws_instance.grc_sovereign.id
  domain   = "vpc"
  tags     = { Name = "grc-claw-eip" }
}

# IAM role for S3 backup access
resource "aws_iam_role" "grc_role" {
  name = "grc-claw-sovereign-${var.environment}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{ Action = "sts:AssumeRole"; Effect = "Allow"; Principal = { Service = "ec2.amazonaws.com" } }]
  })
}

resource "aws_iam_role_policy" "grc_s3_backup" {
  name = "grc-claw-s3-backup"
  role = aws_iam_role.grc_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject", "s3:PutObject", "s3:ListBucket", "s3:DeleteObject"]
      Resource = ["arn:aws:s3:::${var.backup_bucket}", "arn:aws:s3:::${var.backup_bucket}/*"]
    }]
  })
}

resource "aws_iam_instance_profile" "grc_profile" {
  name = "grc-claw-sovereign-${var.environment}"
  role = aws_iam_role.grc_role.name
}

# S3 backup bucket
resource "aws_s3_bucket" "grc_backup" {
  bucket = var.backup_bucket
  tags   = { Name = "grc-claw-backups", Environment = var.environment }
}

resource "aws_s3_bucket_versioning" "grc_backup_versioning" {
  bucket = aws_s3_bucket.grc_backup.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "grc_backup_enc" {
  bucket = aws_s3_bucket.grc_backup.id
  rule { apply_server_side_encryption_by_default { sse_algorithm = "AES256" } }
}

# Outputs
output "public_ip"     { value = aws_eip.grc_eip.public_ip }
output "instance_id"   { value = aws_instance.grc_sovereign.id }
output "ssh_command"   { value = "ssh ubuntu@${aws_eip.grc_eip.public_ip}" }
output "platform_url"  { value = "https://${var.domain}" }
output "next_steps"    { value = "Point your DNS A record for ${var.domain} to ${aws_eip.grc_eip.public_ip}, then run ./scripts/init-sovereign.sh" }
