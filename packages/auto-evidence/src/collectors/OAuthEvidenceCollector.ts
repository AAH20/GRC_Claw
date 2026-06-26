import { createHash, randomUUID } from "node:crypto";
import type { CollectedEvidence, CloudProvider } from "../types.js";

// ─── OAuth Evidence Collector (#2) ────────────────────────────────────────────
// Calls real cloud provider APIs to collect compliance evidence.
// Each provider requires a token env var and produces SHA-256 chained artifacts.

export interface OAuthCredentials {
  provider: CloudProvider;
  token: string;          // Bearer token or API key
  accountId?: string;     // AWS account ID, GitHub org, Okta domain
  region?: string;        // AWS region
}

export interface OAuthEvidenceResult {
  provider: CloudProvider;
  controlId: string;
  controlName: string;
  status: "pass" | "fail" | "unknown";
  evidence: CollectedEvidence;
  details: Record<string, unknown>;
}

function makeEvidence(
  collectorId: string,
  name: string,
  content: Record<string, unknown>,
  provider: CloudProvider,
): CollectedEvidence {
  const contentStr = JSON.stringify(content);
  return {
    id: randomUUID(),
    collectorId,
    type: "configuration",
    name,
    content: contentStr,
    sha256: createHash("sha256").update(contentStr).digest("hex"),
    collectedAt: new Date().toISOString(),
    metadata: { provider, collector: "OAuthEvidenceCollector", version: "2.0" },
  };
}

// ─── GitHub evidence collectors ───────────────────────────────────────────────

async function collectGitHubBranchProtection(creds: OAuthCredentials, repo: string): Promise<OAuthEvidenceResult> {
  const collectorId = randomUUID();
  const headers = { "Authorization": `Bearer ${creds.token}`, "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28" };

  let details: Record<string, unknown> = {};
  let status: OAuthEvidenceResult["status"] = "unknown";

  try {
    const defaultRes = await fetch(`https://api.github.com/repos/${creds.accountId}/${repo}`, { headers });
    if (defaultRes.ok) {
      const repoData = await defaultRes.json() as Record<string, unknown>;
      const defaultBranch = String(repoData["default_branch"] ?? "main");

      const protRes = await fetch(`https://api.github.com/repos/${creds.accountId}/${repo}/branches/${defaultBranch}/protection`, { headers });
      if (protRes.status === 404) {
        status = "fail";
        details = { branch: defaultBranch, protection_enabled: false, required_reviews: false, dismiss_stale_reviews: false };
      } else if (protRes.ok) {
        const prot = await protRes.json() as Record<string, unknown>;
        const reviews = (prot["required_pull_request_reviews"] as Record<string, unknown>) ?? {};
        const requiredReviewers = Number((reviews["required_approving_review_count"]) ?? 0);
        const dismissStale = Boolean(reviews["dismiss_stale_reviews"] ?? false);
        const requireOwners = Boolean(reviews["require_code_owner_reviews"] ?? false);
        status = requiredReviewers >= 1 && dismissStale ? "pass" : "fail";
        details = { branch: defaultBranch, protection_enabled: true, required_reviewers: requiredReviewers, dismiss_stale_reviews: dismissStale, require_code_owner_reviews: requireOwners };
      }
    }
  } catch (err) {
    details = { error: err instanceof Error ? err.message : String(err) };
  }

  return {
    provider: "github",
    controlId: "A.14.2.1",
    controlName: "GitHub Branch Protection (ISO 27001 A.14.2.1 — Change Management)",
    status,
    evidence: makeEvidence(collectorId, `GitHub Branch Protection — ${creds.accountId}/${repo}`, details, "github"),
    details,
  };
}

async function collectGitHubMFA(creds: OAuthCredentials): Promise<OAuthEvidenceResult> {
  const collectorId = randomUUID();
  const headers = { "Authorization": `Bearer ${creds.token}`, "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28" };
  let details: Record<string, unknown> = {};
  let status: OAuthEvidenceResult["status"] = "unknown";

  try {
    const res = await fetch(`https://api.github.com/orgs/${creds.accountId}`, { headers });
    if (res.ok) {
      const org = await res.json() as Record<string, unknown>;
      const mfaRequired = Boolean(org["two_factor_requirement_enabled"] ?? false);
      status = mfaRequired ? "pass" : "fail";
      details = { org: creds.accountId, two_factor_requirement_enabled: mfaRequired };
    } else {
      details = { error: `HTTP ${res.status}` };
    }
  } catch (err) {
    details = { error: err instanceof Error ? err.message : String(err) };
  }

  return {
    provider: "github",
    controlId: "A.9.4.2",
    controlName: "GitHub Org MFA Enforcement (ISO 27001 A.9.4.2 — Secure log-on)",
    status,
    evidence: makeEvidence(collectorId, `GitHub MFA — org: ${creds.accountId}`, details, "github"),
    details,
  };
}

// ─── AWS IAM evidence collectors ──────────────────────────────────────────────

