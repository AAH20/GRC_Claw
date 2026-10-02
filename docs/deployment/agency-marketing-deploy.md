# Agency Marketing — Deployment Guide

> **Version:** 1.0.0 | **Port:** 8037 | **Database:** agency_data

## Overview

Marketing agency management platform for managing multiple clients, white-label reporting, campaign management, resource allocation, and agency analytics.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Load Balancer                     │
├─────────────────────────────────────────────────────┤
│              Agency Marketing Service                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │   API    │  │  Worker  │  │  Cache   │          │
│  │  Server  │  │  Queue   │  │  Layer   │          │
│  └──────────┘  └──────────┘  └──────────┘          │
├─────────────────────────────────────────────────────┤
│              PostgreSQL (agency_data)                      │
└─────────────────────────────────────────────────────┘
```

## Prerequisites

- Docker 24.0+ and Docker Compose v2
- Kubernetes 1.28+ cluster (for K8s deployment)
- Terraform 1.6+ (for infrastructure provisioning)
- Helm 3.13+ (for Kubernetes deployments)
- `kubectl` configured with cluster access
- Domain name and SSL certificates (for production)

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AGENCY_WHITE_LABEL_URL` | Yes | Environment-specific value |
| `CLIENT_ISOLATION_RULES` | Yes | Environment-specific value |
| `REPORTING_TEMPLATE_PATH` | Yes | Environment-specific value |
| `RESOURCE_PLANNING_URL` | Yes | Environment-specific value |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `LOG_LEVEL` | No | Logging level (default: INFO) |
| `METRICS_ENABLED` | No | Enable Prometheus metrics (default: true) |

## 1. Docker Deployment

### Quick Start

```bash
git clone https://github.com/GRC-Claw/agency-marketing.git
cd agency-marketing

cat > .env << 'EOF'
DATABASE_URL=postgresql://user:password@localhost:5432/agency_data
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
EOF

docker build -t agency-marketing:latest .
docker run -d \
  --name agency-marketing \
  -p 8037:8037 \
  --env-file .env \
  --restart unless-stopped \
  agency-marketing:latest
```

### Docker Compose (Full Stack)

```yaml
version: "3.9"

services:
  agency-marketing:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8037:8037"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/agency_data
      - REDIS_URL=redis://redis:6379/0
      - LOG_LEVEL=INFO
      - AGENCY_WHITE_LABEL_URL=${AGENCY_WHITE_LABEL_URL}
      - CLIENT_ISOLATION_RULES=${CLIENT_ISOLATION_RULES}
      - REPORTING_TEMPLATE_PATH=${REPORTING_TEMPLATE_PATH}
      - RESOURCE_PLANNING_URL=${RESOURCE_PLANNING_URL}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8037/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: "1.0"
        reservations:
          memory: 512Mi
          cpus: "0.25"

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: agency_data
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
  redisdata:
```

```bash
docker compose up -d
docker compose logs -f agency-marketing
```

### Production Docker Run

```bash
docker run -d \
  --name agency-marketing \
  -p 8037:8037 \
  --env-file .env.production \
  --restart unless-stopped \
  --memory=2g \
  --cpus=1.0 \
  --log-driver=json-file \
  --log-opt max-size=100m \
  --log-opt max-file=5 \
  --security-opt=no-new-privileges \
  --cap-drop=ALL \
  ghcr.io/grc-claw/agency-marketing:v1.0.0
```

## 2. Kubernetes Deployment

### Namespace and Secrets

```bash
kubectl create namespace grc-claw
kubectl create secret generic agency-marketing-secrets \
  --from-literal=DATABASE_URL='postgresql://user:pass@postgres:5432/agency_data' \
  --from-literal=REDIS_URL='redis://redis:6379/0' \
  --from-literal=AGENCY_WHITE_LABEL_URL='your_value_here' \
  --from-literal=CLIENT_ISOLATION_RULES='your_value_here' \
  --from-literal=REPORTING_TEMPLATE_PATH='your_value_here' \
  --from-literal=RESOURCE_PLANNING_URL='your_value_here' \
  -n grc-claw
```

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agency-marketing
  namespace: grc-claw
  labels:
    app: agency-marketing
    version: v1.0.0
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: agency-marketing
  template:
    metadata:
      labels:
        app: agency-marketing
        version: v1.0.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8037"
        prometheus.io/path: "/api/v1/metrics"
    spec:
      serviceAccountName: agency-marketing-sa
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: agency-marketing
        image: ghcr.io/grc-claw/agency-marketing:v1.0.0
        imagePullPolicy: Always
        ports:
        - containerPort: 8037
          protocol: TCP
        envFrom:
        - secretRef:
            name: agency-marketing-secrets
        env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: POD_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8037
          initialDelaySeconds: 30
          periodSeconds: 15
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8037
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        startupProbe:
          httpGet:
            path: /api/v1/health
            port: 8037
          initialDelaySeconds: 10
          periodSeconds: 5
          failureThreshold: 30
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
      volumes:
      - name: tmp
        emptyDir: {}
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - agency-marketing
              topologyKey: topology.kubernetes.io/zone
```

### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: agency-marketing
  namespace: grc-claw
  labels:
    app: agency-marketing
spec:
  type: ClusterIP
  selector:
    app: agency-marketing
  ports:
  - port: 80
    targetPort: 8037
    protocol: TCP
    name: http
```

### Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: agency-marketing
  namespace: grc-claw
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "60"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "60"
spec:
  tls:
  - hosts:
    - agency-marketing.grc-claw.io
    secretName: agency-marketing-tls
  rules:
  - host: agency-marketing.grc-claw.io
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: agency-marketing
            port:
              number: 80
```

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agency-marketing-hpa
  namespace: grc-claw
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agency-marketing
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
```

### Pod Disruption Budget

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: agency-marketing-pdb
  namespace: grc-claw
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: agency-marketing
```

### Redis Dependency

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agency-marketing-redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: agency-marketing-redis
  template:
    metadata:
      labels:
        app: agency-marketing-redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
---
apiVersion: v1
kind: Service
metadata:
  name: agency-marketing-redis
spec:
  selector:
    app: agency-marketing-redis
  ports:
  - port: 6379
```


### Background Worker (CronJob)

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: agency-marketing-worker
spec:
  schedule: "*/5 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: worker
            image: ghcr.io/grc-claw/agency-marketing:latest
            command: ["python", "-m", "worker"]
            envFrom:
            - secretRef:
                name: agency-marketing-secrets
          restartPolicy: OnFailure
```

### Apply All Manifests

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/pdb.yaml
```

### Helm Chart (Alternative)

```bash
helm repo add grc-claw https://charts.grc-claw.io
helm install agency-marketing grc-claw/agency-marketing \
  --namespace grc-claw \
  --create-namespace \
  --set image.tag=v1.0.0 \
  --set replicaCount=3 \
  --set ingress.host=agency-marketing.grc-claw.io
```

## 3. Terraform Infrastructure

### AWS Deployment

```hcl
terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket         = "grc-claw-terraform-state"
    key            = "agency-marketing/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  default = "us-east-1"
}

variable "environment" {
  default = "production"
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
  name = "agency-marketing-vpc"
  cidr = "10.0.0.0/16"
  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  enable_nat_gateway = true
  single_nat_gateway = false
  enable_vpn_gateway = false
  tags = {
    Name        = "agency-marketing-vpc"
    Environment = var.environment
    Project     = "GRC-Claw"
  }
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"
  cluster_name    = "agency-marketing-cluster"
  cluster_version = "1.28"
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  cluster_endpoint_private_access = true
  cluster_endpoint_public_access  = true
  eks_managed_node_groups = {
    main = {
      desired_size = 3
      min_size     = 2
      max_size     = 10
      instance_types = ["m6i.xlarge"]
      capacity_type  = "ON_DEMAND"
      labels = {
        workload = "general"
      }
      tags = {
        Name = "agency-marketing-worker"
      }
    }
  }
  tags = {
    Name        = "agency-marketing-cluster"
    Environment = var.environment
  }
}

resource "aws_db_instance" "agency-marketing_db" {
  identifier     = "agency-marketing-db"
  engine         = "postgres"
  engine_version = "16.1"
  instance_class = "db.r6g.xlarge"
  allocated_storage     = 100
  max_allocated_storage = 500
  storage_type          = "gp3"
  storage_encrypted     = true
  db_name  = "agency_data"
  username = "grc_admin"
  password = random_password.db_password.result
  vpc_security_group_ids = [aws_security_group.db.id]
  db_subnet_group_name   = aws_db_subnet_group.agency-marketing.name
  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "Mon:04:00-Mon:05:00"
  deletion_protection = true
  skip_final_snapshot = false
  final_snapshot_identifier = "agency-marketing-final-snapshot"
  performance_insights_enabled = true
  tags = {
    Name        = "agency-marketing-db"
    Environment = var.environment
  }
}

resource "random_password" "db_password" {
  length  = 32
  special = false
}

resource "aws_elasticache_replication_group" "agency-marketing_redis" {
  replication_group_id = "agency-marketing-redis"
  description          = "Redis cluster for Agency Marketing"
  node_type            = "cache.r6g.large"
  num_cache_clusters   = 2
  automatic_failover_enabled = true
  multi_az_enabled     = true
  engine_version = "7.0"
  port          = 6379
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  subnet_group_name  = aws_elasticache_subnet_group.agency-marketing.name
  security_group_ids = [aws_security_group.redis.id]
  snapshot_retention_limit = 7
  snapshot_window         = "05:00-06:00"
  tags = {
    Name        = "agency-marketing-redis"
    Environment = var.environment
  }
}

resource "aws_lb" "agency-marketing_alb" {
  name               = "agency-marketing-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = module.vpc.public_subnets
  enable_deletion_protection = true
  enable_http2             = true
  tags = {
    Name        = "agency-marketing-alb"
    Environment = var.environment
  }
}

resource "aws_lb_target_group" "agency-marketing_tg" {
  name     = "agency-marketing-tg"
  port     = 8037
  protocol = "HTTP"
  vpc_id   = module.vpc.vpc_id
  health_check {
    path                = "/api/v1/health"
    port                = "8037"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
  }
  deregistration_delay = 30
}

resource "aws_lb_listener" "agency-marketing_https" {
  load_balancer_arn = aws_lb.agency-marketing_alb.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate.agency-marketing.arn
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.agency-marketing_tg.arn
  }
}

resource "aws_ecs_cluster" "agency-marketing" {
  name = "agency-marketing-cluster"
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  tags = {
    Name        = "agency-marketing-cluster"
    Environment = var.environment
  }
}

resource "aws_ecs_task_definition" "agency-marketing" {
  family                   = "agency-marketing"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn           = aws_iam_role.ecs_task.arn
  container_definitions = jsonencode([{
    name  = "agency-marketing"
    image = "ghcr.io/grc-claw/agency-marketing:v1.0.0"
    essential = true
    portMappings = [{
      containerPort = 8037
      protocol      = "tcp"
    }]
    environment = [
      { name = "LOG_LEVEL", value = "INFO" },
      { name = "METRICS_ENABLED", value = "true" },
  { name = "AGENCY_WHITE_LABEL_URL", value = "placeholder" },
  { name = "CLIENT_ISOLATION_RULES", value = "placeholder" },
  { name = "REPORTING_TEMPLATE_PATH", value = "placeholder" },
  { name = "RESOURCE_PLANNING_URL", value = "placeholder" },
    ]
    secrets = [
      {
        name      = "DATABASE_URL"
        valueFrom = aws_secretsmanager_secret.agency-marketing_db.arn
      },
      {
        name      = "REDIS_URL"
        valueFrom = aws_secretsmanager_secret.agency-marketing_redis.arn
      }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.agency-marketing.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
    healthCheck = {
      command     = ["CMD-SHELL", "curl -f http://localhost:8037/api/v1/health || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 60
    }
  }])
}

resource "aws_ecs_service" "agency-marketing" {
  name            = "agency-marketing"
  cluster         = aws_ecs_cluster.agency-marketing.id
  task_definition = aws_ecs_task_definition.agency-marketing.arn
  desired_count   = 3
  launch_type     = "FARGATE"
  network_configuration {
    subnets          = module.vpc.private_subnets
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = false
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.agency-marketing_tg.arn
    container_name   = "agency-marketing"
    container_port   = 8037
  }
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
  propagate_tags = "SERVICE"
  tags = {
    Name        = "agency-marketing"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_metric_alarm" "agency-marketing_cpu" {
  alarm_name          = "agency-marketing-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 80
  alarm_actions       = [aws_sns_topic.agency-marketing_alerts.arn]
  dimensions = {
    ServiceName = "agency-marketing"
    ClusterName = "agency-marketing-cluster"
  }
}

resource "aws_cloudwatch_metric_alarm" "agency-marketing_memory" {
  alarm_name          = "agency-marketing-high-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 85
  alarm_actions       = [aws_sns_topic.agency-marketing_alerts.arn]
  dimensions = {
    ServiceName = "agency-marketing"
    ClusterName = "agency-marketing-cluster"
  }
}

output "alb_dns_name" {
  value = aws_lb.agency-marketing_alb.dns_name
}

output "db_endpoint" {
  value     = aws_db_instance.agency-marketing_db.endpoint
  sensitive = true
}

output "redis_endpoint" {
  value     = aws_elasticache_replication_group.agency-marketing_redis.primary_endpoint_address
  sensitive = true
}
```

