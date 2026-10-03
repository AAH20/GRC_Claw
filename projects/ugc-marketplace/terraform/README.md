# UGC Marketplace — Terraform Infrastructure

Production-grade Terraform configuration for deploying the UGC Marketplace platform on AWS.

## Architecture Overview

This configuration provisions the following infrastructure:

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **VPC** | AWS VPC | Isolated network with public, private, and database subnets across multiple AZs |
| **EKS** | Amazon EKS (Kubernetes 1.29) | Container orchestration for microservices |
| **RDS** | Amazon RDS (PostgreSQL 16) | Primary relational database |
| **ElastiCache** | Amazon ElastiCache (Redis 7) | In-memory caching and session store |
| **S3** | Amazon S3 | Object storage for app data, media assets, and logs |
| **CloudFront** | Amazon CloudFront | Global CDN for content delivery |
| **Route 53** | Amazon Route 53 | DNS management |
| **CloudWatch** | Amazon CloudWatch | Monitoring, logging, and alerting |

## Prerequisites

- [Terraform](https://www.terraform.io/downloads.html) >= 1.6.0
- [AWS CLI](https://aws.amazon.com/cli/) configured with appropriate credentials
- [kubectl](https://kubernetes.io/docs/tasks/tools/) for cluster management
- AWS account with sufficient permissions

## Quick Start

### 1. Clone and Configure

```bash
cd ~/GRC_Claw/projects/ugc-marketplace/terraform/
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Review the Plan

```bash
terraform plan -out=tfplan
```

### 4. Apply the Configuration

```bash
terraform apply tfplan
```

### 5. Configure kubectl

```bash
aws eks update-kubeconfig --region us-east-1 --name ugc-marketplace-prod
```

### 6. Verify the Deployment

```bash
kubectl get nodes
kubectl get pods --all-namespaces
```

## Remote State Configuration

For team collaboration, configure remote state storage:

1. Create an S3 bucket for state storage:
   ```bash
   aws s3 mb s3://ugc-marketplace-terraform-state --region us-east-1
   aws s3api put-bucket-versioning \
     --bucket ugc-marketplace-terraform-state \
     --versioning-configuration Status=Enabled
   ```

2. Create a DynamoDB table for state locking:
   ```bash
   aws dynamodb create-table \
     --table-name ugc-marketplace-terraform-locks \
     --attribute-definitions AttributeName=LockID,AttributeType=S \
     --key-schema AttributeName=LockID,KeyType=HASH \
     --billing-mode PAY_PER_REQUEST
   ```

3. Uncomment and configure the backend block in `main.tf`:
   ```hcl
   backend "s3" {
     bucket         = "ugc-marketplace-terraform-state"
     key            = "prod/terraform.tfstate"
     region         = "us-east-1"
     encrypt        = true
     dynamodb_table = "ugc-marketplace-terraform-locks"
   }
   ```

4. Re-initialize:
   ```bash
   terraform init -migrate-state
   ```

## Module Structure

```
terraform/
├── main.tf                    # Root module — orchestrates all sub-modules
├── variables.tf               # Input variables
├── outputs.tf                 # Output variables
├── terraform.tfvars.example   # Example variable values
├── README.md                  # This file
└── modules/
    ├── vpc/                   # VPC, subnets, NAT Gateway, route tables
    ├── security/              # Security groups, KMS keys
    ├── eks/                   # EKS cluster, node groups, IRSA
    ├── rds/                   # RDS PostgreSQL instance
    ├── elasticache/           # ElastiCache Redis cluster
    ├── s3/                    # S3 buckets with lifecycle policies
    ├── cloudfront/            # CloudFront distribution
    ├── route53/               # Route 53 DNS records
    └── monitoring/            # CloudWatch dashboards and alarms
```

## Environment Management

Use separate state files per environment:

```bash
# Development
terraform workspace new dev
terraform apply -var-file=terraform.dev.tfvars

# Staging
terraform workspace new staging
terraform apply -var-file=terraform.staging.tfvars

# Production
terraform workspace new prod
terraform apply -var-file=terraform.prod.tfvars
```

## Security Best Practices

- **Secrets Management**: Use AWS Secrets Manager or SSM Parameter Store for sensitive values. Never commit `terraform.tfvars` to version control.
- **Encryption at Rest**: All storage (RDS, ElastiCache, S3, EBS) is encrypted using KMS keys.
- **Encryption in Transit**: TLS is enforced for all service-to-service communication.
- **Network Isolation**: Database and cache subnets have no internet access. NAT Gateway provides controlled outbound access for private subnets.
- **Least Privilege**: Security groups follow the principle of least privilege.
- **VPC Flow Logs**: Enabled for network traffic auditing.

## Cost Optimization

- Use `single_nat_gateway = true` for non-production environments
- Use SPOT instances for non-critical workloads (see `spot` node group)
- Right-size RDS and ElastiCache instances based on actual usage
- Enable S3 lifecycle policies to transition old data to cheaper storage classes
- Use CloudFront to reduce origin load and data transfer costs

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

**Warning**: This will delete all data. Ensure you have backups before running this command.

## Troubleshooting

### EKS nodes not joining the cluster
- Verify the node IAM role has the required policies
- Check that the security group allows communication between nodes and the control plane
- Review node group logs in the AWS Console

### RDS connection failures
- Verify the security group allows inbound traffic on the database port
- Check that the database is in the same VPC as the connecting resources
- Ensure the database is publicly accessible only if intended

### CloudFront distribution not serving content
- Verify the origin S3 bucket policy allows CloudFront access
- Check that the ACM certificate is in `us-east-1`
- Confirm the alternate domain names match the ACM certificate

## License

Proprietary — All rights reserved.