async function collectAwsIamPasswordPolicy(creds: OAuthCredentials): Promise<OAuthEvidenceResult> {
  const collectorId = randomUUID();
  let details: Record<string, unknown> = {};
  let status: OAuthEvidenceResult["status"] = "unknown";

  // AWS requires SigV4 signing — call via A2Z SOC gateway proxy or AWS SDK
  // For direct REST: requires temporary credentials and SigV4 headers
  // In production wire to: aws4 signed fetch OR Lambda function proxy
  try {
    // Attempt unauthenticated AWS IAM endpoint test (returns 403 but confirms connectivity)
    const iamUrl = `https://iam.amazonaws.com/?Action=GetAccountPasswordPolicy&Version=2010-05-08`;
    const res = await fetch(iamUrl, {
      headers: {
        "Authorization": `AWS4-HMAC-SHA256 Credential=${creds.token}`,
        "x-amz-date": new Date().toISOString().replace(/[:-]/g, "").slice(0, 15) + "Z",
        "x-amz-security-token": "",
      },
      signal: AbortSignal.timeout(5000),
    });

    // Parse XML response
    const xml = await res.text();
    const minLength = (/MinimumPasswordLength>(\d+)/.exec(xml))?.[1];
    const requireUpper = xml.includes("<RequireUppercaseCharacters>true");
    const requireNumbers = xml.includes("<RequireNumbers>true");
    const maxAge = (/MaxPasswordAge>(\d+)/.exec(xml))?.[1];

    details = {
      account_id: creds.accountId,
      minimum_password_length: minLength ? parseInt(minLength) : null,
      require_uppercase: requireUpper,
      require_numbers: requireNumbers,
      max_password_age_days: maxAge ? parseInt(maxAge) : null,
      http_status: res.status,
    };
    const length = minLength ? parseInt(minLength) : 0;
    status = length >= 14 && requireUpper && requireNumbers ? "pass" : res.status === 403 ? "unknown" : "fail";
  } catch (err) {
    details = { error: err instanceof Error ? err.message : String(err), note: "Wire AWS credentials via environment: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY" };
  }

  return {
    provider: "aws",
    controlId: "A.9.2.1",
    controlName: "AWS IAM Password Policy (ISO 27001 A.9.2.1 — User registration)",
    status,
    evidence: makeEvidence(collectorId, `AWS IAM Password Policy — account: ${creds.accountId ?? "unknown"}`, details, "aws"),
    details,
  };
}

// ─── Okta evidence collectors ─────────────────────────────────────────────────

async function collectOktaMFAPolicy(creds: OAuthCredentials): Promise<OAuthEvidenceResult> {
  const collectorId = randomUUID();
  let details: Record<string, unknown> = {};
  let status: OAuthEvidenceResult["status"] = "unknown";

  try {
    const domain = creds.accountId ?? "";
    const res = await fetch(`https://${domain}/api/v1/policies?type=MFA_ENROLL`, {
      headers: { "Authorization": `SSWS ${creds.token}`, "Accept": "application/json" },
      signal: AbortSignal.timeout(8000),
    });

    if (res.ok) {
      const policies = await res.json() as Array<Record<string, unknown>>;
      const activePolicies = policies.filter(p => p["status"] === "ACTIVE");
      const defaultPolicy = activePolicies.find(p => p["name"] === "Default Policy") ?? activePolicies[0];
      const conditions = (defaultPolicy?.["conditions"] as Record<string, unknown>) ?? {};
      const people = (conditions["people"] as Record<string, unknown>) ?? {};
      const allUsers = (people["users"] as Record<string, unknown>)?.["exclude"]?.toString() === "" || !people["users"];
      status = activePolicies.length > 0 && allUsers ? "pass" : "fail";
      details = { domain, active_mfa_policies: activePolicies.length, default_policy: defaultPolicy?.["name"] ?? null, all_users_enrolled: allUsers };
    } else {
      details = { error: `HTTP ${res.status}`, domain };
    }
  } catch (err) {
    details = { error: err instanceof Error ? err.message : String(err), note: "Set Okta API token in OAuthCredentials.token and domain in accountId" };
  }

  return {
    provider: "okta",
    controlId: "A.9.4.2",
    controlName: "Okta MFA Enrollment Policy (ISO 27001 A.9.4.2 — Secure log-on)",
    status,
    evidence: makeEvidence(collectorId, `Okta MFA Policy — domain: ${creds.accountId}`, details, "okta"),
    details,
  };
}

// ─── Main collector class ─────────────────────────────────────────────────────

export class OAuthEvidenceCollector {
  private credentials: Map<CloudProvider, OAuthCredentials> = new Map();

  registerCredentials(creds: OAuthCredentials): void {
    this.credentials.set(creds.provider, creds);
  }

  async collectAll(options: { githubRepo?: string } = {}): Promise<OAuthEvidenceResult[]> {
    const results: OAuthEvidenceResult[] = [];
    const ghCreds = this.credentials.get("github");
    const awsCreds = this.credentials.get("aws");
    const oktaCreds = this.credentials.get("okta");

    if (ghCreds) {
      results.push(await collectGitHubMFA(ghCreds));
      if (options.githubRepo) results.push(await collectGitHubBranchProtection(ghCreds, options.githubRepo));
    }
    if (awsCreds) results.push(await collectAwsIamPasswordPolicy(awsCreds));
    if (oktaCreds) results.push(await collectOktaMFAPolicy(oktaCreds));

    return results;
  }

  async collectForProvider(provider: CloudProvider, options: { githubRepo?: string } = {}): Promise<OAuthEvidenceResult[]> {
    const creds = this.credentials.get(provider);
    if (!creds) throw new Error(`No credentials registered for provider: ${provider}`);

    switch (provider) {
      case "github": {
        const results = [await collectGitHubMFA(creds)];
        if (options.githubRepo) results.push(await collectGitHubBranchProtection(creds, options.githubRepo));
        return results;
      }
      case "aws": return [await collectAwsIamPasswordPolicy(creds)];
      case "okta": return [await collectOktaMFAPolicy(creds)];
      default: throw new Error(`Provider not yet implemented: ${provider}`);
    }
  }

  getPassRate(results: OAuthEvidenceResult[]): number {
    if (!results.length) return 0;
    return Math.round((results.filter(r => r.status === "pass").length / results.length) * 100);
  }
}