### GCP Deployment

```hcl
terraform {
  required_version = ">= 1.6.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

variable "gcp_project_id" {
  description = "GCP Project ID"
}

variable "gcp_region" {
  default = "us-central1"
}

resource "google_compute_network" "agency-marketing_vpc" {
  name                    = "agency-marketing-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "agency-marketing_subnet" {
  name          = "agency-marketing-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.gcp_region
  network       = google_compute_network.agency-marketing_vpc.id
  private_ip_google_access = true
  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling       = 0.5
    metadata            = "INCLUDE_ALL_METADATA"
  }
}

resource "google_container_cluster" "agency-marketing" {
  name     = "agency-marketing-cluster"
  location = var.gcp_region
  network    = google_compute_network.agency-marketing_vpc.name
  subnetwork = google_compute_subnetwork.agency-marketing_subnet.name
  remove_default_node_pool = true
  initial_node_count       = 1
  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = "0.0.0.0/0"
      display_name = "all"
    }
  }
  release_channel {
    channel = "REGULAR"
  }
  workload_identity_config {
    workload_pool = "${var.gcp_project_id}.svc.id.goog"
  }
  addons_config {
    horizontal_pod_autoscaling {
      disabled = false
    }
    http_load_balancing {
      disabled = false
    }
  }
}

resource "google_container_node_pool" "agency-marketing_nodes" {
  name       = "agency-marketing-node-pool"
  location   = var.gcp_region
  cluster    = google_container_cluster.agency-marketing.name
  node_count = 3
  management {
    auto_repair  = true
    auto_upgrade = true
  }
  upgrade_settings {
    max_surge       = 1
    max_unavailable = 0
  }
  node_config {
    machine_type = "n2-standard-4"
    service_account = google_service_account.agency-marketing.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
    labels = {
      workload = "general"
    }
    tags = ["agency-marketing-node"]
    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }
  }
}

resource "google_sql_database_instance" "agency-marketing" {
  name             = "agency-marketing-db"
  database_version = "POSTGRES_16"
  region           = var.gcp_region
  settings {
    tier              = "db-custom-4-16384"
    availability_type = "REGIONAL"
    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.agency-marketing_vpc.id
    }
    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
    }
    maintenance_window {
      day  = 1
      hour = 4
    }
    insights_config {
      query_insights_enabled = true
    }
    database_flags {
      name  = "max_connections"
      value = "500"
    }
  }
  deletion_protection = true
}

resource "google_sql_database" "agency_data" {
  name     = "agency_data"
  instance = google_sql_database_instance.agency-marketing.name
}

resource "google_redis_instance" "agency-marketing" {
  name               = "agency-marketing-redis"
  tier               = "STANDARD_HA"
  memory_size_gb     = 5
  region             = var.gcp_region
  authorized_network = google_compute_network.agency-marketing_vpc.id
  redis_configs = {
    maxmemory-policy = "allkeys-lru"
  }
  maintenance_policy {
    weekly_maintenance_window {
      day = "TUESDAY"
      start_time {
        hours   = 3
        minutes = 0
      }
    }
  }
}

resource "google_cloud_run_v2_service" "agency-marketing" {
  name     = "agency-marketing"
  location = var.gcp_region
  ingress  = "INGRESS_TRAFFIC_ALL"
  template {
    service_account = google_service_account.agency-marketing.email
    vpc_access {
      connector = google_vpc_access_connector.agency-marketing.id
      egress    = "ALL_TRAFFIC"
    }
    containers {
      image = "ghcr.io/grc-claw/agency-marketing:v1.0.0"
      ports {
        container_port = 8037
      }
      env {
        name  = "DATABASE_URL"
        value = "postgresql://user:pass@/agency_data?host=/cloudsql/${google_sql_database_instance.agency-marketing.connection_name}"
      }
      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
        cpu_idle = true
      }
      startup_probe {
        http_get {
          path = "/api/v1/health"
          port = 8037
        }
        initial_delay_seconds = 10
        period_seconds        = 5
        failure_threshold     = 30
        timeout_seconds       = 5
      }
      liveness_probe {
        http_get {
          path = "/api/v1/health"
          port = 8037
        }
        period_seconds    = 15
        timeout_seconds   = 5
        failure_threshold = 3
      }
    }
    scaling {
      min_instance_count = 2
      max_instance_count = 20
    }
  }
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

output "cloud_run_url" {
  value = google_cloud_run_v2_service.agency-marketing.uri
}

output "db_connection_name" {
  value = google_sql_database_instance.agency-marketing.connection_name
}
```

