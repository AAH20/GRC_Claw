# Lead Scorer — Deployment Guide

> **Version:** 1.0.0 | **Port:** 8002 | **Database:** lead_scores

## Overview

Machine learning lead scoring system that evaluates and ranks prospects based on behavioral signals, demographic data, and engagement patterns to prioritize sales efforts.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Load Balancer                     │
├─────────────────────────────────────────────────────┤
│              Lead Scorer Service                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │   API    │  │  Worker  │  │  Cache   │          │
│  │  Server  │  │  Queue   │  │  Layer   │          │
│  └──────────┘  └──────────┘  └──────────┘          │
├─────────────────────────────────────────────────────┤
│              PostgreSQL (lead_scores)                      │
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
| `SCORING_MODEL_PATH` | Yes | Environment-specific value |
| `CRM_SYNC_URL` | Yes | Environment-specific value |
| `LEAD_THRESHOLD` | Yes | Environment-specific value |
| `SCORE_DECAY_RATE` | Yes | Environment-specific value |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `LOG_LEVEL` | No | Logging level (default: INFO) |
| `METRICS_ENABLED` | No | Enable Prometheus metrics (default: true) |

## 1. Docker Deployment

### Quick Start

```bash
git clone https://github.com/GRC-Claw/lead-scorer.git
cd lead-scorer

cat > .env << 'EOF'
DATABASE_URL=postgresql://user:password@localhost:5432/lead_scores
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
EOF

docker build -t lead-scorer:latest .
docker run -d \
  --name lead-scorer \
  -p 8002:8002 \
  --env-file .env \
  --restart unless-stopped \
  lead-scorer:latest
```

### Docker Compose (Full Stack)

```yaml
version: "3.9"

services:
  lead-scorer:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8002:8002"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/lead_scores
      - REDIS_URL=redis://redis:6379/0
      - LOG_LEVEL=INFO
      - SCORING_MODEL_PATH=${SCORING_MODEL_PATH}
      - CRM_SYNC_URL=${CRM_SYNC_URL}
      - LEAD_THRESHOLD=${LEAD_THRESHOLD}
      - SCORE_DECAY_RATE=${SCORE_DECAY_RATE}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/api/v1/health"]
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
      POSTGRES_DB: lead_scores
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
docker compose logs -f lead-scorer
```

### Production Docker Run

```bash
docker run -d \
  --name lead-scorer \
  -p 8002:8002 \
  --env-file .env.production \
  --restart unless-stopped \
  --memory=2g \
  --cpus=1.0 \
  --log-driver=json-file \
  --log-opt max-size=100m \
  --log-opt max-file=5 \
  --security-opt=no-new-privileges \
  --cap-drop=ALL \
  ghcr.io/grc-claw/lead-scorer:v1.0.0
```

## 2. Kubernetes Deployment

### Namespace and Secrets

```bash
kubectl create namespace grc-claw
kubectl create secret generic lead-scorer-secrets \
  --from-literal=DATABASE_URL='postgresql://user:pass@postgres:5432/lead_scores' \
  --from-literal=REDIS_URL='redis://redis:6379/0' \
  --from-literal=SCORING_MODEL_PATH='your_value_here' \
  --from-literal=CRM_SYNC_URL='your_value_here' \
  --from-literal=LEAD_THRESHOLD='your_value_here' \
  --from-literal=SCORE_DECAY_RATE='your_value_here' \
  -n grc-claw
```

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lead-scorer
  namespace: grc-claw
  labels:
    app: lead-scorer
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
      app: lead-scorer
  template:
    metadata:
      labels:
        app: lead-scorer
        version: v1.0.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8002"
        prometheus.io/path: "/api/v1/metrics"
    spec:
      serviceAccountName: lead-scorer-sa
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: lead-scorer
        image: ghcr.io/grc-claw/lead-scorer:v1.0.0
        imagePullPolicy: Always
        ports:
        - containerPort: 8002
          protocol: TCP
        envFrom:
        - secretRef:
            name: lead-scorer-secrets
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
            port: 8002
          initialDelaySeconds: 30
          periodSeconds: 15
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8002
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        startupProbe:
          httpGet:
            path: /api/v1/health
            port: 8002
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
                  - lead-scorer
              topologyKey: topology.kubernetes.io/zone
