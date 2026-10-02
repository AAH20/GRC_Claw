"""SEO agent for auditing and optimizing search engine visibility."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class SEOIssueSeverity(StrEnum):
    """Severity levels for SEO issues."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class SEOIssue:
    """An SEO issue found during audit.

    Attributes:
        code: Issue identifier code.
        severity: Issue severity level.
        message: Human-readable description.
        recommendation: Suggested fix.
    """

    code: str
    severity: SEOIssueSeverity
    message: str
    recommendation: str


@dataclass
class SEOResult:
    """Result of an SEO audit.

    Attributes:
        url: Audited page URL.
        score: Overall SEO score (0-100).
        issues: List of found issues.
        meta_tags: Extracted meta tags.
        structured_data: Detected structured data.
    """

    url: str
    score: float
    issues: list[SEOIssue] = field(default_factory=list)
    meta_tags: dict[str, str] = field(default_factory=dict)
    structured_data: list[dict[str, Any]] = field(default_factory=list)


class SEOAgent:
    """Agent for auditing and optimizing SEO.

    This agent checks meta tags, structured data, content quality,
    and technical SEO factors to improve search engine visibility.
    """

    def __init__(self, max_audit_depth: int = 3, check_mobile_friendly: bool = True) -> None:
        """Initialize the SEO agent.

        Args:
            max_audit_depth: Maximum depth for crawling internal links.
            check_mobile_friendly: Whether to check mobile-friendliness.
        """
        self._max_audit_depth = max_audit_depth
        self._check_mobile_friendly = check_mobile_friendly
        logger.info(
            "SEOAgent initialized",
            max_audit_depth=max_audit_depth,
            check_mobile_friendly=check_mobile_friendly,
        )

    def audit_page(self, url: str, html_content: str | None = None) -> SEOResult:
        """Run a full SEO audit on a page.

        Args:
            url: The page URL to audit.
            html_content: Optional pre-fetched HTML content.

        Returns:
            SEO audit result with score and issues.
        """
        logger.info("Starting SEO audit", url=url)

        if html_content is None:
            html_content = self._fetch_page(url)

        issues: list[SEOIssue] = []
        meta_tags = self._extract_meta_tags(html_content)
        structured_data = self._extract_structured_data(html_content)

        title_issues = self._check_title(meta_tags)
        issues.extend(title_issues)

        desc_issues = self._check_meta_description(meta_tags)
        issues.extend(desc_issues)

        heading_issues = self._check_headings(html_content)
        issues.extend(heading_issues)

        image_issues = self._check_image_alt_text(html_content)
        issues.extend(image_issues)

        if not structured_data:
            issues.append(
                SEOIssue(
                    code="NO_STRUCTURED_DATA",
                    severity=SEOIssueSeverity.WARNING,
                    message="No structured data (JSON-LD) found",
                    recommendation="Add schema.org structured data for rich snippets",
                )
            )

        if self._check_mobile_friendly:
            mobile_issues = self._check_mobile_friendly(html_content)
            issues.extend(mobile_issues)

        score = self._calculate_score(issues)

        result = SEOResult(
            url=url,
            score=score,
            issues=issues,
            meta_tags=meta_tags,
            structured_data=structured_data,
        )

        logger.info("SEO audit completed", url=url, score=score, issue_count=len(issues))
        return result

    def get_optimization_suggestions(self, result: SEOResult) -> list[str]:
        """Get actionable optimization suggestions from an audit result.

        Args:
            result: The SEO audit result.

        Returns:
            List of optimization suggestions.
        """
        suggestions: list[str] = []
        for issue in result.issues:
            if issue.severity in (SEOIssueSeverity.CRITICAL, SEOIssueSeverity.WARNING):
                suggestions.append(f"[{issue.severity.value.upper()}] {issue.recommendation}")
        return suggestions

    def _fetch_page(self, url: str) -> str:
        """Fetch page HTML content.

        Args:
            url: The page URL.

        Returns:
            HTML content string.
        """
        logger.debug("Fetching page content", url=url)
        return ""

    def _extract_meta_tags(self, html: str) -> dict[str, str]:
        """Extract meta tags from HTML.

        Args:
            html: HTML content.

        Returns:
            Dictionary of meta tag name to content.
        """
        meta_tags: dict[str, str] = {}
        pattern = r'<meta\s+(?:name|property)="([^"]+)"\s+content="([^"]*)"'
        for match in re.finditer(pattern, html, re.IGNORECASE):
            meta_tags[match.group(1)] = match.group(2)
        return meta_tags

    def _extract_structured_data(self, html: str) -> list[dict[str, Any]]:
        """Extract JSON-LD structured data from HTML.

        Args:
            html: HTML content.

        Returns:
            List of structured data objects.
        """
        structured_data: list[dict[str, Any]] = []
        pattern = r'<script\s+type="application/ld\+json">\s*(.*?)\s*</script>'
        import json

        for match in re.finditer(pattern, html, re.DOTALL | re.IGNORECASE):
            try:
                data = json.loads(match.group(1))
                structured_data.append(data)
            except (json.JSONDecodeError, ValueError):
                logger.warning("Failed to parse structured data")
        return structured_data

    def _check_title(self, meta_tags: dict[str, str]) -> list[SEOIssue]:
        """Check title tag for SEO issues."""
        issues: list[SEOIssue] = []
        title = meta_tags.get("title", "")

        if not title:
            issues.append(
                SEOIssue(
                    code="MISSING_TITLE",
                    severity=SEOIssueSeverity.CRITICAL,
                    message="Missing title tag",
                    recommendation="Add a descriptive title tag (50-60 characters)",
                )
            )
        elif len(title) < 30:
            issues.append(
                SEOIssue(
                    code="SHORT_TITLE",
                    severity=SEOIssueSeverity.WARNING,
                    message=f"Title is too short ({len(title)} characters)",
                    recommendation="Expand title to 50-60 characters with relevant keywords",
                )
            )
        elif len(title) > 60:
            issues.append(
                SEOIssue(
                    code="LONG_TITLE",
                    severity=SEOIssueSeverity.WARNING,
                    message=f"Title is too long ({len(title)} characters)",
                    recommendation="Shorten title to 50-60 characters",
                )
            )

        return issues

    def _check_meta_description(self, meta_tags: dict[str, str]) -> list[SEOIssue]:
        """Check meta description for SEO issues."""
        issues: list[SEOIssue] = []
        description = meta_tags.get("description", "")

        if not description:
            issues.append(
                SEOIssue(
                    code="MISSING_DESCRIPTION",
                    severity=SEOIssueSeverity.CRITICAL,
                    message="Missing meta description",
                    recommendation="Add a compelling meta description (150-160 characters)",
                )
            )
        elif len(description) < 120:
            issues.append(
                SEOIssue(
                    code="SHORT_DESCRIPTION",
                    severity=SEOIssueSeverity.WARNING,
                    message=f"Meta description is too short ({len(description)} characters)",
                    recommendation="Expand description to 150-160 characters",
                )
            )
        elif len(description) > 160:
            issues.append(
                SEOIssue(
                    code="LONG_DESCRIPTION",
                    severity=SEOIssueSeverity.WARNING,
                    message=f"Meta description is too long ({len(description)} characters)",
                    recommendation="Shorten description to 150-160 characters",
                )
            )

        return issues

    def _check_headings(self, html: str) -> list[SEOIssue]:
        """Check heading structure for SEO issues."""
        issues: list[SEOIssue] = []
        h1_pattern = r"<h1[^>]*>(.*?)</h1>"
        h1_matches = re.findall(h1_pattern, html, re.IGNORECASE | re.DOTALL)

        if len(h1_matches) == 0:
            issues.append(
                SEOIssue(
                    code="MISSING_H1",
                    severity=SEOIssueSeverity.CRITICAL,
                    message="Missing H1 heading",
                    recommendation="Add a single H1 heading with the primary keyword",
                )
            )
        elif len(h1_matches) > 1:
            issues.append(
                SEOIssue(
                    code="MULTIPLE_H1",
                    severity=SEOIssueSeverity.WARNING,
                    message=f"Multiple H1 headings found ({len(h1_matches)})",
                    recommendation="Use only one H1 heading per page",
                )
            )

        return issues

    def _check_image_alt_text(self, html: str) -> list[SEOIssue]:
        """Check image alt text for SEO issues."""
        issues: list[SEOIssue] = []
        img_pattern = r"<img[^>]*>"
        img_tags = re.findall(img_pattern, html, re.IGNORECASE)

        images_without_alt = 0
        for img in img_tags:
            if 'alt=""' in img or "alt=" not in img:
                images_without_alt += 1

        if images_without_alt > 0:
            issues.append(
                SEOIssue(
                    code="MISSING_ALT_TEXT",
                    severity=SEOIssueSeverity.WARNING,
                    message=f"{images_without_alt} image(s) missing alt text",
                    recommendation="Add descriptive alt text to all images",
                )
            )

        return issues

    def _check_mobile_friendly(self, html: str) -> list[SEOIssue]:
        """Check mobile-friendliness of the page."""
        issues: list[SEOIssue] = []

        viewport_pattern = r'<meta\s+name="viewport"\s+content="([^"]*)"'
        viewport_match = re.search(viewport_pattern, html, re.IGNORECASE)

        if not viewport_match:
            issues.append(
                SEOIssue(
                    code="MISSING_VIEWPORT",
                    severity=SEOIssueSeverity.CRITICAL,
                    message="Missing viewport meta tag",
                    recommendation=(
                        'Add <meta name="viewport" content="width=device-width, initial-scale=1">'
                    ),
                )
            )

        return issues

    def _calculate_score(self, issues: list[SEOIssue]) -> float:
        """Calculate overall SEO score from issues."""
        score = 100.0
        for issue in issues:
            if issue.severity == SEOIssueSeverity.CRITICAL:
                score -= 15.0
            elif issue.severity == SEOIssueSeverity.WARNING:
                score -= 5.0
            elif issue.severity == SEOIssueSeverity.INFO:
                score -= 1.0
        return max(score, 0.0)