### Azure Deployment

```hcl
terraform {
  required_version = ">= 1.6.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

variable "azure_region" {
  default = "East US"
}

variable "environment" {
  default = "production"
}

resource "azurerm_resource_group" "agency-marketing" {
  name     = "rg-agency-marketing-${var.environment}"
  location = var.azure_region
  tags = {
    Project     = "GRC-Claw"
    Environment = var.environment
    Service     = "Agency Marketing"
  }
}

resource "azurerm_virtual_network" "agency-marketing" {
  name                = "vnet-agency-marketing"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.agency-marketing.location
  resource_group_name = azurerm_resource_group.agency-marketing.name
}

resource "azurerm_subnet" "agency-marketing_aks" {
  name                 = "snet-aks"
  resource_group_name  = azurerm_resource_group.agency-marketing.name
  virtual_network_name = azurerm_virtual_network.agency-marketing.name
  address_prefixes     = ["10.0.1.0/24"]
}

resource "azurerm_subnet" "agency-marketing_db" {
  name                 = "snet-db"
  resource_group_name  = azurerm_resource_group.agency-marketing.name
  virtual_network_name = azurerm_virtual_network.agency-marketing.name
  address_prefixes     = ["10.0.2.0/24"]
  delegation {
    name = "postgresql"
    service_delegation {
      name    = "Microsoft.DBforPostgreSQL/flexibleServers"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
    }
  }
}

resource "azurerm_kubernetes_cluster" "agency-marketing" {
  name                = "aks-agency-marketing"
  location            = azurerm_resource_group.agency-marketing.location
  resource_group_name = azurerm_resource_group.agency-marketing.name
  dns_prefix          = "agency-marketing-aks"
  kubernetes_version  = "1.28"
  default_node_pool {
    name       = "general"
    node_count = 3
    vm_size    = "Standard_D4s_v3"
    vnet_subnet_id = azurerm_subnet.agency-marketing_aks.id
    upgrade_settings {
      max_surge = "10%"
    }
  }
  identity {
    type = "SystemAssigned"
  }
  network_profile {
    network_plugin    = "azure"
    load_balancer_sku = "standard"
    service_cidr      = "10.1.0.0/16"
    dns_service_ip    = "10.1.0.10"
  }
  oms_agent {
    log_analytics_workspace_id = azurerm_log_analytics_workspace.agency-marketing.id
  }
  tags = {
    Environment = var.environment
  }
}

resource "azurerm_postgresql_flexible_server" "agency-marketing" {
  name                = "psql-agency-marketing"
  resource_group_name = azurerm_resource_group.agency-marketing.name
  location            = azurerm_resource_group.agency-marketing.location
  version    = "16"
  sku_name   = "GP_Standard_D4s_v3"
  storage_mb = 131072
  backup_retention_days        = 30
  geo_redundant_backup_enabled = true
  delegated_subnet_id = azurerm_subnet.agency-marketing_db.id
  private_dns_zone_id = azurerm_private_dns_zone.agency-marketing.id
  high_availability {
    mode = "ZoneRedundant"
  }
  maintenance_window {
    day_of_week  = 0
    start_hour   = 4
    start_minute = 0
  }
  tags = {
    Environment = var.environment
  }
}

resource "azurerm_postgresql_flexible_server_database" "agency_data" {
  name      = "agency_data"
  server_id = azurerm_postgresql_flexible_server.agency-marketing.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

resource "azurerm_redis_cache" "agency-marketing" {
  name                = "redis-agency-marketing"
  location            = azurerm_resource_group.agency-marketing.location
  resource_group_name = azurerm_resource_group.agency-marketing.name
  capacity            = 2
  family              = "P"
  sku_name            = "Premium"
  enable_non_ssl_port = false
  minimum_tls_version = "1.2"
  redis_configuration {
    maxmemory_policy = "allkeys-lru"
  }
  patch_schedule {
    day_of_week    = "Tuesday"
    start_hour_utc = 3
  }
}

resource "azurerm_container_registry" "agency-marketing" {
  name                = "cragencymarketing"
  resource_group_name = azurerm_resource_group.agency-marketing.name
  location            = azurerm_resource_group.agency-marketing.location
  sku                 = "Premium"
  admin_enabled       = true
  georeplications {
    location = "West US 2"
    tags = {
      Environment = var.environment
    }
  }
  trust_policy {
    enabled = true
  }
  retention_policy {
    days    = 30
    enabled = true
  }
}

resource "azurerm_log_analytics_workspace" "agency-marketing" {
  name                = "law-agency-marketing"
  location            = azurerm_resource_group.agency-marketing.location
  resource_group_name = azurerm_resource_group.agency-marketing.name
  sku                 = "PerGB2018"
  retention_in_days   = 90
}

resource "azurerm_application_insights" "agency-marketing" {
  name                = "ai-agency-marketing"
  location            = azurerm_resource_group.agency-marketing.location
  resource_group_name = azurerm_resource_group.agency-marketing.name
  workspace_id        = azurerm_log_analytics_workspace.agency-marketing.id
  application_type    = "web"
}

output "aks_cluster_name" {
  value = azurerm_kubernetes_cluster.agency-marketing.name
}

output "postgres_fqdn" {
  value     = azurerm_postgresql_flexible_server.agency-marketing.fqdn
  sensitive = true
}

output "redis_hostname" {
  value = azurerm_redis_cache.agency-marketing.hostname
}
```

