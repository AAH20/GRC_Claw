"""Security testing framework for marketing systems.

This module provides security testing capabilities including:
- Authentication and authorization testing
- Input validation testing
- Rate limiting verification
- Data exposure testing
- Security header validation
- Vulnerability scanning helpers
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class Severity(Enum):
    """Security issue severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SecurityTestCategory(Enum):
    """Categories of security tests."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    INPUT_VALIDATION = "input_validation"
    RATE_LIMITING = "rate_limiting"
    DATA_EXPOSURE = "data_exposure"
    HEADERS = "headers"
    ENCRYPTION = "encryption"
    SESSION = "session"


@dataclass
class SecurityFinding:
    """Represents a security finding.

    Attributes:
        finding_id: Unique finding identifier.
        title: Short title of the finding.
        description: Detailed description.
        severity: Severity level.
        category: Security test category.
        location: Where the finding was detected.
        evidence: Evidence supporting the finding.
        remediation: Recommended fix.
        cwe_id: Optional CWE identifier.
        references: List of reference URLs.
    """

    finding_id: str
    title: str
    description: str
    severity: Severity
    category: SecurityTestCategory
    location: str = ""
    evidence: str = ""
    remediation: str = ""
    cwe_id: str | None = None
    references: list[str] = field(default_factory=list)


@dataclass
class SecurityTestResult:
    """Result of a security test run.

    Attributes:
        test_name: Name of the test.
        category: Test category.
        findings: List of security findings.
        passed: Whether the test passed (no critical/high findings).
        duration_seconds: Test execution duration.
        metadata: Additional test metadata.
    """

    test_name: str
    category: SecurityTestCategory
    findings: list[SecurityFinding] = field(default_factory=list)
    passed: bool = True
    duration_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def critical_count(self) -> int:
        """Count of critical findings."""
        return sum(1 for f in self.findings if f.severity == Severity.CRITICAL)

    @property
    def high_count(self) -> int:
        """Count of high findings."""
        return sum(1 for f in self.findings if f.severity == Severity.HIGH)

    @property
    def medium_count(self) -> int:
        """Count of medium findings."""
        return sum(1 for f in self.findings if f.severity == Severity.MEDIUM)

    @property
    def low_count(self) -> int:
        """Count of low findings."""
        return sum(1 for f in self.findings if f.severity == Severity.LOW)


class SecurityTarget(ABC):
    """Abstract base class for security test targets."""

    @abstractmethod
    async def authenticate(self, credentials: dict[str, str]) -> bool:
        """Attempt authentication.

        Args:
            credentials: Authentication credentials.

        Returns:
            True if authentication succeeded.
        """
        ...

    @abstractmethod
    async def send_request(
        self, method: str, path: str, headers: dict[str, str] | None = None,
        body: str | None = None,
    ) -> dict[str, Any]:
        """Send a request to the target.

        Args:
            method: HTTP method.
            path: Request path.
            headers: Optional headers.
            body: Optional request body.

        Returns:
            Response dictionary with status_code, headers, body.
        """
        ...

    @abstractmethod
    async def get_headers(self, path: str = "/") -> dict[str, str]:
        """Get response headers for a path.

        Args:
            path: The path to check.

        Returns:
            Dictionary of response headers.
        """
        ...


class AuthenticationTester:
    """Tests authentication mechanisms."""

    def __init__(self, target: SecurityTarget) -> None:
        """Initialize AuthenticationTester.

        Args:
            target: The security target.
        """
        self.target = target

    async def test_weak_credentials(self) -> list[SecurityFinding]:
        """Test for weak/default credentials.

        Returns:
            List of findings.
        """
        findings: list[SecurityFinding] = []
        common_creds = [
            {"username": "admin", "password": "admin"},
            {"username": "admin", "password": "password"},
            {"username": "admin", "password": "123456"},
            {"username": "test", "password": "test"},
            {"username": "user", "password": "user"},
        ]

        for creds in common_creds:
            try:
                success = await self.target.authenticate(creds)
                if success:
                    findings.append(
                        SecurityFinding(
                            finding_id="AUTH-001",
                            title="Weak credentials accepted",
                            description=(
                                f"System accepted weak credentials: "
                                f"{creds['username']}/{creds['password']}"
                            ),
                            severity=Severity.CRITICAL,
                            category=SecurityTestCategory.AUTHENTICATION,
                            evidence=f"Authentication succeeded with {creds}",
                            remediation="Enforce strong password policy",
                            cwe_id="CWE-521",
                        )
                    )
                    break
            except Exception:
                continue

        return findings

    async def test_brute_force_protection(self) -> list[SecurityFinding]:
        """Test for brute force protection.

        Returns:
            List of findings.
        """
        findings: list[SecurityFinding] = []
        attempts = 10
        success_count = 0

        for i in range(attempts):
            try:
                success = await self.target.authenticate(
                    {"username": "testuser", "password": f"wrong{i}"}
                )
                if success:
                    success_count += 1
            except Exception:
                break

        if success_count == attempts:
            findings.append(
                SecurityFinding(
                    finding_id="AUTH-002",
                    title="No brute force protection",
                    description=(
                        f"System allowed {attempts} failed login attempts "
                        "without lockout or rate limiting"
                    ),
                    severity=Severity.HIGH,
                    category=SecurityTestCategory.AUTHENTICATION,
                    evidence=f"{attempts} consecutive failed attempts allowed",
                    remediation="Implement account lockout and rate limiting",
                    cwe_id="CWE-307",
                )
            )

        return findings


class AuthorizationTester:
    """Tests authorization mechanisms."""

    def __init__(self, target: SecurityTarget) -> None:
        """Initialize AuthorizationTester.

        Args:
            target: The security target.
        """
        self.target = target

    async def test_horizontal_privilege_escalation(self) -> list[SecurityFinding]:
        """Test for horizontal privilege escalation.

        Returns:
            List of findings.
        """
        findings: list[SecurityFinding] = []

        test_paths = [
            "/api/users/1/profile",
            "/api/users/2/profile",
            "/api/orders/12345",
            "/api/campaigns/other-user-campaign",
        ]

        for path in test_paths:
            try:
                response = await self.target.send_request("GET", path)
                if response.get("status_code") == 200:
                    findings.append(
                        SecurityFinding(
                            finding_id="AUTHZ-001",
                            title="Horizontal privilege escalation",
                            description=f"Unauthorized access to {path}",
                            severity=Severity.CRITICAL,
                            category=SecurityTestCategory.AUTHORIZATION,
                            location=path,
                            evidence=f"Received 200 response for {path}",
                            remediation="Implement proper authorization checks",
                            cwe_id="CWE-639",
                        )
                    )
            except Exception:
                continue

        return findings

    async def test_vertical_privilege_escalation(self) -> list[SecurityFinding]:
        """Test for vertical privilege escalation.

        Returns:
            List of findings.
        """
        findings: list[SecurityFinding] = []

        admin_paths = [
            "/api/admin/users",
            "/api/admin/settings",
            "/api/admin/billing",
        ]

        for path in admin_paths:
            try:
                response = await self.target.send_request("GET", path)
                if response.get("status_code") == 200:
                    findings.append(
                        SecurityFinding(
                            finding_id="AUTHZ-002",
                            title="Vertical privilege escalation",
                            description=f"Admin access granted for {path}",
                            severity=Severity.CRITICAL,
                            category=SecurityTestCategory.AUTHORIZATION,
                            location=path,
                            evidence=f"Received 200 response for {path}",
                            remediation="Implement role-based access control",
                            cwe_id="CWE-284",
                        )
                    )
            except Exception:
                continue

        return findings


class InputValidationTester:
    """Tests input validation."""

    def __init__(self, target: SecurityTarget) -> None:
        """Initialize InputValidationTester.

        Args:
            target: The security target.
        """
        self.target = target

    async def test_sql_injection(self) -> list[SecurityFinding]:
        """Test for SQL injection vulnerabilities.

        Returns:
            List of findings.
        """
        findings: list[SecurityFinding] = []
        payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "1' UNION SELECT * FROM users--",
            "' OR 1=1--",
        ]

        test_paths = ["/api/search", "/api/users", "/api/campaigns"]

        for path in test_paths:
            for payload in payloads:
                try:
                    response = await self.target.send_request(
                        "GET", f"{path}?q={payload}"
                    )
                    body = response.get("body", "")
                    if any(
                        indicator in body.lower()
                        for indicator in ["sql", "mysql", "sqlite", "postgresql", "error"]
                    ):
                        findings.append(
                            SecurityFinding(
                                finding_id="INPV-001",
                                title="SQL injection vulnerability",
                                description=f"SQL injection possible at {path}",
                                severity=Severity.CRITICAL,
                                category=SecurityTestCategory.INPUT_VALIDATION,
                                location=path,
                                evidence=f"Payload: {payload}",
                                remediation="Use parameterized queries",
                                cwe_id="CWE-89",
                            )
                        )
                        break
                except Exception:
                    continue

        return findings

    async def test_xss(self) -> list[SecurityFinding]:
        """Test for cross-site scripting vulnerabilities.

        Returns:
            List of findings.
        """
        findings: list[SecurityFinding] = []
        payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
        ]

        test_paths = ["/api/search", "/api/comments", "/api/feedback"]

        for path in test_paths:
            for payload in payloads:
                try:
                    response = await self.target.send_request(
                        "GET", f"{path}?q={payload}"
                    )
                    body = response.get("body", "")
                    if payload in body:
                        findings.append(
                            SecurityFinding(
                                finding_id="INPV-002",
                                title="Cross-site scripting (XSS)",
                                description=f"XSS vulnerability at {path}",
                                severity=Severity.HIGH,
                                category=SecurityTestCategory.INPUT_VALIDATION,
                                location=path,
                                evidence=f"Payload reflected: {payload}",
                                remediation="Implement output encoding and CSP",
                                cwe_id="CWE-79",
                            )
                        )
                        break
                except Exception:
                    continue

        return findings


class RateLimitTester:
    """Tests rate limiting."""

    def __init__(self, target: SecurityTarget) -> None:
        """Initialize RateLimitTester.

        Args:
            target: The security target.
        """
        self.target = target

    async def test_rate_limiting(
        self, requests_count: int = 100, time_window_seconds: float = 60.0
    ) -> list[SecurityFinding]:
        """Test if rate limiting is enforced.

        Args:
            requests_count: Number of requests to send.
            time_window_seconds: Time window for the requests.

        Returns:
            List of findings.
        """
        findings: list[SecurityFinding] = []
        success_count = 0

        for i in range(requests_count):
            try:
                response = await self.target.send_request("GET", "/api/data")
                if response.get("status_code") == 200:
                    success_count += 1
                elif response.get("status_code") == 429:
                    break
            except Exception:
                break

        if success_count >= requests_count:
            findings.append(
                SecurityFinding(
                    finding_id="RATE-001",
                    title="No rate limiting enforced",
                    description=(
                        f"System allowed {requests_count} requests without "
                        "rate limiting"
                    ),
                    severity=Severity.MEDIUM,
                    category=SecurityTestCategory.RATE_LIMITING,
                    evidence=f"{success_count} successful requests in {time_window_seconds}s",
                    remediation="Implement rate limiting",
                    cwe_id="CWE-770",
                )
            )

        return findings


class SecurityHeaderTester:
    """Tests security headers."""

    REQUIRED_HEADERS: dict[str, str] = {
        "Strict-Transport-Security": "HSTS",
        "X-Content-Type-Options": "MIME sniffing protection",
        "X-Frame-Options": "Clickjacking protection",
        "Content-Security-Policy": "CSP",
        "X-XSS-Protection": "XSS filter",
        "Referrer-Policy": "Referrer policy",
    }

    def __init__(self, target: SecurityTarget) -> None:
        """Initialize SecurityHeaderTester.

        Args:
            target: The security target.
        """
        self.target = target

    async def test_security_headers(self) -> list[SecurityFinding]:
        """Test for required security headers.

        Returns:
            List of findings.
        """
        findings: list[SecurityFinding] = []

        try:
            headers = await self.target.get_headers()
            headers_lower = {k.lower(): v for k, v in headers.items()}

            for header, description in self.REQUIRED_HEADERS.items():
                if header.lower() not in headers_lower:
                    findings.append(
                        SecurityFinding(
                            finding_id="HEAD-001",
                            title=f"Missing security header: {header}",
                            description=f"Security header {header} is not set",
                            severity=Severity.MEDIUM,
                            category=SecurityTestCategory.HEADERS,
                            evidence=f"Header {header} not found in response",
                            remediation=f"Set {header} header for {description}",
                        )
                    )
        except Exception as e:
            findings.append(
                SecurityFinding(
                    finding_id="HEAD-002",
                    title="Failed to retrieve headers",
                    description=f"Could not retrieve response headers: {e}",
                    severity=Severity.LOW,
                    category=SecurityTestCategory.HEADERS,
                )
            )

        return findings


class SecurityTestRunner:
    """Runs all security tests."""

    def __init__(self, target: SecurityTarget) -> None:
        """Initialize SecurityTestRunner.

        Args:
            target: The security target.
        """
        self.target = target
        self._results: list[SecurityTestResult] = []

    async def run_all(self) -> list[SecurityTestResult]:
        """Run all security tests.

        Returns:
            List of test results.
        """
        self._results = []

        auth_tester = AuthenticationTester(self.target)
        start = time.monotonic()
        findings: list[SecurityFinding] = []
        findings.extend(await auth_tester.test_weak_credentials())
        findings.extend(await auth_tester.test_brute_force_protection())
        self._results.append(
            SecurityTestResult(
                test_name="Authentication Tests",
                category=SecurityTestCategory.AUTHENTICATION,
                findings=findings,
                passed=not any(
                    f.severity in (Severity.CRITICAL, Severity.HIGH)
                    for f in findings
                ),
                duration_seconds=time.monotonic() - start,
            )
        )

        authz_tester = AuthorizationTester(self.target)
        start = time.monotonic()
        findings = []
        findings.extend(await authz_tester.test_horizontal_privilege_escalation())
        findings.extend(await authz_tester.test_vertical_privilege_escalation())
        self._results.append(
            SecurityTestResult(
                test_name="Authorization Tests",
                category=SecurityTestCategory.AUTHORIZATION,
                findings=findings,
                passed=not any(
                    f.severity in (Severity.CRITICAL, Severity.HIGH)
                    for f in findings
                ),
                duration_seconds=time.monotonic() - start,
            )
        )

        inv_tester = InputValidationTester(self.target)
        start = time.monotonic()
        findings = []
        findings.extend(await inv_tester.test_sql_injection())
        findings.extend(await inv_tester.test_xss())
        self._results.append(
            SecurityTestResult(
                test_name="Input Validation Tests",
                category=SecurityTestCategory.INPUT_VALIDATION,
                findings=findings,
                passed=not any(
                    f.severity in (Severity.CRITICAL, Severity.HIGH)
                    for f in findings
                ),
                duration_seconds=time.monotonic() - start,
            )
        )

        rate_tester = RateLimitTester(self.target)
        start = time.monotonic()
        findings = await rate_tester.test_rate_limiting()
        self._results.append(
            SecurityTestResult(
                test_name="Rate Limiting Tests",
                category=SecurityTestCategory.RATE_LIMITING,
                findings=findings,
                passed=not any(
                    f.severity in (Severity.CRITICAL, Severity.HIGH)
                    for f in findings
                ),
                duration_seconds=time.monotonic() - start,
            )
        )

        header_tester = SecurityHeaderTester(self.target)
        start = time.monotonic()
        findings = await header_tester.test_security_headers()
        self._results.append(
            SecurityTestResult(
                test_name="Security Headers Tests",
                category=SecurityTestCategory.HEADERS,
                findings=findings,
                passed=True,
                duration_seconds=time.monotonic() - start,
            )
        )

        return self._results

    def get_summary(self) -> dict[str, Any]:
        """Get summary of all security test results.

        Returns:
            Dictionary with summary statistics.
        """
        if not self._results:
            return {"total": 0, "passed": 0, "failed": 0, "findings": 0}

        total_findings = sum(len(r.findings) for r in self._results)
        critical = sum(r.critical_count for r in self._results)
        high = sum(r.high_count for r in self._results)
        medium = sum(r.medium_count for r in self._results)
        low = sum(r.low_count for r in self._results)

        return {
            "total_tests": len(self._results),
            "passed": sum(1 for r in self._results if r.passed),
            "failed": sum(1 for r in self._results if not r.passed),
            "total_findings": total_findings,
            "critical": critical,
            "high": high,
            "medium": medium,
            "low": low,
        }
