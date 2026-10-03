# Gated Communities — Terraform Infrastructure

Production-grade Terraform configuration for deploying the Gated Communities platform on AWS.

## Architecture

This configuration provisions:

- **VPC** — Multi-AZ VPC with public and private subnets, NAT gateways, and proper routing
- **EKS** — Managed Kubernetes cluster with auto-scaling node groups
- **RDS** — Highly-available PostgreSQL database in private subnets
- **ElastiCache** — Redis cluster for caching and session storage
- **S3** — Buckets for assets, backups, and logs

## Prerequisites

- [Terraform](https://www.terraform.io/downloads.html) >= 1.5.0
- [AWS CLI](https://aws.amazon.com/cli/) configured with appropriate credentials
- An S3 bucket for remote state: `gated-communities-terraform-state`
- A DynamoDB table for state locking: `gated-communities-terraform-locks`

## Quick Start

1. **Clone and navigate to the terraform directory:**
   ```bash
   cd ~/GRC_Claw/projects/gated-communities/terraform/
   ```

2. **Create your tfvars file:**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

3. **Edit `terraform.tfvars`** with your actual values (especially `rds_password`).

4. **Initialize Terraform:**
   ```bash
   terraform init
   ```

5. **Review the execution plan:**
   ```bash
   terraform plan
   ```

6. **Apply the infrastructure:**
   ```bash
   terraform apply
   ```

## Remote State

State is stored in S3 with DynamoDB-based locking. The backend configuration is in `main.tf`:

```hcl
backend "s3" {
  bucket         = "gated-communities-terraform-state"
  key            = "infrastructure/terraform.tfstate"
  region         = "us-east-1"
  encrypt        = true
  dynamodb_table = "gated-communities-terraform-locks"
}
```

### One-time Backend Bootstrap

Before first use, create the S3 bucket and DynamoDB table:

```bash
# Create the state bucket
aws s3api create-bucket \
  --bucket gated-communities-terraform-state \
  --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket gated-communities-terraform-state \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket gated-communities-terraform-state \
  --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

# Create the DynamoDB lock table
aws dynamodb create-table \
  --table-name gated-communities-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

## Module Structure

```
terraform/
├── main.tf                  # Root module — wires everything together
├── variables.tf             # Input variables
├── outputs.tf               # Output values
├── terraform.tfvars.example # Example variable values
├── README.md                # This file
└── modules/
    ├── vpc/                 # VPC, subnets, NAT gateways, route tables
    ├── eks/                 # EKS cluster, node groups, IAM roles
    ├── rds/                 # RDS PostgreSQL, parameter groups, subnet groups
    ├── elasticache/         # ElastiCache Redis, subnet groups, security groups
    └── s3/                  # S3 buckets with versioning and encryption
```

## Security

- All resources are tagged for cost allocation and access control
- RDS and ElastiCache are deployed in private subnets
- S3 buckets have versioning and encryption enabled
- EKS cluster endpoint is private by default
- Security groups follow least-privilege principles

## Cost Optimization

- Use `t3` burstable instances for non-production environments
- Adjust `eks_node_min_size` to 0 for development to scale to zero
- Consider Graviton (`t4g`) instances for better price-performance

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

> **Warning:** This will delete all data including databases and S3 buckets. Ensure you have backups before running destroy.