### Terraform Apply

```bash
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

## 4. Cloud Deployment

### AWS Deployment

#### Using AWS Console

1. **Create ECR Repository**
   ```bash
   aws ecr create-repository --repository-name agency-marketing --region us-east-1
   ```

2. **Push Docker Image**
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com
   docker build -t agency-marketing .
   docker tag agency-marketing:latest $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com/agency-marketing:v1.0.0
   docker push $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com/agency-marketing:v1.0.0
   ```

3. **Deploy via ECS**
   - Navigate to ECS → Clusters → Create Cluster
   - Select "EC2 Linux + Networking" or "Fargate"
   - Create Task Definition with the ECR image
   - Configure Service with Application Load Balancer
   - Set up Auto Scaling (min: 3, max: 20)

4. **Configure RDS**
   - Create PostgreSQL 16 instance
   - Enable Multi-AZ, encryption, and Performance Insights
   - Configure security group for ECS tasks

5. **Configure ElastiCache**
   - Create Redis 7 cluster with replication
   - Enable encryption at rest and in transit
   - Configure subnet group and security group

#### Using AWS CDK (Python)

```python
from aws_cdk import (
    Stack, aws_ecs as ecs, aws_ecs_patterns as ecs_patterns,
    aws_ec2 as ec2, aws_rds as rds, aws_ecr as ecr, Duration,
)
from constructs import Construct

class AgencyMarketingStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        vpc = ec2.Vpc(self, "VPC", max_azs=3)
        cluster = ecs.Cluster(self, "Cluster", vpc=vpc)
        repository = ecr.Repository(self, "Repo",
            repository_name="agency-marketing",
            image_scan_on_push=True,
            removal_policy=RemovalPolicy.RETAIN
        )
        rds.DatabaseInstance(self, "Database",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_16
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.R6G, ec2.InstanceSize.LARGE
            ),
            vpc=vpc, multi_az=True, storage_encrypted=True,
            deletion_protection=True, database_name="agency_data"
        )
        service = ecs_patterns.ApplicationLoadBalancedFargateService(self, "Service",
            cluster=cluster, cpu=1024, memory_limit_mib=2048,
            desired_count=3,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_ecr_repository(repository, "v1.0.0"),
                container_port=8037,
                environment={"LOG_LEVEL": "INFO"},
                secrets={
                    "DATABASE_URL": ecs.Secret.from_secrets_manager(db.secret, "connectionString"),
                }
            ),
            health_check_grace_period=Duration.seconds(60),
            circuit_breaker=ecs.DeploymentCircuitBreaker(rollback=True)
        )
        service.target_group.configure_health_check(
            path="/api/v1/health",
            interval=Duration.seconds(30),
            timeout=Duration.seconds(5),
            healthy_threshold_count=2,
            unhealthy_threshold_count=3
        )
```

