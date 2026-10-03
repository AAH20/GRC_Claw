# Recruitment Platform - Terraform Infrastructure

Production-grade Terraform configuration for deploying the Recruitment Platform on AWS.

## Architecture Overview

This infrastructure includes:

- **VPC** — Multi-AZ VPC with public, private, and database subnets, NAT gateways, and flow logs
- **EKS** — Managed Kubernetes cluster with general and spot node groups, IRSA, and cluster addons
- **RDS** — Highly available PostgreSQL database with encryption, performance insights, and automated backups
- **ElastiCache** — Redis cluster with encryption at rest and in transit, automatic failover
- **S3** — Application storage and backup buckets with versioning, encryption, and lifecycle policies
- **KMS** — Encryption keys for EKS secrets, RDS, and S3
- **IAM** — Roles for service accounts (cert-manager, external-dns, AWS Load Balancer Controller)
- **AWS Backup** — Centralized backup vault with daily and weekly backup plans

## Prerequisites

- [Terraform](https://www.terraform.io/downloads.html) >= 1.5.0
- [AWS CLI](https://aws.amazon.com/cli/) configured with appropriate credentials
- [kubectl](https://kubernetes.io/docs/tasks/tools/) installed
- [Helm](https://helm.sh/docs/intro/install/) installed (optional, for deployments)

## Quick Start

### 1. Clone and Navigate

```bash
cd ~/GRC_Claw/projects/recruitment-platform/terraform/
```

### 2. Configure Variables

Copy the example variables file and customize:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your desired values.

### 3. Initialize Terraform

```bash
terraform init
```

This will:
- Download required providers
- Configure the S3 backend for remote state
- Set up the DynamoDB table for state locking

### 4. Review the Plan

```bash
terraform plan
```

Review the planned changes carefully before applying.

### 5. Apply the Infrastructure

```bash
terraform apply
```

Type `yes` when prompted to confirm.

### 6. Configure kubectl

```bash
aws eks update-kubeconfig --name recruitment-platform-development-eks --region us-east-1
```

### 7. Verify the Deployment

```bash
kubectl get nodes
kubectl get pods --all-namespaces
```

## Remote State

State is stored in an S3 bucket with DynamoDB-based locking:

- **State Bucket**: `recruitment-platform-terraform-state`
- **Lock Table**: `recruitment-platform-terraform-locks`
- **Region**: `us-east-1`
- **Encryption**: Enabled (AES-256)

### Creating the Backend Resources

Before first use, create the S3 bucket and DynamoDB table for remote state:

```bash
# Create the S3 bucket
aws s3api create-bucket \
  --bucket recruitment-platform-terraform-state \
  --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket recruitment-platform-terraform-state \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket recruitment-platform-terraform-state \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

# Create the DynamoDB table for state locking
aws dynamodb create-table \
  --table-name recruitment-platform-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

## Environments

### Development

```bash
terraform workspace new development
terraform apply -var-file=terraform.tfvars
```

### Staging

```bash
terraform workspace new staging
# Create terraform.tfvars.staging with staging values
terraform apply -var-file=terraform.tfvars.staging
```

### Production

```bash
terraform workspace new production
# Create terraform.tfvars.production with production values
terraform apply -var-file=terraform.tfvars.production
```

## Production Checklist

Before deploying to production:

- [ ] Set `environment = "production"`
- [ ] Set `eks_public_access = false` (or restrict CIDRs)
- [ ] Set `rds_instance_class` to a production-grade instance (e.g., `db.r6g.xlarge`)
- [ ] Set `rds_allocated_storage` and `rds_max_allocated_storage` appropriately
- [ ] Set `rds_backup_retention = 35` (maximum)
- [ ] Set `elasticache_node_type` to a production-grade instance
- [ ] Set `elasticache_num_cache_clusters >= 2` for HA
- [ ] Set `eks_node_min_size >= 2` for HA
- [ ] Set `eks_spot_min_size = 0` (avoid spot for production workloads)
- [ ] Review and adjust `vpc_cidr` to avoid conflicts
- [ ] Enable deletion protection for RDS (automatic in production)
- [ ] Configure AWS Backup selection tags on resources
- [ ] Set up monitoring and alerting (CloudWatch alarms)
- [ ] Review security group rules and restrict as needed
- [ ] Enable AWS GuardDuty and Security Hub
- [ ] Configure AWS Config for compliance monitoring

## Security

- All data encrypted at rest using KMS customer-managed keys
- All data encrypted in transit (TLS)
- Private subnets for EKS nodes, RDS, and ElastiCache
- Security groups restrict traffic to minimum required
- S3 buckets block all public access
- EKS cluster endpoint private access enabled
- IRSA used instead of node IAM roles where possible

## Cost Optimization

- Spot instances for non-critical workloads
- S3 lifecycle policies for cost-effective storage
- Right-sized RDS and ElastiCache instances for development
- NAT gateway sharing in non-production environments
- EBS gp3 volumes for better price-performance

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

**Warning**: This will delete all data including RDS snapshots and S3 objects. Proceed with caution.

## Troubleshooting

### State Lock Issues

If a previous apply was interrupted, you may need to force-unlock:

```bash
terraform force-unlock <LOCK_ID>
```

### EKS Node Group Issues

Check node group status:

```bash
aws eks describe-nodegroup \
  --cluster-name recruitment-platform-development-eks \
  --nodegroup-name recruitment-platform-development-general \
  --region us-east-1
```

### RDS Connection Issues

Verify security group rules and network connectivity:

```bash
nc -zv <rds-endpoint> 5432
```

## Module Structure

```
terraform/
├── main.tf                  # Main infrastructure configuration
├── variables.tf             # Input variables
├── outputs.tf               # Output values
├── terraform.tfvars.example # Example variable values
└── README.md                # This file
```

## Resources

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Terraform EKS Module](https://registry.terraform.io/modules/terraform-aws-modules/eks/aws/latest)
- [Terraform VPC Module](https://registry.terraform.io/modules/terraform-aws-modules/vpc/aws/latest)
- [Terraform RDS Module](https://registry.terraform.io/modules/terraform-aws-modules/rds/aws/latest)
- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