```

### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: lead-scorer
  namespace: grc-claw
  labels:
    app: lead-scorer
spec:
  type: ClusterIP
  selector:
    app: lead-scorer
  ports:
  - port: 80
    targetPort: 8002
    protocol: TCP
    name: http
```

### Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: lead-scorer
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
    - lead-scorer.grc-claw.io
    secretName: lead-scorer-tls
  rules:
  - host: lead-scorer.grc-claw.io
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: lead-scorer
            port:
              number: 80
```

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: lead-scorer-hpa
  namespace: grc-claw
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: lead-scorer
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
  name: lead-scorer-pdb
  namespace: grc-claw
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: lead-scorer
```

### Redis Dependency

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lead-scorer-redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: lead-scorer-redis
  template:
    metadata:
      labels:
        app: lead-scorer-redis
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
  name: lead-scorer-redis
spec:
  selector:
    app: lead-scorer-redis
  ports:
  - port: 6379
```


### Background Worker (CronJob)

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: lead-scorer-worker
spec:
  schedule: "*/5 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: worker
            image: ghcr.io/grc-claw/lead-scorer:latest
            command: ["python", "-m", "worker"]
            envFrom:
            - secretRef:
                name: lead-scorer-secrets
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
helm install lead-scorer grc-claw/lead-scorer \
  --namespace grc-claw \
  --create-namespace \
  --set image.tag=v1.0.0 \
  --set replicaCount=3 \
  --set ingress.host=lead-scorer.grc-claw.io
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
    key            = "lead-scorer/terraform.tfstate"
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
  name = "lead-scorer-vpc"
  cidr = "10.0.0.0/16"
  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  enable_nat_gateway = true
  single_nat_gateway = false
  enable_vpn_gateway = false
  tags = {
    Name        = "lead-scorer-vpc"
    Environment = var.environment
    Project     = "GRC-Claw"
  }
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"
  cluster_name    = "lead-scorer-cluster"
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
        Name = "lead-scorer-worker"
      }
    }
  }
  tags = {
    Name        = "lead-scorer-cluster"
    Environment = var.environment
  }
}

resource "aws_db_instance" "lead-scorer_db" {
  identifier     = "lead-scorer-db"
  engine         = "postgres"
  engine_version = "16.1"
  instance_class = "db.r6g.xlarge"
  allocated_storage     = 100
  max_allocated_storage = 500
  storage_type          = "gp3"
  storage_encrypted     = true
  db_name  = "lead_scores"
  username = "grc_admin"
  password = random_password.db_password.result
  vpc_security_group_ids = [aws_security_group.db.id]
  db_subnet_group_name   = aws_db_subnet_group.lead-scorer.name
  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "Mon:04:00-Mon:05:00"
  deletion_protection = true
  skip_final_snapshot = false
  final_snapshot_identifier = "lead-scorer-final-snapshot"
  performance_insights_enabled = true
  tags = {
    Name        = "lead-scorer-db"
    Environment = var.environment
  }
}

resource "random_password" "db_password" {
  length  = 32
  special = false
}

resource "aws_elasticache_replication_group" "lead-scorer_redis" {
  replication_group_id = "lead-scorer-redis"
  description          = "Redis cluster for Lead Scorer"
  node_type            = "cache.r6g.large"
  num_cache_clusters   = 2
  automatic_failover_enabled = true
  multi_az_enabled     = true
  engine_version = "7.0"
  port          = 6379
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  subnet_group_name  = aws_elasticache_subnet_group.lead-scorer.name
  security_group_ids = [aws_security_group.redis.id]
  snapshot_retention_limit = 7
  snapshot_window         = "05:00-06:00"
  tags = {
    Name        = "lead-scorer-redis"
    Environment = var.environment
  }
}

resource "aws_lb" "lead-scorer_alb" {
  name               = "lead-scorer-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = module.vpc.public_subnets
  enable_deletion_protection = true
  enable_http2             = true
  tags = {
    Name        = "lead-scorer-alb"
    Environment = var.environment
  }
}

resource "aws_lb_target_group" "lead-scorer_tg" {
  name     = "lead-scorer-tg"
  port     = 8002
  protocol = "HTTP"
  vpc_id   = module.vpc.vpc_id
  health_check {
    path                = "/api/v1/health"
    port                = "8002"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
  }
  deregistration_delay = 30
}

resource "aws_lb_listener" "lead-scorer_https" {
  load_balancer_arn = aws_lb.lead-scorer_alb.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate.lead-scorer.arn
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.lead-scorer_tg.arn
  }
}

resource "aws_ecs_cluster" "lead-scorer" {
  name = "lead-scorer-cluster"
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  tags = {
    Name        = "lead-scorer-cluster"
    Environment = var.environment
  }
}

resource "aws_ecs_task_definition" "lead-scorer" {
  family                   = "lead-scorer"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn           = aws_iam_role.ecs_task.arn
  container_definitions = jsonencode([{
    name  = "lead-scorer"
    image = "ghcr.io/grc-claw/lead-scorer:v1.0.0"
    essential = true
    portMappings = [{
      containerPort = 8002
      protocol      = "tcp"
    }]
    environment = [
      { name = "LOG_LEVEL", value = "INFO" },
      { name = "METRICS_ENABLED", value = "true" },
  { name = "SCORING_MODEL_PATH", value = "placeholder" },
  { name = "CRM_SYNC_URL", value = "placeholder" },
  { name = "LEAD_THRESHOLD", value = "placeholder" },
  { name = "SCORE_DECAY_RATE", value = "placeholder" },
    ]
    secrets = [
      {
        name      = "DATABASE_URL"
        valueFrom = aws_secretsmanager_secret.lead-scorer_db.arn
      },
      {
        name      = "REDIS_URL"
        valueFrom = aws_secretsmanager_secret.lead-scorer_redis.arn
      }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.lead-scorer.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
    healthCheck = {
      command     = ["CMD-SHELL", "curl -f http://localhost:8002/api/v1/health || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 60
    }
  }])
}

resource "aws_ecs_service" "lead-scorer" {
  name            = "lead-scorer"
  cluster         = aws_ecs_cluster.lead-scorer.id
  task_definition = aws_ecs_task_definition.lead-scorer.arn
  desired_count   = 3
  launch_type     = "FARGATE"
  network_configuration {
    subnets          = module.vpc.private_subnets
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = false
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.lead-scorer_tg.arn
    container_name   = "lead-scorer"
    container_port   = 8002
  }
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
  propagate_tags = "SERVICE"
  tags = {
    Name        = "lead-scorer"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_metric_alarm" "lead-scorer_cpu" {
  alarm_name          = "lead-scorer-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 80
  alarm_actions       = [aws_sns_topic.lead-scorer_alerts.arn]
  dimensions = {
    ServiceName = "lead-scorer"
    ClusterName = "lead-scorer-cluster"
  }
}

resource "aws_cloudwatch_metric_alarm" "lead-scorer_memory" {
  alarm_name          = "lead-scorer-high-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 85
  alarm_actions       = [aws_sns_topic.lead-scorer_alerts.arn]
  dimensions = {
    ServiceName = "lead-scorer"
    ClusterName = "lead-scorer-cluster"
  }
}

output "alb_dns_name" {
  value = aws_lb.lead-scorer_alb.dns_name
}

output "db_endpoint" {
  value     = aws_db_instance.lead-scorer_db.endpoint
  sensitive = true
}

output "redis_endpoint" {
  value     = aws_elasticache_replication_group.lead-scorer_redis.primary_endpoint_address
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

resource "google_compute_network" "lead-scorer_vpc" {
  name                    = "lead-scorer-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "lead-scorer_subnet" {
  name          = "lead-scorer-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.gcp_region
  network       = google_compute_network.lead-scorer_vpc.id
  private_ip_google_access = true
  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling       = 0.5
    metadata            = "INCLUDE_ALL_METADATA"
  }
}

resource "google_container_cluster" "lead-scorer" {
  name     = "lead-scorer-cluster"
  location = var.gcp_region
  network    = google_compute_network.lead-scorer_vpc.name
  subnetwork = google_compute_subnetwork.lead-scorer_subnet.name
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

resource "google_container_node_pool" "lead-scorer_nodes" {
  name       = "lead-scorer-node-pool"
  location   = var.gcp_region
  cluster    = google_container_cluster.lead-scorer.name
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
    service_account = google_service_account.lead-scorer.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
    labels = {
      workload = "general"
    }
    tags = ["lead-scorer-node"]
    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }
  }
}

resource "google_sql_database_instance" "lead-scorer" {
  name             = "lead-scorer-db"
  database_version = "POSTGRES_16"
  region           = var.gcp_region
  settings {
    tier              = "db-custom-4-16384"
    availability_type = "REGIONAL"
    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.lead-scorer_vpc.id
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

resource "google_sql_database" "lead_scores" {
  name     = "lead_scores"
  instance = google_sql_database_instance.lead-scorer.name
}

resource "google_redis_instance" "lead-scorer" {
  name               = "lead-scorer-redis"
  tier               = "STANDARD_HA"
  memory_size_gb     = 5
  region             = var.gcp_region
  authorized_network = google_compute_network.lead-scorer_vpc.id
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

resource "google_cloud_run_v2_service" "lead-scorer" {
  name     = "lead-scorer"
  location = var.gcp_region
  ingress  = "INGRESS_TRAFFIC_ALL"
  template {
    service_account = google_service_account.lead-scorer.email
    vpc_access {
      connector = google_vpc_access_connector.lead-scorer.id
      egress    = "ALL_TRAFFIC"
    }
    containers {
      image = "ghcr.io/grc-claw/lead-scorer:v1.0.0"
      ports {
        container_port = 8002
      }
      env {
        name  = "DATABASE_URL"
        value = "postgresql://user:pass@/lead_scores?host=/cloudsql/${google_sql_database_instance.lead-scorer.connection_name}"
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
          port = 8002
        }
        initial_delay_seconds = 10
        period_seconds        = 5
        failure_threshold     = 30
        timeout_seconds       = 5
      }
      liveness_probe {
        http_get {
          path = "/api/v1/health"
          port = 8002
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
  value = google_cloud_run_v2_service.lead-scorer.uri
}

output "db_connection_name" {
  value = google_sql_database_instance.lead-scorer.connection_name
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

resource "azurerm_resource_group" "lead-scorer" {
  name     = "rg-lead-scorer-${var.environment}"
  location = var.azure_region
  tags = {
    Project     = "GRC-Claw"
    Environment = var.environment
    Service     = "Lead Scorer"
  }
}

resource "azurerm_virtual_network" "lead-scorer" {
  name                = "vnet-lead-scorer"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.lead-scorer.location
  resource_group_name = azurerm_resource_group.lead-scorer.name
}

resource "azurerm_subnet" "lead-scorer_aks" {
  name                 = "snet-aks"
  resource_group_name  = azurerm_resource_group.lead-scorer.name
  virtual_network_name = azurerm_virtual_network.lead-scorer.name
  address_prefixes     = ["10.0.1.0/24"]
}

resource "azurerm_subnet" "lead-scorer_db" {
  name                 = "snet-db"
  resource_group_name  = azurerm_resource_group.lead-scorer.name
  virtual_network_name = azurerm_virtual_network.lead-scorer.name
  address_prefixes     = ["10.0.2.0/24"]
  delegation {
    name = "postgresql"
    service_delegation {
      name    = "Microsoft.DBforPostgreSQL/flexibleServers"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
    }
  }
}

resource "azurerm_kubernetes_cluster" "lead-scorer" {
  name                = "aks-lead-scorer"
  location            = azurerm_resource_group.lead-scorer.location
  resource_group_name = azurerm_resource_group.lead-scorer.name
  dns_prefix          = "lead-scorer-aks"
  kubernetes_version  = "1.28"
  default_node_pool {
    name       = "general"
    node_count = 3
    vm_size    = "Standard_D4s_v3"
    vnet_subnet_id = azurerm_subnet.lead-scorer_aks.id
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
    log_analytics_workspace_id = azurerm_log_analytics_workspace.lead-scorer.id
  }
  tags = {
    Environment = var.environment
  }
}

resource "azurerm_postgresql_flexible_server" "lead-scorer" {
  name                = "psql-lead-scorer"
  resource_group_name = azurerm_resource_group.lead-scorer.name
  location            = azurerm_resource_group.lead-scorer.location
  version    = "16"
  sku_name   = "GP_Standard_D4s_v3"
  storage_mb = 131072
  backup_retention_days        = 30
  geo_redundant_backup_enabled = true
  delegated_subnet_id = azurerm_subnet.lead-scorer_db.id
  private_dns_zone_id = azurerm_private_dns_zone.lead-scorer.id
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

resource "azurerm_postgresql_flexible_server_database" "lead_scores" {
  name      = "lead_scores"
  server_id = azurerm_postgresql_flexible_server.lead-scorer.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

resource "azurerm_redis_cache" "lead-scorer" {
  name                = "redis-lead-scorer"
  location            = azurerm_resource_group.lead-scorer.location
  resource_group_name = azurerm_resource_group.lead-scorer.name
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

resource "azurerm_container_registry" "lead-scorer" {
  name                = "crleadscorer"
  resource_group_name = azurerm_resource_group.lead-scorer.name
  location            = azurerm_resource_group.lead-scorer.location
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

resource "azurerm_log_analytics_workspace" "lead-scorer" {
  name                = "law-lead-scorer"
  location            = azurerm_resource_group.lead-scorer.location
  resource_group_name = azurerm_resource_group.lead-scorer.name
  sku                 = "PerGB2018"
  retention_in_days   = 90
}

resource "azurerm_application_insights" "lead-scorer" {
  name                = "ai-lead-scorer"
  location            = azurerm_resource_group.lead-scorer.location
  resource_group_name = azurerm_resource_group.lead-scorer.name
  workspace_id        = azurerm_log_analytics_workspace.lead-scorer.id
  application_type    = "web"
}

output "aks_cluster_name" {
  value = azurerm_kubernetes_cluster.lead-scorer.name
}

output "postgres_fqdn" {
  value     = azurerm_postgresql_flexible_server.lead-scorer.fqdn
  sensitive = true
}

output "redis_hostname" {
  value = azurerm_redis_cache.lead-scorer.hostname
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
   aws ecr create-repository --repository-name lead-scorer --region us-east-1
   ```