### GCP Deployment

#### Using gcloud CLI

```bash
gcloud config set project YOUR_PROJECT_ID
gcloud services enable container.googleapis.com sqladmin.googleapis.com redis.googleapis.com run.googleapis.com monitoring.googleapis.com cloudbuild.googleapis.com

gcloud container clusters create agency-marketing-cluster \
  --region=us-central1 --num-nodes=3 --machine-type=n2-standard-4 \
  --enable-autoscaling --min-nodes=2 --max-nodes=10 \
  --enable-network-policy --enable-autoupgrade --enable-autorepair \
  --workload-pool=YOUR_PROJECT_ID.svc.id.goog

gcloud sql instances create agency-marketing-db \
  --database-version=POSTGRES_16 --tier=db-custom-4-16384 \
  --region=us-central1 --availability-type=regional \
  --storage-auto-increase --backup-start-time=03:00 \
  --enable-point-in-time-recovery

gcloud sql databases create agency_data --instance=agency-marketing-db

gcloud redis instances create agency-marketing-redis \
  --size=5 --region=us-central1 --zone=us-central1-a \
  --network=default --tier=standard

gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/agency-marketing:v1.0.0

gcloud run deploy agency-marketing \
  --image=gcr.io/YOUR_PROJECT_ID/agency-marketing:v1.0.0 \
  --region=us-central1 --platform=managed \
  --min-instances=2 --max-instances=20 \
  --concurrency=100 --timeout=300 \
  --set-env-vars="LOG_LEVEL=INFO" \
  --set-secrets="DATABASE_URL=db-url:latest,REDIS_URL=redis-url:latest" \
  --allow-unauthenticated
```

### Azure Deployment

#### Using Azure CLI

```bash
az login
az group create --name rg-agency-marketing-production --location eastus

az acr create --resource-group rg-agency-marketing-production \
  --name cragencymarketing --sku Premium --location eastus

az acr build --registry cragencymarketing --image agency-marketing:v1.0.0 .

az aks create --resource-group rg-agency-marketing-production \
  --name aks-agency-marketing --node-count 3 --node-vm-size Standard_D4s_v3 \
  --enable-cluster-autoscaler --min-count 2 --max-count 10 \
  --generate-ssh-keys --attach-acr cragencymarketing

az aks get-credentials --resource-group rg-agency-marketing-production --name aks-agency-marketing

az postgres flexible-server create \
  --resource-group rg-agency-marketing-production --name psql-agency-marketing \
  --location eastus --version 16 --sku-name GP_Standard_D4s_v3 \
  --storage-size 128 --backup-retention 30 --high-availability ZoneRedundant

az postgres flexible-server db create \
  --resource-group rg-agency-marketing-production --server-name psql-agency-marketing \
  --database-name agency_data

az redis create --resource-group rg-agency-marketing-production \
  --name redis-agency-marketing --location eastus --sku Premium --vm-size P2 \
  --enable-non-ssl-port false

kubectl apply -f k8s/
```

## 5. Monitoring and Observability

### Prometheus ServiceMonitor

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: agency-marketing-metrics
  namespace: monitoring
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app: agency-marketing
  endpoints:
  - port: http
    path: /api/v1/metrics
    interval: 15s
    scrapeTimeout: 10s
  namespaceSelector:
    matchNames:
    - grc-claw
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Agency Marketing — Overview",
    "panels": [
      {
        "title": "Request Rate",
        "type": "timeseries",
        "targets": [{
          "expr": "rate(http_requests_total{service=\"agency-marketing\"}[5m])"
        }]
      },
      {
        "title": "Error Rate",
        "type": "timeseries",
        "targets": [{
          "expr": "rate(http_requests_total{service=\"agency-marketing\",status=~\"5..\"}[5m])"
        }]
      },
      {
        "title": "Latency P95",
        "type": "timeseries",
        "targets": [{
          "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{service=\"agency-marketing\"}[5m]))"
        }]
      },
      {
        "title": "CPU Usage",
        "type": "timeseries",
        "targets": [{
          "expr": "rate(container_cpu_usage_seconds_total{pod=~\"agency-marketing-.*\"}[5m])"
        }]
      },
      {
        "title": "Memory Usage",
        "type": "timeseries",
        "targets": [{
          "expr": "container_memory_working_set_bytes{pod=~\"agency-marketing-.*\"}"
        }]
      }
    ]
  }
}
```

### Health Check Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Liveness probe |
| `/api/v1/health/ready` | GET | Readiness probe |
| `/api/v1/metrics` | GET | Prometheus metrics |
| `/api/v1/status` | GET | Detailed service status |

### Log Aggregation

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: agency-marketing-fluent-bit-config
data:
  fluent-bit.conf: |
    [INPUT]
        Name              tail
        Path              /var/log/containers/agency-marketing-*.log
        Parser            docker
        Tag               agency-marketing
    [FILTER]
        Name              kubernetes
        Match             agency-marketing
        Kube_URL          https://kubernetes.default.svc:443
        Merge_Log         On
        Keep_Log          Off
    [OUTPUT]
        Name              opensearch
        Match             agency-marketing
        Host              opensearch-cluster
        Port              9200
        Index             agency-marketing-logs
        Type              _doc
        tls               On
        tls.verify        Off
```

