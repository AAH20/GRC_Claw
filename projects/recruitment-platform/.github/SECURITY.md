# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Which versions are eligible for receiving such patches depends on the CVSS v3.0 Rating:

| Version | Supported |
|---------|-----------|
| 1.x.x   | ✅ Yes    |
| 0.x.x   | ❌ No     |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via one of the following methods:

1. **GitHub Security Advisories** (preferred): [Report a vulnerability](https://github.com/GRC_Claw/recruitment-platform/security/advisories/new)
2. **Email**: [team@grc-claw.com](mailto:team@grc-claw.com)

Please include the following information in your report:

- **Type of issue** (e.g., SQL injection, XSS, CSRF, authentication bypass)
- **Full paths** of the source file(s) related to the issue
- **Step-by-step instructions** to reproduce the issue
- **Proof-of-concept or exploit code** (if available)
- **Impact of the issue** (what an attacker can do)
- **Affected versions** (if known)

### What to Expect

| Step | Timeline | Description |
|------|----------|-------------|
| 1 | Within 48 hours | Acknowledgment of your report |
| 2 | Within 7 days | Initial assessment and severity classification |
| 3 | Within 14 days | Fix or mitigation plan communicated |
| 4 | Within 30 days | Patch released (for critical/high severity) |

We will keep you informed of the progress towards a fix and announcement.

## Security Measures

### Authentication & Authorization

- All API endpoints require authentication via JWT tokens
- Role-based access control (RBAC) is enforced at the API gateway level
- Session tokens expire after 24 hours of inactivity
- Multi-factor authentication (MFA) is supported for admin accounts

### Data Protection

- All data in transit is encrypted using TLS 1.3
- Sensitive data at rest is encrypted using AES-256
- Passwords are hashed using bcrypt with a minimum cost factor of 12
- PII (Personally Identifiable Information) is stored in isolated, encrypted columns
- Database connections use certificate-based authentication

### Infrastructure

- All infrastructure is deployed in a private VPC
- Network security groups restrict traffic to necessary ports only
- DDoS protection is enabled via cloud provider services
- Regular vulnerability scans are performed on all infrastructure components
- Container images are scanned for vulnerabilities before deployment

### Application Security

- Input validation and sanitization on all user-provided data
- Parameterized queries to prevent SQL injection
- Content Security Policy (CSP) headers are set on all responses
- Rate limiting is applied to all API endpoints
- CORS is configured with strict origin policies
- Security headers (X-Content-Type-Options, X-Frame-Options, etc.) are set

### Dependency Management

- Automated dependency scanning via Dependabot
- Regular manual dependency audits
- All dependencies are pinned to specific versions
- License compliance checks are performed on all dependencies

### Monitoring & Incident Response

- Centralized logging with audit trails for all sensitive operations
- Real-time alerting for suspicious activity
- Automated incident response playbooks
- Regular security reviews and penetration testing

## Security Best Practices for Contributors

When contributing to this project, please follow these security guidelines:

1. **Never commit secrets** — API keys, passwords, tokens, or certificates
2. **Validate all inputs** — both client-side and server-side
3. **Use parameterized queries** — never concatenate SQL strings
4. **Sanitize output** — prevent XSS by escaping user-generated content
5. **Follow the principle of least privilege** — request only necessary permissions
6. **Keep dependencies updated** — run `npm audit` before submitting PRs
7. **Review your code** for security issues before submitting

## Security-Related Configuration

### Environment Variables

The following environment variables should be set in production:

```bash
# Database
DATABASE_URL=postgresql://...
DATABASE_SSL_MODE=require

# Authentication
JWT_SECRET=<strong-random-secret>
JWT_EXPIRATION=24h
BCRYPT_ROUNDS=12

# Encryption
ENCRYPTION_KEY=<32-byte-hex-key>
ENCRYPTION_IV=<16-byte-hex-iv>

# API Security
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=100
CORS_ORIGIN=https://app.grc-claw.com

# Logging
LOG_LEVEL=info
AUDIT_LOG_ENABLED=true
```

### Security Headers

The following security headers are set by default:

```
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

## Vulnerability Disclosure Policy

We follow a coordinated vulnerability disclosure process:

1. **Private reporting** — vulnerabilities are reported privately
2. **Assessment** — our security team assesses the vulnerability
3. **Fix development** — a fix is developed and tested
4. **Coordinated disclosure** — the vulnerability is disclosed publicly after a fix is available
5. **Credit** — reporters are credited in the release notes (unless they prefer to remain anonymous)

We aim to disclose vulnerabilities within 90 days of the initial report, depending on the complexity of the fix.

## Security Contacts

- **Security Team**: [team@grc-claw.com](mailto:team@grc-claw.com)
- **GitHub Security Advisories**: [Report a vulnerability](https://github.com/GRC_Claw/recruitment-platform/security/advisories/new)

## Attribution

This security policy is based on best practices from the [OpenSSF](https://openssf.org/) and [OWASP](https://owasp.org/) guidelines.

---

Last updated: 2026-10-03