2. **Push Docker Image**
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com
   docker build -t lead-scorer .
   docker tag lead-scorer:latest $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com/lead-scorer:v1.0.0
   docker push $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com/lead-scorer:v1.0.0
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

class LeadScorerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        vpc = ec2.Vpc(self, "VPC", max_azs=3)
        cluster = ecs.Cluster(self, "Cluster", vpc=vpc)
        repository = ecr.Repository(self, "Repo",
            repository_name="lead-scorer",
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
            deletion_protection=True, database_name="lead_scores"
        )
        service = ecs_patterns.ApplicationLoadBalancedFargateService(self, "Service",
            cluster=cluster, cpu=1024, memory_limit_mib=2048,
            desired_count=3,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_ecr_repository(repository, "v1.0.0"),
                container_port=8002,
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

gcloud container clusters create lead-scorer-cluster \
  --region=us-central1 --num-nodes=3 --machine-type=n2-standard-4 \
  --enable-autoscaling --min-nodes=2 --max-nodes=10 \
  --enable-network-policy --enable-autoupgrade --enable-autorepair \
  --workload-pool=YOUR_PROJECT_ID.svc.id.goog

gcloud sql instances create lead-scorer-db \
  --database-version=POSTGRES_16 --tier=db-custom-4-16384 \
  --region=us-central1 --availability-type=regional \
  --storage-auto-increase --backup-start-time=03:00 \
  --enable-point-in-time-recovery

gcloud sql databases create lead_scores --instance=lead-scorer-db

gcloud redis instances create lead-scorer-redis \
  --size=5 --region=us-central1 --zone=us-central1-a \
  --network=default --tier=standard

gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/lead-scorer:v1.0.0

gcloud run deploy lead-scorer \
  --image=gcr.io/YOUR_PROJECT_ID/lead-scorer:v1.0.0 \
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
az group create --name rg-lead-scorer-production --location eastus

az acr create --resource-group rg-lead-scorer-production \
  --name crleadscorer --sku Premium --location eastus

az acr build --registry crleadscorer --image lead-scorer:v1.0.0 .

az aks create --resource-group rg-lead-scorer-production \
  --name aks-lead-scorer --node-count 3 --node-vm-size Standard_D4s_v3 \
  --enable-cluster-autoscaler --min-count 2 --max-count 10 \
  --generate-ssh-keys --attach-acr crleadscorer

az aks get-credentials --resource-group rg-lead-scorer-production --name aks-lead-scorer

az postgres flexible-server create \
  --resource-group rg-lead-scorer-production --name psql-lead-scorer \
  --location eastus --version 16 --sku-name GP_Standard_D4s_v3 \
  --storage-size 128 --backup-retention 30 --high-availability ZoneRedundant

az postgres flexible-server db create \
  --resource-group rg-lead-scorer-production --server-name psql-lead-scorer \
  --database-name lead_scores

az redis create --resource-group rg-lead-scorer-production \
  --name redis-lead-scorer --location eastus --sku Premium --vm-size P2 \
  --enable-non-ssl-port false

kubectl apply -f k8s/
```

## 5. Monitoring and Observability

### Prometheus ServiceMonitor

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: lead-scorer-metrics
  namespace: monitoring
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app: lead-scorer
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
    "title": "Lead Scorer — Overview",
    "panels": [
      {
        "title": "Request Rate",
        "type": "timeseries",
        "targets": [{
          "expr": "rate(http_requests_total{service=\"lead-scorer\"}[5m])"
        }]
      },
      {
        "title": "Error Rate",
        "type": "timeseries",
        "targets": [{
          "expr": "rate(http_requests_total{service=\"lead-scorer\",status=~\"5..\"}[5m])"
        }]
      },
      {
        "title": "Latency P95",
        "type": "timeseries",
        "targets": [{
          "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{service=\"lead-scorer\"}[5m]))"
        }]
      },
      {
        "title": "CPU Usage",
        "type": "timeseries",
        "targets": [{
          "expr": "rate(container_cpu_usage_seconds_total{pod=~\"lead-scorer-.*\"}[5m])"
        }]
      },
      {
        "title": "Memory Usage",
        "type": "timeseries",
        "targets": [{
          "expr": "container_memory_working_set_bytes{pod=~\"lead-scorer-.*\"}"
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
  name: lead-scorer-fluent-bit-config
data:
  fluent-bit.conf: |
    [INPUT]
        Name              tail
        Path              /var/log/containers/lead-scorer-*.log
        Parser            docker
        Tag               lead-scorer
    [FILTER]
        Name              kubernetes
        Match             lead-scorer
        Kube_URL          https://kubernetes.default.svc:443
        Merge_Log         On
        Keep_Log          Off
    [OUTPUT]
        Name              opensearch
        Match             lead-scorer
        Host              opensearch-cluster
        Port              9200
        Index             lead-scorer-logs
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
  name: lead-scorer-network-policy
  namespace: grc-claw
spec:
  podSelector:
    matchLabels:
      app: lead-scorer
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
      port: 8002
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: lead-scorer-redis
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
  name: lead-scorer-psp
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
  name: lead-scorer-external-secrets
  namespace: grc-claw
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  target:
    name: lead-scorer-secrets
  data:
  - secretKey: DATABASE_URL
    remoteRef:
      key: lead-scorer/database
      property: url
  - secretKey: REDIS_URL
    remoteRef:
      key: lead-scorer/redis
      property: value
  - secretKey: SCORING_MODEL_PATH
    remoteRef:
      key: lead-scorer/scoring_model_path
      property: value
  - secretKey: CRM_SYNC_URL
    remoteRef:
      key: lead-scorer/crm_sync_url
      property: value
  - secretKey: LEAD_THRESHOLD
    remoteRef:
      key: lead-scorer/lead_threshold
      property: value
  - secretKey: SCORE_DECAY_RATE
    remoteRef:
      key: lead-scorer/score_decay_rate
      property: value
```

## 7. Backup and Disaster Recovery

### Database Backup Strategy

```yaml
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: lead-scorer-daily-backup
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
        app: lead-scorer
    storageLocation: aws-default
    volumeSnapshotLocations:
    - aws-default
    ttl: 720h0m0s
```

### Point-in-Time Recovery

```bash
# AWS RDS
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier lead-scorer-db \
  --target-db-instance-identifier lead-scorer-db-recovery \
  --restore-time 2024-01-15T03:00:00Z

# GCP Cloud SQL
gcloud sql instances clone lead-scorer-db lead-scorer-db-recovery \
  --point-in-time="2024-01-15T03:00:00Z"
```

## 8. Compliance

- GDPR right to explanation
- Data retention policies
- Consent tracking

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
  name: lead-scorer-audit-policy
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
lead_scores = host=localhost port=5432 dbname=lead_scores

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
        "KEY_PREFIX": "lead-scorer",
    }
}
```

### CDN Configuration

```hcl
resource "aws_cloudfront_distribution" "lead-scorer" {
  enabled             = true
  is_ipv6_enabled    = true
  default_root_object = "index.html"
  price_class         = "PriceClass_All"
  origin {
    domain_name = aws_lb.lead-scorer_alb.dns_name
    origin_id   = "lead-scorer-alb"
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
    target_origin_id = "lead-scorer-alb"
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
    acm_certificate_arn      = aws_acm_certificate.lead-scorer.arn
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
| CrashLoopBackOff | App startup failure | Check logs: `kubectl logs deploy/lead-scorer --previous` |
| High memory usage | Memory leak or undersized limit | Increase memory limit, profile application |
| Database connection timeout | Connection pool exhausted | Increase pool size, check PgBouncer |
| Slow API responses | Missing indexes or N+1 queries | Add database indexes, optimize queries |
| SSL certificate errors | Expired or misconfigured cert | Renew cert, check cert-manager logs |

### Debugging Commands

```bash
kubectl get pods -n grc-claw -l app=lead-scorer
kubectl logs -n grc-claw -l app=lead-scorer --tail=100 -f
kubectl exec -it -n grc-claw deploy/lead-scorer -- /bin/sh
kubectl get events -n grc-claw --sort-by='.lastTimestamp'
kubectl port-forward -n grc-claw svc/lead-scorer 8002:8002
kubectl top pods -n grc-claw -l app=lead-scorer
kubectl describe pod -n grc-claw -l app=lead-scorer
```

## 11. CI/CD Pipeline

### GitHub Actions

```yaml
name: Deploy Lead Scorer

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: grc-claw/lead-scorer

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
        aws eks update-kubeconfig --name lead-scorer-staging
        kubectl set image deployment/lead-scorer lead-scorer=${ env.REGISTRY }/${ env.IMAGE_NAME }:${ github.sha } -n grc-claw-staging
        kubectl rollout status deployment/lead-scorer -n grc-claw-staging

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
        aws eks update-kubeconfig --name lead-scorer-production
        kubectl set image deployment/lead-scorer lead-scorer=${ env.REGISTRY }/${ env.IMAGE_NAME }:${ github.sha } -n grc-claw
        kubectl rollout status deployment/lead-scorer -n grc-claw
    - run: |
        kubectl run verify --rm -i --restart=Never --image=curlimages/curl -- curl -sf http://lead-scorer.grc-claw.svc.cluster.local/api/v1/health
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
  name: lead-scorer-vpa
  namespace: grc-claw
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: lead-scorer
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: lead-scorer
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
kubectl rollout undo deployment/lead-scorer -n grc-claw
kubectl rollout status deployment/lead-scorer -n grc-claw
kubectl get pods -n grc-claw -l app=lead-scorer
kubectl logs -n grc-claw -l app=lead-scorer --tail=50
```

### Incident Response

1. **Detect**: Alert fires (PagerDuty/Opsgenie)
2. **Acknowledge**: On-call engineer acknowledges within 5 minutes
3. **Mitigate**: Rollback or scale as needed
4. **Resolve**: Confirm service health restored
5. **Post-mortem**: Document within 24 hours

---

## Cloud Service Integrations

- AWS SageMaker for model hosting
- Google BigQuery for feature store
- Azure Data Lake for historical scoring

---

*Last updated: 2024-01-15 | Maintained by GRC-Claw Platform Team*