## 6. Security

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: agency-marketing-network-policy
  namespace: grc-claw
spec:
  podSelector:
    matchLabels:
      app: agency-marketing
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    - podSelector:
        matchLabels:
          app: prometheus
    ports:
    - protocol: TCP
      port: 8037
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: agency-marketing-redis
    ports:
    - protocol: TCP
      port: 6379
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to: []
    ports:
    - protocol: TCP
      port: 443
    - protocol: TCP
      port: 80
```

### Pod Security Standards

```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: agency-marketing-psp
spec:
  privileged: false
  runAsUser:
    rule: MustRunAsNonRoot
  seLinux:
    rule: RunAsAny
  fsGroup:
    rule: RunAsAny
  volumes:
  - 'configMap'
  - 'emptyDir'
  - 'secret'
  - 'persistentVolumeClaim'
```

### Secrets Management

```bash
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: agency-marketing-external-secrets
  namespace: grc-claw
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  target:
    name: agency-marketing-secrets
  data:
  - secretKey: DATABASE_URL
    remoteRef:
      key: agency-marketing/database
      property: url
  - secretKey: REDIS_URL
    remoteRef:
      key: agency-marketing/redis
      property: value
  - secretKey: AGENCY_WHITE_LABEL_URL
    remoteRef:
      key: agency-marketing/agency_white_label_url
      property: value
  - secretKey: CLIENT_ISOLATION_RULES
    remoteRef:
      key: agency-marketing/client_isolation_rules
      property: value
  - secretKey: REPORTING_TEMPLATE_PATH
    remoteRef:
      key: agency-marketing/reporting_template_path
      property: value
  - secretKey: RESOURCE_PLANNING_URL
    remoteRef:
      key: agency-marketing/resource_planning_url
      property: value
```

## 7. Backup and Disaster Recovery

### Database Backup Strategy

```yaml
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: agency-marketing-daily-backup
  namespace: velero
spec:
  schedule: "0 2 * * *"
  template:
    includedNamespaces:
    - grc-claw
    includedResources:
    - persistentvolumeclaims
    - secrets
    - configmaps
    labelSelector:
      matchLabels:
        app: agency-marketing
    storageLocation: aws-default
    volumeSnapshotLocations:
    - aws-default
    ttl: 720h0m0s
```

### Point-in-Time Recovery

```bash
# AWS RDS
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier agency-marketing-db \
  --target-db-instance-identifier agency-marketing-db-recovery \
  --restore-time 2024-01-15T03:00:00Z

# GCP Cloud SQL
gcloud sql instances clone agency-marketing-db agency-marketing-db-recovery \
  --point-in-time="2024-01-15T03:00:00Z"
```

## 8. Compliance

- Client data segregation
- White-label branding rights
- Agency-client data agreements

### Data Classification

| Data Type | Classification | Handling |
|-----------|---------------|----------|
| Customer PII | Confidential | Encrypted at rest and in transit |
| Marketing metrics | Internal | Access-controlled |
| API keys | Secret | Secrets manager only |
| Logs | Internal | 90-day retention |

### Audit Logging

```yaml
apiVersion: audit.k8s.io/v1
kind: Policy
metadata:
  name: agency-marketing-audit-policy
rules:
- level: Metadata
  resources:
  - group: ""
    resources: ["secrets", "configmaps"]
- level: RequestResponse
  resources:
  - group: ""
    resources: ["pods", "services"]
  verbs: ["create", "update", "delete", "patch"]
