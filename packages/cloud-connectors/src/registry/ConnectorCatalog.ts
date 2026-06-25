export type ConnectorProvider =
  | "aws"
  | "azure"
  | "gcp"
  | "github"
  | "okta"
  | "cloudflare"
  | "datadog"
  | "splunk"
  | "jira"
  | "slack"
  | "salesforce"
  | "snowflake"
  | "mongodb"
  | "redis";

export type ConnectorCategory =
  | "security"
  | "compliance"
  | "identity"
  | "devops"
  | "data"
  | "network"
  | "storage"
  | "compute";

export type AuthType = "api_key" | "oauth2" | "bearer" | "basic" | "aws_sigv4" | "service_account";

export interface ConnectorDefinition {
  id: string;
  name: string;
  provider: ConnectorProvider;
  category: ConnectorCategory;
  apiEndpoint: string;
  authType: AuthType;
  evidenceTypes: string[];
  frameworks: string[];
  description: string;
}

export const CONNECTOR_CATALOG: ConnectorDefinition[] = [
  // ──────────────────────────────────────────────
  // AWS (20 connectors)
  // ──────────────────────────────────────────────
  {
    id: "aws-iam",
    name: "AWS IAM",
    provider: "aws",
    category: "identity",
    apiEndpoint: "https://iam.{region}.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["policy_audit", "access_review", "mfa_status", "credential_rotation"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF", "CIS AWS"],
    description: "Identity and Access Management — policies, roles, users, groups, MFA, credential reports",
  },
  {
    id: "aws-s3",
    name: "AWS S3",
    provider: "aws",
    category: "storage",
    apiEndpoint: "https://s3.{region}.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["bucket_policy", "encryption_status", "public_access", "versioning", "logging"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF", "HIPAA", "PCI DSS"],
    description: "Simple Storage Service — bucket configs, encryption, public access, lifecycle policies",
  },
  {
    id: "aws-ec2",
    name: "AWS EC2",
    provider: "aws",
    category: "compute",
    apiEndpoint: "https://ec2.{region}.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["instance_inventory", "security_group", "patch_status", "ebs_encryption"],
    frameworks: ["SOC 2", "ISO 27001", "CIS AWS", "PCI DSS"],
    description: "Elastic Compute Cloud — instances, AMIs, security groups, EBS volumes",
  },
  {
    id: "aws-rds",
    name: "AWS RDS",
    provider: "aws",
    category: "data",
    apiEndpoint: "https://rds.{region}.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["db_inventory", "encryption", "backup_status", "access_logs", "parameter_groups"],
    frameworks: ["SOC 2", "ISO 27001", "HIPAA", "PCI DSS"],
    description: "Relational Database Service — instances, snapshots, encryption, parameter groups",
  },
  {
    id: "aws-cloudtrail",
    name: "AWS CloudTrail",
    provider: "aws",
    category: "security",
    apiEndpoint: "https://cloudtrail.{region}.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["audit_log", "api_call", "event_history", "trail_config"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF", "CIS AWS", "PCI DSS", "HIPAA"],
    description: "Cloud audit trail — API activity logging, event selectors, trail configurations",
  },
  {
    id: "aws-guardduty",
    name: "AWS GuardDuty",
    provider: "aws",
    category: "security",
    apiEndpoint: "https://guardduty.{region}.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["threat_finding", "anomaly_detection", "malware_indicator", "unauthorized_access"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF"],
    description: "Threat detection — ML-based anomaly, malware detection, unauthorized API calls",
  },
  {
    id: "aws-security-hub",
    name: "AWS Security Hub",
    provider: "aws",
    category: "security",
    apiEndpoint: "https://securityhub.{region}.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["security_score", "compliance_finding", "control_status", "aggregated_finding"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF", "CIS AWS"],
    description: "Security posture aggregation — compliance scores, ASFF findings, control status",
  },
  {
    id: "aws-waf",
    name: "AWS WAF",
    provider: "aws",
    category: "network",
    apiEndpoint: "https://wafv2.{region}.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["web_acl_config", "rule_status", "request_metric", "blocked_request"],
    frameworks: ["SOC 2", "ISO 27001", "PCI DSS"],
    description: "Web Application Firewall — WAF rules, rate limiting, managed rule groups",
  },
  {
    id: "aws-shield",
    name: "AWS Shield",
    provider: "aws",
    category: "network",
    apiEndpoint: "https://shield.{region}.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["ddos_protection", "attack_mitigation", "protection_group"],
    frameworks: ["SOC 2", "ISO 27001"],
    description: "DDoS protection — Advanced Shield protections, attack reports, proactive engage",
  },
  {
    id: "aws-kms",
    name: "AWS KMS",
    provider: "aws",
    category: "security",
    apiEndpoint: "https://kms.{region}.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["key_policy", "key_rotation", "key_usage", "alias_config"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF", "PCI DSS", "HIPAA"],
    description: "Key Management Service — encryption keys, policies, rotation, grants",
  },
  {
    id: "aws-vpc",
    name: "AWS VPC",
    provider: "aws",
    category: "network",
    apiEndpoint: "https://ec2.{region}.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["vpc_config", "subnet_config", "route_table", "flow_log", "nacl"],
    frameworks: ["SOC 2", "ISO 27001", "CIS AWS"],
    description: "Virtual Private Cloud — subnets, routing, NACLs, flow logs, endpoints",
  },
  {
    id: "aws-lambda",
    name: "AWS Lambda",
    provider: "aws",
    category: "compute",
    apiEndpoint: "https://lambda.{region}.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["function_config", "layer_version", "environment_variable", "execution_role"],
    frameworks: ["SOC 2", "ISO 27001"],
    description: "Serverless functions — runtime config, layers, environment, IAM execution roles",
  },
  {
    id: "aws-ecs",
    name: "AWS ECS",
    provider: "aws",
    category: "compute",
    apiEndpoint: "https://ecs.{region}.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["cluster_config", "task_definition", "service_status", "container_insights"],
    frameworks: ["SOC 2", "ISO 27001", "CIS AWS"],
    description: "Elastic Container Service — clusters, task definitions, services, container insights",
  },
  {
    id: "aws-eks",
    name: "AWS EKS",
    provider: "aws",
    category: "compute",
    apiEndpoint: "https://eks.{region}.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["cluster_config", "node_group", "addon_status", "rbac_audit"],
    frameworks: ["SOC 2", "ISO 27001", "CIS AWS"],
    description: "Elastic Kubernetes Service — clusters, managed node groups, add-ons, RBAC",
  },
  {
    id: "aws-dynamodb",
    name: "AWS DynamoDB",
    provider: "aws",
    category: "data",
    apiEndpoint: "https://dynamodb.{region}.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["table_config", "encryption", "backup_status", "pitr_status"],
    frameworks: ["SOC 2", "ISO 27001", "HIPAA"],
    description: "NoSQL database — tables, capacity, encryption, backups, global tables",
  },
  {
    id: "aws-sqs",
    name: "AWS SQS",
    provider: "aws",
    category: "data",
    apiEndpoint: "https://sqs.{region}.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["queue_config", "policy_audit", "dead_letter", "encryption"],
    frameworks: ["SOC 2", "ISO 27001"],
    description: "Simple Queue Service — queue policies, encryption, DLQ, access controls",
  },
  {
    id: "aws-sns",
    name: "AWS SNS",
    provider: "aws",
    category: "data",
    apiEndpoint: "https://sns.{region}.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["topic_config", "subscription_policy", "encryption"],
    frameworks: ["SOC 2", "ISO 27001"],
    description: "Simple Notification Service — topics, subscriptions, access policies",
  },
  {
    id: "aws-route53",
    name: "AWS Route 53",
    provider: "aws",
    category: "network",
    apiEndpoint: "https://route53.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["dns_config", "health_check", "domain_transfer_lock"],
    frameworks: ["SOC 2", "ISO 27001"],
    description: "DNS service — hosted zones, health checks, domain registration, DNSSEC",
  },
  {
    id: "aws-cloudfront",
    name: "AWS CloudFront",
    provider: "aws",
    category: "network",
    apiEndpoint: "https://cloudfront.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["distribution_config", "waf_association", "origin_access", "ssl_cert"],
    frameworks: ["SOC 2", "ISO 27001", "PCI DSS"],
    description: "CDN — distributions, WAF associations, origin access, TLS configurations",
  },
  {
    id: "aws-organizations",
    name: "AWS Organizations",
    provider: "aws",
    category: "compliance",
    apiEndpoint: "https://organizations.{region}.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["ou_structure", "scp_policy", "account_baseline", "cloudtrail_org"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF", "CIS AWS"],
    description: "Multi-account governance — OUs, SCPs, consolidated billing, control tower",
  },

  // ──────────────────────────────────────────────
  // Azure (15 connectors)
  // ──────────────────────────────────────────────
  {
    id: "azure-sentinel",
    name: "Microsoft Sentinel",
    provider: "azure",
    category: "security",
    apiEndpoint: "https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/{rg}/providers/Microsoft.OperationalInsights/workspaces/{workspace}",
    authType: "oauth2",
    evidenceTypes: ["alert", "incident", "hunting_query", "automation_rule", "entity"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF", "MITRE ATT&CK"],
    description: "Cloud-native SIEM — analytics rules, incidents, workbooks, automation",
  },
  {
    id: "azure-defender",
    name: "Microsoft Defender for Cloud",
    provider: "azure",
    category: "security",
    apiEndpoint: "https://management.azure.com/subscriptions/{subscriptionId}/providers/Microsoft.Security",
    authType: "oauth2",
    evidenceTypes: ["secure_score", "recommendation", "assessment", "regulatory_compliance"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF", "CIS Azure"],
    description: "CSPM and CWPP — secure scores, regulatory compliance, workload protections",
  },
  {
    id: "azure-ad",
    name: "Azure Active Directory",
    provider: "azure",
    category: "identity",
    apiEndpoint: "https://graph.microsoft.com/v1.0",
    authType: "oauth2",
    evidenceTypes: ["user_inventory", "mfa_status", "conditional_access", "risk_user", "app_registration"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF", "CIS Azure", "HIPAA"],
    description: "Identity platform — users, groups, MFA, conditional access, risky sign-ins",
  },
  {
    id: "azure-storage",
    name: "Azure Blob Storage",
    provider: "azure",
    category: "storage",
    apiEndpoint: "https://management.azure.com/subscriptions/{subscriptionId}/providers/Microsoft.Storage",
    authType: "oauth2",
    evidenceTypes: ["account_config", "encryption", "access_tier", "soft_delete", "public_access"],
    frameworks: ["SOC 2", "ISO 27001", "HIPAA", "PCI DSS"],
    description: "Object storage — accounts, containers, encryption, soft delete, lifecycle policies",
  },
  {
    id: "azure-sql",
    name: "Azure SQL Database",
    provider: "azure",
    category: "data",
    apiEndpoint: "https://management.azure.com/subscriptions/{subscriptionId}/providers/Microsoft.Sql",
    authType: "oauth2",
    evidenceTypes: ["server_config", "firewall_rule", "audit_setting", "tde_status", "vulnerability"],
    frameworks: ["SOC 2", "ISO 27001", "HIPAA", "PCI DSS"],
    description: "Managed SQL — server configs, auditing, TDE, vulnerability assessments",
  },
  {
    id: "azure-keyvault",
    name: "Azure Key Vault",
    provider: "azure",
    category: "security",
    apiEndpoint: "https://management.azure.com/subscriptions/{subscriptionId}/providers/Microsoft.KeyVault",
    authType: "oauth2",
    evidenceTypes: ["vault_config", "key_rotation", "secret_expiry", "access_policy", "purge_protection"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF", "PCI DSS", "HIPAA"],
    description: "Key management — vaults, keys, secrets, certificates, access policies",
  },
  {
    id: "azure-monitor",
    name: "Azure Monitor",
    provider: "azure",
    category: "security",
    apiEndpoint: "https://management.azure.com/subscriptions/{subscriptionId}/providers/Microsoft.Insights",
    authType: "oauth2",
    evidenceTypes: ["diagnostic_setting", "alert_rule", "activity_log", "metric"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF"],
    description: "Observability platform — diagnostics, alerts, metrics, activity logs",
  },
  {
    id: "azure-nsg",
    name: "Azure NSG",
    provider: "azure",
    category: "network",
    apiEndpoint: "https://management.azure.com/subscriptions/{subscriptionId}/providers/Microsoft.Network/networkSecurityGroups",
    authType: "oauth2",
    evidenceTypes: ["security_rule", "flow_log", "effective_rule", "association"],
    frameworks: ["SOC 2", "ISO 27001", "CIS Azure"],
    description: "Network Security Groups — inbound/outbound rules, flow logs, effective rules",
  },
  {
    id: "azure-appservice",
    name: "Azure App Service",
    provider: "azure",
    category: "compute",
    apiEndpoint: "https://management.azure.com/subscriptions/{subscriptionId}/providers/Microsoft.Web",
    authType: "oauth2",
    evidenceTypes: ["site_config", "ssl_binding", "auth_setting", "backup_config", "network_config"],
    frameworks: ["SOC 2", "ISO 27001", "PCI DSS"],
    description: "Web apps and APIs — site configs, TLS, authentication, deployment slots",
  },
  {
    id: "azure-cosmosdb",
    name: "Azure Cosmos DB",
    provider: "azure",
    category: "data",
    apiEndpoint: "https://management.azure.com/subscriptions/{subscriptionId}/providers/Microsoft.DocumentDB",
    authType: "oauth2",
    evidenceTypes: ["account_config", "consistency_level", "firewall_config", "diagnostic_log"],
    frameworks: ["SOC 2", "ISO 27001", "HIPAA"],
    description: "Multi-model database — accounts, consistency, IP rules, multi-region writes",
  },
  {
    id: "azure-aks",
    name: "Azure Kubernetes Service",
    provider: "azure",
    category: "compute",
    apiEndpoint: "https://management.azure.com/subscriptions/{subscriptionId}/providers/Microsoft.ContainerService/managedClusters",
    authType: "oauth2",
    evidenceTypes: ["cluster_config", "rbac_config", "network_policy", "addon_status"],
    frameworks: ["SOC 2", "ISO 27001", "CIS Azure"],
    description: "Managed Kubernetes — clusters, RBAC, network policies, Azure AD integration",
  },
  {
    id: "azure-entra-id",
    name: "Microsoft Entra ID",
    provider: "azure",
    category: "identity",
    apiEndpoint: "https://graph.microsoft.com/v1.0",
    authType: "oauth2",
    evidenceTypes: ["pim_assignment", "access_review", "verified_credential", "identity_protection"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF", "CIS Azure"],
    description: "Identity governance — PIM, access reviews, verified ID, identity protection",
  },
  {
    id: "azure-policy",
    name: "Azure Policy",
    provider: "azure",
    category: "compliance",
    apiEndpoint: "https://management.azure.com/subscriptions/{subscriptionId}/providers/Microsoft.Policy",
    authType: "oauth2",
    evidenceTypes: ["policy_assignment", "compliance_result", "remediation_task", "policy_set"],
    frameworks: ["SOC 2", "ISO 27001", "CIS Azure", "NIST CSF"],
    description: "Policy enforcement — assignments, compliance states, remediations, initiatives",
  },
  {
    id: "azure-blueprints",
    name: "Azure Blueprints",
    provider: "azure",
    category: "compliance",
    apiEndpoint: "https://management.azure.com/providers/Microsoft.Blueprint/blueprints",
    authType: "oauth2",
    evidenceTypes: ["blueprint_assignment", "artifact_config", "locked_assignment"],
    frameworks: ["SOC 2", "ISO 27001", "CIS Azure"],
    description: "Environment templating — blueprint assignments, artifacts, locked deployments",
  },
  {
    id: "azure-frontdoor",
    name: "Azure Front Door",
    provider: "azure",
    category: "network",
    apiEndpoint: "https://management.azure.com/subscriptions/{subscriptionId}/providers/Microsoft.Network/frontDoors",
    authType: "oauth2",
    evidenceTypes: ["waf_policy", "routing_rule", "origin_group", "security_policy"],
    frameworks: ["SOC 2", "ISO 27001", "PCI DSS"],
    description: "Global load balancer — WAF policies, routing, origin groups, TLS offload",
  },

  // ──────────────────────────────────────────────
  // GCP (10 connectors)
  // ──────────────────────────────────────────────
  {
    id: "gcp-scc",
    name: "Google Security Command Center",
    provider: "gcp",
    category: "security",
    apiEndpoint: "https://securitycenter.googleapis.com/v1/organizations/{orgId}/sources",
    authType: "service_account",
    evidenceTypes: ["finding", "asset_inventory", "security_center_mute", "run_finding"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF", "CIS GCP"],
    description: "Security posture — findings, assets, mute configs, Continuous Risk Assessment",
  },
  {
    id: "gcp-chronicle",
    name: "Google Chronicle SIEM",
    provider: "gcp",
    category: "security",
    apiEndpoint: "https://chronicle.googleapis.com/v1/organizations/{orgId}/instances/{instanceId}/rules",
    authType: "service_account",
    evidenceTypes: ["detection_rule", "ioc_match", "retrohunt_result", "log_ingestion"],
    frameworks: ["SOC 2", "ISO 27001", "MITRE ATT&CK"],
    description: "Cloud SIEM — detection rules, IOC matching, retrohunt, log analytics",
  },
  {
    id: "gcp-iam",
    name: "Google Cloud IAM",
    provider: "gcp",
    category: "identity",
    apiEndpoint: "https://cloudresourcemanager.googleapis.com/v1/projects/{projectId}",
    authType: "service_account",
    evidenceTypes: ["binding_audit", "service_account_key", "conditional_binding", "denied_access"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF", "CIS GCP"],
    description: "Identity and Access Management — bindings, service accounts, deny policies, audit logs",
  },
  {
    id: "gcp-storage",
    name: "Google Cloud Storage",
    provider: "gcp",
    category: "storage",
    apiEndpoint: "https://storage.googleapis.com/storage/v1",
    authType: "service_account",
    evidenceTypes: ["bucket_policy", "iam_binding", "encryption_config", "retention_policy", "uniform_access"],
    frameworks: ["SOC 2", "ISO 27001", "HIPAA", "PCI DSS"],
    description: "Object storage — buckets, IAM bindings, CMEK, retention, lifecycle",
  },
  {
    id: "gcp-compute",
    name: "Google Compute Engine",
    provider: "gcp",
    category: "compute",
    apiEndpoint: "https://compute.googleapis.com/compute/v1/projects/{projectId}",
    authType: "service_account",
    evidenceTypes: ["instance_config", "firewall_rule", "disk_encryption", "snapshot_policy"],
    frameworks: ["SOC 2", "ISO 27001", "CIS GCP"],
    description: "Virtual machines — instances, disks, snapshots, firewall rules, OS images",
  },
  {
    id: "gcp-gke",
    name: "Google Kubernetes Engine",
    provider: "gcp",
    category: "compute",
    apiEndpoint: "https://container.googleapis.com/v1/projects/{projectId}/zones/{zone}/clusters",
    authType: "service_account",
    evidenceTypes: ["cluster_config", "node_pool", "workload_identity", "network_policy"],
    frameworks: ["SOC 2", "ISO 27001", "CIS GCP"],
    description: "Managed Kubernetes — clusters, node pools, Workload Identity, binary authorization",
  },
  {
    id: "gcp-cloudsql",
    name: "Google Cloud SQL",
    provider: "gcp",
    category: "data",
    apiEndpoint: "https://sqladmin.googleapis.com/v1/projects/{projectId}",
    authType: "service_account",
    evidenceTypes: ["instance_config", "backup_config", "ssl_required", "authorized_network"],
    frameworks: ["SOC 2", "ISO 27001", "HIPAA", "PCI DSS"],
    description: "Managed databases — MySQL/PostgreSQL/SQL Server instances, backups, SSL, networking",
  },
  {
    id: "gcp-kms",
    name: "Google Cloud KMS",
    provider: "gcp",
    category: "security",
    apiEndpoint: "https://cloudkms.googleapis.com/v1/projects/{projectId}/locations/{location}/keyRings",
    authType: "service_account",
    evidenceTypes: ["key_ring", "crypto_key", "key_rotation", "access_policy"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF", "PCI DSS"],
    description: "Key Management Service — key rings, crypto keys, rotation, access controls",
  },
  {
    id: "gcp-logging",
    name: "Google Cloud Logging",
    provider: "gcp",
    category: "security",
    apiEndpoint: "https://logging.googleapis.com/v2/projects/{projectId}/logs",
    authType: "service_account",
    evidenceTypes: ["audit_log", "log_sink", "log_metric", "exclusion_filter"],
    frameworks: ["SOC 2", "ISO 27001", "CIS GCP"],
    description: "Cloud Logging — audit logs, sinks, metrics, export destinations",
  },
  {
    id: "gcp-armor",
    name: "Google Cloud Armor",
    provider: "gcp",
    category: "network",
    apiEndpoint: "https://compute.googleapis.com/compute/v1/projects/{projectId}/global/securityPolicies",
    authType: "service_account",
    evidenceTypes: ["security_policy", "ddos_protection", "waf_rule", "adaptive_protection"],
    frameworks: ["SOC 2", "ISO 27001", "PCI DSS"],
    description: "DDoS and WAF — security policies, rate limiting, bot management, adaptive protection",
  },

  // ──────────────────────────────────────────────
  // GitHub (5 connectors)
  // ──────────────────────────────────────────────
  {
    id: "github-repos",
    name: "GitHub Repositories",
    provider: "github",
    category: "devops",
    apiEndpoint: "https://api.github.com/repos/{owner}/{repo}",
    authType: "bearer",
    evidenceTypes: ["branch_protection", "codeowners", "dependabot_alert", "secret_scanning_alert"],
    frameworks: ["SOC 2", "ISO 27001", "NIST SSDF", "SLSA"],
    description: "Source control — branch protection, code owners, repository settings, visibility",
  },
  {
    id: "github-actions",
    name: "GitHub Actions",
    provider: "github",
    category: "devops",
    apiEndpoint: "https://api.github.com/repos/{owner}/{repo}/actions",
    authType: "bearer",
    evidenceTypes: ["workflow_run", "runner_status", "secret_usage", "oidc_token", "artifact_retention"],
    frameworks: ["SOC 2", "ISO 27001", "NIST SSDF", "SLSA"],
    description: "CI/CD — workflows, runner groups, OIDC tokens, artifact attestation",
  },
  {
    id: "github-dependabot",
    name: "GitHub Dependabot",
    provider: "github",
    category: "security",
    apiEndpoint: "https://api.github.com/repos/{owner}/{repo}/dependabot",
    authType: "bearer",
    evidenceTypes: ["vulnerability_alert", "security_update", "version_update", "alert_status"],
    frameworks: ["SOC 2", "ISO 27001", "NIST SSDF", "OWASP"],
    description: "Dependency management — vulnerability alerts, auto-fix PRs, version updates",
  },
  {
    id: "github-secret-scanning",
    name: "GitHub Secret Scanning",
    provider: "github",
    category: "security",
    apiEndpoint: "https://api.github.com/repos/{owner}/{repo}/secret-scanning",
    authType: "bearer",
    evidenceTypes: ["secret_alert", "push_protection", "pattern_match"],
    frameworks: ["SOC 2", "ISO 27001", "NIST SSDF"],
    description: "Secret detection — push protection, partner alerts, custom patterns",
  },
  {
    id: "github-code-scanning",
    name: "GitHub Code Scanning (CodeQL)",
    provider: "github",
    category: "security",
    apiEndpoint: "https://api.github.com/repos/{owner}/{repo}/code-scanning",
    authType: "bearer",
    evidenceTypes: ["sarif_alert", "query_suite", "analysis_status", "rule_preview"],
    frameworks: ["SOC 2", "ISO 27001", "NIST SSDF", "OWASP"],
    description: "SAST — CodeQL analysis, SARIF uploads, security queries, alert management",
  },

  // ──────────────────────────────────────────────
  // Okta (3 connectors)
  // ──────────────────────────────────────────────
  {
    id: "okta-users",
    name: "Okta Users",
    provider: "okta",
    category: "identity",
    apiEndpoint: "https://{domain}/api/v1/users",
    authType: "api_key",
    evidenceTypes: ["user_status", "mfa_enrollment", "password_policy", "session_expiry", "last_login"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF", "CIS"],
    description: "User management — profiles, MFA enrollment, password policies, lifecycle states",
  },
  {
    id: "okta-factors",
    name: "Okta MFA Factors",
    provider: "okta",
    category: "identity",
    apiEndpoint: "https://{domain}/api/v1/users/{userId}/factors",
    authType: "api_key",
    evidenceTypes: ["factor_enrollment", "factor_type", "factor_status", "verify_result"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF", "PCI DSS"],
    description: "Multi-factor authentication — enrollment status, factor types, verification results",
  },
  {
    id: "okta-apps",
    name: "Okta Applications",
    provider: "okta",
    category: "identity",
    apiEndpoint: "https://{domain}/api/v1/apps",
    authType: "api_key",
    evidenceTypes: ["app_config", "sso_config", "provisioning", "assigned_users", "oauth_scope"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF"],
    description: "SSO applications — SAML/OIDC configs, provisioning, user assignments, sign-on policies",
  },

  // ──────────────────────────────────────────────
  // Cloudflare (3 connectors)
  // ──────────────────────────────────────────────
  {
    id: "cloudflare-waf",
    name: "Cloudflare WAF",
    provider: "cloudflare",
    category: "network",
    apiEndpoint: "https://api.cloudflare.com/client/v4/zones/{zoneId}/firewall/rules",
    authType: "bearer",
    evidenceTypes: ["firewall_rule", "rate_limit", "managed_rule", "bot_management"],
    frameworks: ["SOC 2", "ISO 27001", "PCI DSS", "OWASP"],
    description: "Web Application Firewall — custom rules, rate limiting, managed rulesets, bot score",
  },
  {
    id: "cloudflare-access",
    name: "Cloudflare Access",
    provider: "cloudflare",
    category: "identity",
    apiEndpoint: "https://api.cloudflare.com/client/v4/accounts/{accountId}/access/applications",
    authType: "bearer",
    evidenceTypes: ["access_application", "policy_audit", "session_audit", "identity_provider"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF"],
    description: "Zero Trust access — applications, policies, device posture, identity provider integrations",
  },
  {
    id: "cloudflare-gateway",
    name: "Cloudflare Gateway",
    provider: "cloudflare",
    category: "network",
    apiEndpoint: "https://api.cloudflare.com/client/v4/accounts/{accountId}/gateway",
    authType: "bearer",
    evidenceTypes: ["dns_log", "http_log", "network_log", "policy_category"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF"],
    description: "Secure Web Gateway — DNS/HTTP/network filtering, DLP, CASB, browser isolation",
  },

  // ──────────────────────────────────────────────
  // Datadog (3 connectors)
  // ──────────────────────────────────────────────
  {
    id: "datadog-metrics",
    name: "Datadog Metrics",
    provider: "datadog",
    category: "security",
    apiEndpoint: "https://api.datadoghq.com/api/v1/query",
    authType: "api_key",
    evidenceTypes: ["metric_series", "monitor_alert", "dashboard_config", "anomaly_detection"],
    frameworks: ["SOC 2", "ISO 27001"],
    description: "Infrastructure metrics — hosts, containers, APM traces, custom metrics, monitors",
  },
  {
    id: "datadog-logs",
    name: "Datadog Log Management",
    provider: "datadog",
    category: "security",
    apiEndpoint: "https://api.datadoghq.com/api/v2/logs/events",
    authType: "api_key",
    evidenceTypes: ["log_index", "log_pattern", "sensitive_data_scan", "archive_config"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF"],
    description: "Log analytics — index, archive, rehydrate, sensitive data scanning, live tail",
  },
  {
    id: "datadog-security",
    name: "Datadog Cloud SIEM",
    provider: "datadog",
    category: "security",
    apiEndpoint: "https://api.datadoghq.com/api/v2/security",
    authType: "api_key",
    evidenceTypes: ["security_signal", "detection_rule", "vulnerability", "misconfig"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF", "MITRE ATT&CK"],
    description: "Cloud SIEM — signals, detection rules, CSPM, runtime security, vulnerability mgmt",
  },

  // ──────────────────────────────────────────────
  // Splunk (2 connectors)
  // ──────────────────────────────────────────────
  {
    id: "splunk-events",
    name: "Splunk Events",
    provider: "splunk",
    category: "security",
    apiEndpoint: "https://{host}/services/search/jobs/export",
    authType: "bearer",
    evidenceTypes: ["index_event", "search_result", "sourcetype", "saved_search"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF", "MITRE ATT&CK"],
    description: "Event search — indexes, saved searches, data models, event types, field extractions",
  },
  {
    id: "splunk-alerts",
    name: "Splunk Enterprise Security",
    provider: "splunk",
    category: "security",
    apiEndpoint: "https://{host}/servicesNS/-/-/saved/searches",
    authType: "bearer",
    evidenceTypes: ["notable_event", "risk_score", "correlation_search", "lookup", "asset_identity"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF", "MITRE ATT&CK"],
    description: "Enterprise Security — notables, risk-based alerting, correlation, threat intelligence",
  },

  // ──────────────────────────────────────────────
  // Jira (2 connectors)
  // ──────────────────────────────────────────────
  {
    id: "jira-issues",
    name: "Jira Issues",
    provider: "jira",
    category: "devops",
    apiEndpoint: "https://{domain}.atlassian.net/rest/api/3/issue",
    authType: "basic",
    evidenceTypes: ["issue_audit", "workflow_transition", "field_change", "comment"],
    frameworks: ["SOC 2", "ISO 27001"],
    description: "Issue tracking — issues, workflows, fields, sprint boards, audit logs",
  },
  {
    id: "jira-projects",
    name: "Jira Projects",
    provider: "jira",
    category: "devops",
    apiEndpoint: "https://{domain}.atlassian.net/rest/api/3/project",
    authType: "basic",
    evidenceTypes: ["project_config", "permission_scheme", "notification_scheme", "workflow_scheme"],
    frameworks: ["SOC 2", "ISO 27001"],
    description: "Project management — schemes, permissions, components, versions, boards",
  },

  // ──────────────────────────────────────────────
  // Slack (2 connectors)
  // ──────────────────────────────────────────────
  {
    id: "slack-messages",
    name: "Slack Messages",
    provider: "slack",
    category: "devops",
    apiEndpoint: "https://slack.com/api/conversations.history",
    authType: "bearer",
    evidenceTypes: ["message_audit", "attachment_scan", "sensitive_data", "bot_activity"],
    frameworks: ["SOC 2", "ISO 27001"],
    description: "Messaging — channel messages, DMs, files, app mentions, audit trail",
  },
  {
    id: "slack-channels",
    name: "Slack Channels",
    provider: "slack",
    category: "devops",
    apiEndpoint: "https://slack.com/api/conversations.info",
    authType: "bearer",
    evidenceTypes: ["channel_config", "member_access", "external_shared", "private_channel"],
    frameworks: ["SOC 2", "ISO 27001"],
    description: "Channel management — public/private/shared channels, memberships, retention",
  },

  // ──────────────────────────────────────────────
  // Salesforce (2 connectors)
  // ──────────────────────────────────────────────
  {
    id: "salesforce-objects",
    name: "Salesforce Objects",
    provider: "salesforce",
    category: "data",
    apiEndpoint: "https://{instance}.salesforce.com/services/data/v{version}/sobjects",
    authType: "oauth2",
    evidenceTypes: ["object_permission", "field_level_security", "record_access", "sharing_rule"],
    frameworks: ["SOC 2", "ISO 27001", "HIPAA"],
    description: "CRM data — objects, field-level security, sharing rules, record ownership",
  },
  {
    id: "salesforce-events",
    name: "Salesforce Events",
    provider: "salesforce",
    category: "security",
    apiEndpoint: "https://{instance}.salesforce.com/services/data/v{version}/query",
    authType: "oauth2",
    evidenceTypes: ["login_event", "api_call", "setup_audit", "field_audit", "permission_change"],
    frameworks: ["SOC 2", "ISO 27001", "HIPAA"],
    description: "Audit events — login history, API usage, setup audit trail, field tracking",
  },

  // ──────────────────────────────────────────────
  // Snowflake (2 connectors)
  // ──────────────────────────────────────────────
  {
    id: "snowflake-queries",
    name: "Snowflake Queries",
    provider: "snowflake",
    category: "data",
    apiEndpoint: "https://{account}.snowflakecomputing.com/api/v2/statements",
    authType: "oauth2",
    evidenceTypes: ["query_history", "data_access", "copy_history", "data_transfer"],
    frameworks: ["SOC 2", "ISO 27001", "HIPAA", "PCI DSS"],
    description: "Data warehouse — query history, access patterns, data sharing, replication",
  },
  {
    id: "snowflake-access",
    name: "Snowflake Access",
    provider: "snowflake",
    category: "identity",
    apiEndpoint: "https://{account}.snowflakecomputing.com/api/v2/accounts/{accountId}/users",
    authType: "oauth2",
    evidenceTypes: ["user_inventory", "role_assignment", "session_policy", "password_policy", "mfa_status"],
    frameworks: ["SOC 2", "ISO 27001", "HIPAA", "PCI DSS"],
    description: "Data access governance — users, roles, session policies, network policies, MFA",
  },

  // ──────────────────────────────────────────────
  // MongoDB (2 connectors)
  // ──────────────────────────────────────────────
  {
    id: "mongodb-collections",
    name: "MongoDB Atlas Collections",
    provider: "mongodb",
    category: "data",
    apiEndpoint: "https://cloud.mongodb.com/api/atlas/v1.0/groups/{groupId}/clusters",
    authType: "api_key",
    evidenceTypes: ["collection_config", "index_usage", "data_size", "encryption_at_rest"],
    frameworks: ["SOC 2", "ISO 27001", "HIPAA"],
    description: "NoSQL database — clusters, collections, indexes, encryption, performance advisor",
  },
  {
    id: "mongodb-access",
    name: "MongoDB Atlas Access",
    provider: "mongodb",
    category: "identity",
    apiEndpoint: "https://cloud.mongodb.com/api/atlas/v1.0/groups/{groupId}/databaseUsers",
    authType: "api_key",
    evidenceTypes: ["database_user", "role_assignment", "ip_access_list", "api_key_audit"],
    frameworks: ["SOC 2", "ISO 27001", "HIPAA"],
    description: "Database access — users, custom roles, IP whitelists, audit API keys",
  },

  // ──────────────────────────────────────────────
  // Redis (2 connectors)
  // ──────────────────────────────────────────────
  {
    id: "redis-config",
    name: "Redis Enterprise Config",
    provider: "redis",
    category: "data",
    apiEndpoint: "https://{endpoint}/v1/cluster",
    authType: "api_key",
    evidenceTypes: ["cluster_config", "memory_usage", "persistence_config", "eviction_policy"],
    frameworks: ["SOC 2", "ISO 27001"],
    description: "In-memory data store — cluster config, persistence, replication, TLS enforcement",
  },
  {
    id: "redis-access",
    name: "Redis Enterprise Access",
    provider: "redis",
    category: "identity",
    apiEndpoint: "https://{endpoint}/v1/redis-access",
    authType: "api_key",
    evidenceTypes: ["acl_config", "user_inventory", "tls_config", "authentication"],
    frameworks: ["SOC 2", "ISO 27001"],
    description: "Access control — ACLs, RBAC users, TLS certificates, authentication settings",
  },

  // ──────────────────────────────────────────────
  // Additional AWS (6 connectors)
  // ──────────────────────────────────────────────
  {
    id: "aws-config",
    name: "AWS Config",
    provider: "aws",
    category: "compliance",
    apiEndpoint: "https://config.{region}.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["resource_compliance", "config_rule", "configuration_item", "remediation"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF", "CIS AWS"],
    description: "Resource compliance — config rules, compliance evaluations, remediation actions",
  },
  {
    id: "aws-cloudwatch",
    name: "Amazon CloudWatch",
    provider: "aws",
    category: "security",
    apiEndpoint: "https://monitoring.{region}.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["metric_alarm", "log_group", "dashboard", "anomaly_detector"],
    frameworks: ["SOC 2", "ISO 27001"],
    description: "Monitoring — alarms, log groups, dashboards, anomaly detection, metric streams",
  },
  {
    id: "aws-codepipeline",
    name: "AWS CodePipeline",
    provider: "aws",
    category: "devops",
    apiEndpoint: "https://codepipeline.{region}.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["pipeline_config", "execution_history", "stage_status", "artifact_bucket"],
    frameworks: ["SOC 2", "ISO 27001"],
    description: "CI/CD pipeline — stages, actions, execution history, artifact encryption",
  },
  {
    id: "aws-codebuild",
    name: "AWS CodeBuild",
    provider: "aws",
    category: "devops",
    apiEndpoint: "https://codebuild.{region}.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["build_project", "build_report", "secret_env_var", "build_phase"],
    frameworks: ["SOC 2", "ISO 27001"],
    description: "Build service — projects, build reports, environment variables, VPC config",
  },
  {
    id: "aws-elb",
    name: "AWS Elastic Load Balancing",
    provider: "aws",
    category: "network",
    apiEndpoint: "https://elasticloadbalancing.{region}.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["lb_config", "listener_policy", "access_log", "waf_association"],
    frameworks: ["SOC 2", "ISO 27001", "PCI DSS"],
    description: "Load balancing — ALB/NLB/GLB configs, listeners, WAF associations, access logs",
  },
  {
    id: "aws-ssm",
    name: "AWS Systems Manager",
    provider: "aws",
    category: "compliance",
    apiEndpoint: "https://ssm.{region}.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["patch_compliance", "parameter_store", "session_manager", "automation"],
    frameworks: ["SOC 2", "ISO 27001", "CIS AWS"],
    description: "Operations — patch baselines, parameter store, session logging, automation runbooks",
  },
  {
    id: "aws-acm",
    name: "AWS Certificate Manager",
    provider: "aws",
    category: "security",
    apiEndpoint: "https://acm.{region}.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["certificate_inventory", "expiration_status", "auto_renewal", "pca_config"],
    frameworks: ["SOC 2", "ISO 27001", "PCI DSS"],
    description: "TLS certificates — issuance, renewal, private CA, transparency logs",
  },
  {
    id: "aws-secrets-manager",
    name: "AWS Secrets Manager",
    provider: "aws",
    category: "security",
    apiEndpoint: "https://secretsmanager.{region}.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["secret_inventory", "rotation_config", "access_policy", "kms_key"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF", "PCI DSS"],
    description: "Secret management — rotation, cross-account sharing, fine-grained policies",
  },
  {
    id: "aws-wellarchitected",
    name: "AWS Well-Architected Tool",
    provider: "aws",
    category: "compliance",
    apiEndpoint: "https://wellarchitected.{region}.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["workload_review", "pillar_score", "improvement_plan", "milestone"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF"],
    description: "Architecture review — workload reviews, pillar scores, improvement plans, milestones",
  },
  {
    id: "aws-inspector",
    name: "AWS Inspector",
    provider: "aws",
    category: "security",
    apiEndpoint: "https://inspector2.{region}.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["vulnerability_finding", "cve_score", "remediation", "ecr_image_scan"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF"],
    description: "Vulnerability scanning — EC2, ECR, Lambda, network reachability, CVE reporting",
  },
  {
    id: "aws-access-analyzer",
    name: "AWS IAM Access Analyzer",
    provider: "aws",
    category: "identity",
    apiEndpoint: "https://access-analyzer.{region}.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["external_access", "unused_access", "policy_generation", "zone_of_trust"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF"],
    description: "Access analysis — external access findings, unused access, policy generation",
  },
  {
    id: "aws-bedrock",
    name: "AWS Bedrock",
    provider: "aws",
    category: "compute",
    apiEndpoint: "https://bedrock.{region}.amazonaws.com",
    authType: "aws_sigv4",
    evidenceTypes: ["model_access", "guardrail_config", "usage_audit", "data_source"],
    frameworks: ["SOC 2", "ISO 27001", "ISO 42001"],
    description: "AI/ML platform — model access, guardrails, usage metrics, custom model deployment",
  },
  // ──────────────────────────────────────────────
  // Azure additional (5 connectors)
  // ──────────────────────────────────────────────
  {
    id: "azure-purview",
    name: "Microsoft Purview",
    provider: "azure",
    category: "data",
    apiEndpoint: "https://management.azure.com/subscriptions/{subscriptionId}/providers/Microsoft.Purview",
    authType: "oauth2",
    evidenceTypes: ["data_catalog", "classification", "lineage", "sensitivity_label", "dlp_alert"],
    frameworks: ["SOC 2", "ISO 27001", "GDPR", "HIPAA"],
    description: "Data governance — classification, DLP, information barriers, eDiscovery, audit",
  },
  {
    id: "azure-firewall",
    name: "Azure Firewall",
    provider: "azure",
    category: "network",
    apiEndpoint: "https://management.azure.com/subscriptions/{subscriptionId}/providers/Microsoft.Network/azureFirewalls",
    authType: "oauth2",
    evidenceTypes: ["firewall_policy", "threat_intel", "nat_rule", "application_rule", "dns_proxy"],
    frameworks: ["SOC 2", "ISO 27001", "CIS Azure"],
    description: "Managed firewall — policies, threat intelligence, centralized logging, FQDN filtering",
  },
  {
    id: "azure-information-protection",
    name: "Azure Information Protection",
    provider: "azure",
    category: "compliance",
    apiEndpoint: "https://management.azure.com/providers/Microsoft.InformationProtection",
    authType: "oauth2",
    evidenceTypes: ["label_policy", "sensitivity_label", "doc_inspector", "protection_action"],
    frameworks: ["SOC 2", "ISO 27001", "GDPR", "HIPAA"],
    description: "Data classification — sensitivity labels, auto-labeling, protection actions, analytics",
  },
  {
    id: "azure-devops",
    name: "Azure DevOps",
    provider: "azure",
    category: "devops",
    apiEndpoint: "https://dev.azure.com/{organization}/_apis",
    authType: "bearer",
    evidenceTypes: ["pipeline_config", "repo_branch_protection", "artifacts_feed", "release_gate"],
    frameworks: ["SOC 2", "ISO 27001", "NIST SSDF"],
    description: "DevOps platform — repos, pipelines, boards, artifacts, test plans, extensions",
  },
  {
    id: "azure-communication",
    name: "Azure Communication Services",
    provider: "azure",
    category: "compliance",
    apiEndpoint: "https://management.azure.com/subscriptions/{subscriptionId}/providers/Microsoft.Communication",
    authType: "oauth2",
    evidenceTypes: ["sms_log", "call_recording", "identity_token", "acs_config"],
    frameworks: ["SOC 2", "ISO 27001"],
    description: "Communication platform — SMS, voice, video, chat, email, identity",
  },
  // ──────────────────────────────────────────────
  // GitHub additional (2 connectors)
  // ──────────────────────────────────────────────
  {
    id: "github-copilot",
    name: "GitHub Copilot",
    provider: "github",
    category: "devops",
    apiEndpoint: "https://api.github.com/orgs/{org}/copilot",
    authType: "bearer",
    evidenceTypes: ["seat_assignment", "usage_metrics", "content_exclusion", "policy_config"],
    frameworks: ["SOC 2", "ISO 27001"],
    description: "AI pair programming — seat management, usage analytics, content exclusions, policies",
  },
  {
    id: "github-security",
    name: "GitHub Security Overview",
    provider: "github",
    category: "security",
    apiEndpoint: "https://api.github.com/orgs/{org}/security-alerts",
    authType: "bearer",
    evidenceTypes: ["security_advisory", "dependabot_alert", "code_scanning_alert", "secret_scanning_alert"],
    frameworks: ["SOC 2", "ISO 27001", "NIST SSDF"],
    description: "Org-wide security — alert aggregation, severity trends, auto-dismiss, review flows",
  },
  // ──────────────────────────────────────────────
  // Okta additional (1 connector)
  // ──────────────────────────────────────────────
  {
    id: "okta-system",
    name: "Okta System Log",
    provider: "okta",
    category: "security",
    apiEndpoint: "https://{domain}/api/v1/logs",
    authType: "api_key",
    evidenceTypes: ["auth_event", "policy_change", "admin_action", "rate_limit", "suspicious_activity"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF"],
    description: "Audit logging — authentication events, policy changes, admin actions, risk signals",
  },
  // ──────────────────────────────────────────────
  // Cloudflare additional (2 connectors)
  // ──────────────────────────────────────────────
  {
    id: "cloudflare-dns",
    name: "Cloudflare DNS Analytics",
    provider: "cloudflare",
    category: "network",
    apiEndpoint: "https://api.cloudflare.com/client/v4/zones/{zoneId}/dns_analytics",
    authType: "bearer",
    evidenceTypes: ["query_log", "query_type", "response_code", "top_domains"],
    frameworks: ["SOC 2", "ISO 27001"],
    description: "DNS analytics — query logs, response analysis, threat detection, domain classification",
  },
  {
    id: "cloudflare-r2",
    name: "Cloudflare R2 Storage",
    provider: "cloudflare",
    category: "storage",
    apiEndpoint: "https://api.cloudflare.com/client/v4/accounts/{accountId}/r2/buckets",
    authType: "bearer",
    evidenceTypes: ["bucket_config", "object_retention", "access_audit", "custom_domain"],
    frameworks: ["SOC 2", "ISO 27001"],
    description: "Object storage — buckets, S3-compatible API, lifecycle, retention, anti-ransomware",
  },
  // ──────────────────────────────────────────────
  // Datadog additional (1 connector)
  // ──────────────────────────────────────────────
  {
    id: "datadog-ci-cd",
    name: "Datadog CI Visibility",
    provider: "datadog",
    category: "devops",
    apiEndpoint: "https://api.datadoghq.com/api/v2/ci/pipelines",
    authType: "api_key",
    evidenceTypes: ["pipeline_event", "test_result", "deployment_event", "flaky_test"],
    frameworks: ["SOC 2", "ISO 27001"],
    description: "CI/CD visibility — pipeline traces, test performance, deployment tracking, flaky detection",
  },
  // ──────────────────────────────────────────────
  // Splunk additional (1 connector)
  // ──────────────────────────────────────────────
  {
    id: "splunk-ueba",
    name: "Splunk UBA",
    provider: "splunk",
    category: "security",
    apiEndpoint: "https://{host}/servicesNS/-/-/saved/searches",
    authType: "bearer",
    evidenceTypes: ["anomaly_detection", "threat_score", "user_risk", "entity_risk"],
    frameworks: ["SOC 2", "ISO 27001", "NIST CSF"],
    description: "User Behavior Analytics — threat detection, entity risk scoring, anomaly baselining",
  },
  // ──────────────────────────────────────────────
  // Jira additional (1 connector)
  // ──────────────────────────────────────────────
  {
    id: "jira-insight",
    name: "Jira Service Management",
    provider: "jira",
    category: "devops",
    apiEndpoint: "https://{domain}.atlassian.net/rest/api/3/serviceDesk",
    authType: "basic",
    evidenceTypes: ["incident_ticket", "change_request", "sla_compliance", "approval_workflow"],
    frameworks: ["SOC 2", "ISO 27001", "ITIL"],
    description: "ITSM — incidents, changes, SLAs, approval workflows, CMDB integration",
  },
  // ──────────────────────────────────────────────
  // Snowflake additional (1 connector)
  // ──────────────────────────────────────────────
  {
    id: "snowflake-monitoring",
    name: "Snowflake Account Usage",
    provider: "snowflake",
    category: "compliance",
    apiEndpoint: "https://{account}.snowflakecomputing.com/api/v2/statements",
    authType: "oauth2",
    evidenceTypes: ["account_usage", "login_history", "query_history", "storage_usage", "task_history"],
    frameworks: ["SOC 2", "ISO 27001", "HIPAA", "PCI DSS"],
    description: "Account governance — login history, storage trends, task runs, resource monitors",
  },
  // ──────────────────────────────────────────────
  // Additional Cloudflare
  // ──────────────────────────────────────────────
  {
    id: "cloudflare-ssl",
    name: "Cloudflare SSL/TLS",
    provider: "cloudflare",
    category: "security",
    apiEndpoint: "https://api.cloudflare.com/client/v4/zones/{zoneId}/ssl",
    authType: "bearer",
    evidenceTypes: ["ssl_mode", "certificate_status", "hsts_config", "min_tls_version"],
    frameworks: ["SOC 2", "ISO 27001", "PCI DSS"],
    description: "TLS management — SSL modes, Universal/Advanced certificates, HSTS, min TLS version",
  },
  // ──────────────────────────────────────────────
  // Additional GCP
  // ──────────────────────────────────────────────
  {
    id: "gcp-dlp",
    name: "Google Cloud DLP",
    provider: "gcp",
    category: "compliance",
    apiEndpoint: "https://dlp.googleapis.com/v2/projects/{projectId}",
    authType: "service_account",
    evidenceTypes: ["inspection_job", "stored_info_type", "deidentification_config", "finding"],
    frameworks: ["SOC 2", "ISO 27001", "HIPAA", "GDPR"],
    description: "Data Loss Prevention — inspections, de-identification, stored infoTypes, risk analysis",
  },
  {
    id: "gcp-firestore",
    name: "Google Cloud Firestore",
    provider: "gcp",
    category: "data",
    apiEndpoint: "https://firestore.googleapis.com/v1/projects/{projectId}/databases/(default)/documents",
    authType: "service_account",
    evidenceTypes: ["collection_config", "security_rule", "backup_schedule", "encryption_config"],
    frameworks: ["SOC 2", "ISO 27001", "HIPAA"],
    description: "Serverless NoSQL — collections, security rules, backups, encryption, multi-region",
  },
  // ──────────────────────────────────────────────
  // Additional MongoDB
  // ──────────────────────────────────────────────
  {
    id: "mongodb-audit",
    name: "MongoDB Atlas Audit",
    provider: "mongodb",
    category: "security",
    apiEndpoint: "https://cloud.mongodb.com/api/atlas/v1.0/groups/{groupId}/auditLog",
    authType: "api_key",
    evidenceTypes: ["audit_event", "auth_event", "schema_change", "query_event"],
    frameworks: ["SOC 2", "ISO 27001", "HIPAA", "PCI DSS"],
    description: "Database auditing — authentication events, DDL changes, queries, access patterns",
  },
  // ──────────────────────────────────────────────
  // Additional Redis
  // ──────────────────────────────────────────────
  {
    id: "redis-metrics",
    name: "Redis Enterprise Metrics",
    provider: "redis",
    category: "security",
    apiEndpoint: "https://{endpoint}/v1/metrics",
    authType: "api_key",
    evidenceTypes: ["throughput", "latency", "memory", "connections", "eviction"],
    frameworks: ["SOC 2", "ISO 27001"],
    description: "Performance metrics — throughput, latency, memory pressure, connection tracking",
  },
];

export function getConnectorById(id: string): ConnectorDefinition | undefined {
  return CONNECTOR_CATALOG.find((c) => c.id === id);
}

export function getConnectorsByProvider(provider: ConnectorProvider): ConnectorDefinition[] {
  return CONNECTOR_CATALOG.filter((c) => c.provider === provider);
}

export function getConnectorsByCategory(category: ConnectorCategory): ConnectorDefinition[] {
  return CONNECTOR_CATALOG.filter((c) => c.category === category);
}

export function getConnectorsByFramework(framework: string): ConnectorDefinition[] {
  return CONNECTOR_CATALOG.filter((c) => c.frameworks.includes(framework));
}

export function getProviders(): ConnectorProvider[] {
  return [...new Set(CONNECTOR_CATALOG.map((c) => c.provider))];
}

export function getCatalogSummary(): Record<ConnectorProvider, number> {
  const summary: Partial<Record<ConnectorProvider, number>> = {};
  for (const connector of CONNECTOR_CATALOG) {
    summary[connector.provider] = (summary[connector.provider] || 0) + 1;
  }
  return summary as Record<ConnectorProvider, number>;
}