```

## 9. Performance Tuning

### Database Optimization

```sql
-- Connection pooling (PgBouncer)
-- pgbouncer.ini
[databases]
agency_data = host=localhost port=5432 dbname=agency_data

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
reserve_pool_size = 5
```

### Caching Strategy

```python
CACHE_CONFIG = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://redis:6379/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {"max_connections": 50},
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
        },
        "TIMEOUT": 300,
        "KEY_PREFIX": "agency-marketing",
    }
}
```

### CDN Configuration

```hcl
resource "aws_cloudfront_distribution" "agency-marketing" {
  enabled             = true
  is_ipv6_enabled    = true
  default_root_object = "index.html"
  price_class         = "PriceClass_All"
  origin {
    domain_name = aws_lb.agency-marketing_alb.dns_name
    origin_id   = "agency-marketing-alb"
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "agency-marketing-alb"
    forwarded_values {
      query_string = true
      headers      = ["Origin", "Access-Control-Request-Headers", "Access-Control-Request-Method"]
      cookies {
        forward = "all"
      }
    }
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
    compress               = true
  }
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate.agency-marketing.arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }
}
```

## 10. Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Pod stuck in Pending | Insufficient resources | Check node capacity, scale cluster |
| CrashLoopBackOff | App startup failure | Check logs: `kubectl logs deploy/agency-marketing --previous` |
| High memory usage | Memory leak or undersized limit | Increase memory limit, profile application |
| Database connection timeout | Connection pool exhausted | Increase pool size, check PgBouncer |
| Slow API responses | Missing indexes or N+1 queries | Add database indexes, optimize queries |
| SSL certificate errors | Expired or misconfigured cert | Renew cert, check cert-manager logs |

### Debugging Commands

```bash
kubectl get pods -n grc-claw -l app=agency-marketing
kubectl logs -n grc-claw -l app=agency-marketing --tail=100 -f
kubectl exec -it -n grc-claw deploy/agency-marketing -- /bin/sh
kubectl get events -n grc-claw --sort-by='.lastTimestamp'
kubectl port-forward -n grc-claw svc/agency-marketing 8037:8037
kubectl top pods -n grc-claw -l app=agency-marketing
kubectl describe pod -n grc-claw -l app=agency-marketing
```

## 11. CI/CD Pipeline

### GitHub Actions

```yaml
name: Deploy Agency Marketing

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: grc-claw/agency-marketing

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.12'
    - run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    - run: pytest --cov=app --cov-report=xml

  security-scan:
    runs-on: ubuntu-latest
    needs: test
    steps:
    - uses: actions/checkout@v4
    - uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        format: 'sarif'
        output: 'trivy-results.sarif'

  build:
    runs-on: ubuntu-latest
    needs: [test, security-scan]
    permissions:
      contents: read
      packages: write
    steps:
    - uses: actions/checkout@v4
    - uses: docker/login-action@v3
      with:
        registry: ${ env.REGISTRY }
        username: ${ github.actor }
        password: ${ secrets.GITHUB_TOKEN }
    - uses: docker/metadata-action@v5
      with:
        images: ${ env.REGISTRY }/${ env.IMAGE_NAME }
    - uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: ${ steps.meta.outputs.tags }
        labels: ${ steps.meta.outputs.labels }
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy-staging:
    runs-on: ubuntu-latest
    needs: build
    environment: staging
    steps:
    - uses: actions/checkout@v4
    - uses: aws-actions/configure-aws-credentials@v4
      with:
        role-to-assume: ${ secrets.AWS_DEPLOY_ROLE_ARN }
        aws-region: us-east-1
    - run: |
        aws eks update-kubeconfig --name agency-marketing-staging
        kubectl set image deployment/agency-marketing agency-marketing=${ env.REGISTRY }/${ env.IMAGE_NAME }:${ github.sha } -n grc-claw-staging
        kubectl rollout status deployment/agency-marketing -n grc-claw-staging

  deploy-production:
    runs-on: ubuntu-latest
    needs: deploy-staging
    environment: production
    steps:
    - uses: actions/checkout@v4
    - uses: aws-actions/configure-aws-credentials@v4
      with:
        role-to-assume: ${ secrets.AWS_DEPLOY_ROLE_ARN }
        aws-region: us-east-1
    - run: |
        aws eks update-kubeconfig --name agency-marketing-production
        kubectl set image deployment/agency-marketing agency-marketing=${ env.REGISTRY }/${ env.IMAGE_NAME }:${ github.sha } -n grc-claw
        kubectl rollout status deployment/agency-marketing -n grc-claw
    - run: |
        kubectl run verify --rm -i --restart=Never --image=curlimages/curl -- curl -sf http://agency-marketing.grc-claw.svc.cluster.local/api/v1/health
```

## 12. Cost Optimization

### AWS Cost Optimization

| Service | Strategy | Estimated Savings |
|---------|----------|-------------------|
| EC2/EKS | Use Spot instances for non-critical workloads | 60-70% |
| RDS | Use Graviton instances, enable storage autoscaling | 20-30% |
| ElastiCache | Use reserved nodes for steady-state | 30-40% |
| ALB | Consolidate under shared ALB | 20-30% |
| CloudWatch | Use metric filters, reduce log retention | 10-20% |

### Resource Right-Sizing

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: agency-marketing-vpa
  namespace: grc-claw
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agency-marketing
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: agency-marketing
      minAllowed:
        cpu: 100m
        memory: 256Mi
      maxAllowed:
        cpu: 2000m
        memory: 4Gi
      controlledResources: ["cpu", "memory"]
```

## 13. Runbook

### Deployment Checklist

- [ ] All environment variables configured in secrets manager
- [ ] Database migrations applied
- [ ] Redis cluster healthy
- [ ] SSL certificates valid
- [ ] DNS records propagated
- [ ] Monitoring dashboards configured
- [ ] Alert rules active
- [ ] Backup schedule verified
- [ ] Runbook documentation updated
- [ ] On-call rotation notified
- [ ] Rollback plan documented

### Rollback Procedure

```bash
kubectl rollout undo deployment/agency-marketing -n grc-claw
kubectl rollout status deployment/agency-marketing -n grc-claw
kubectl get pods -n grc-claw -l app=agency-marketing
kubectl logs -n grc-claw -l app=agency-marketing --tail=50
```

### Incident Response

1. **Detect**: Alert fires (PagerDuty/Opsgenie)
2. **Acknowledge**: On-call engineer acknowledges within 5 minutes
3. **Mitigate**: Rollback or scale as needed
4. **Resolve**: Confirm service health restored
5. **Post-mortem**: Document within 24 hours

---

## Cloud Service Integrations

- AWS Organizations for multi-account
- Google Cloud SQL for client data
- Azure DevOps for project management

---

*Last updated: 2024-01-15 | Maintained by GRC-Claw Platform Team*
