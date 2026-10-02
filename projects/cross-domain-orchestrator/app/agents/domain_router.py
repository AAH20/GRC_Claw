"""Domain Router Agent.

Routes incoming requests to the appropriate domain based on request
content, domain capabilities, and routing rules.
"""

from __future__ import annotations

import logging
from typing import Any

from app.models.domain import DomainInfo, DomainRequest, DomainResponse, DomainType

logger = logging.getLogger(__name__)


class DomainRouterAgent:
    """Agent responsible for routing requests to the correct domain.

    The router maintains a registry of available domains and uses
    configurable rules to determine the optimal domain for each request.

    Attributes:
        domains: Registry of available domains.
        routing_rules: List of routing rules for domain selection.
    """

    def __init__(self) -> None:
        """Initialize the Domain Router Agent."""
        self.domains: dict[str, DomainInfo] = {}
        self.routing_rules: list[dict[str, Any]] = []
        self._initialize_default_domains()

    def _initialize_default_domains(self) -> None:
        """Initialize the default set of domains."""
        default_domains = [
            DomainInfo(
                name="security",
                type=DomainType.SECURITY,
                description="Security operations and threat management",
                capabilities=["threat_detection", "vulnerability_scan", "incident_response"],
            ),
            DomainInfo(
                name="compliance",
                type=DomainType.COMPLIANCE,
                description="Regulatory compliance and audit management",
                capabilities=["audit", "policy_check", "reporting"],
            ),
            DomainInfo(
                name="operations",
                type=DomainType.OPERATIONS,
                description="Operational processes and infrastructure management",
                capabilities=["deployment", "monitoring", "scaling"],
            ),
            DomainInfo(
                name="finance",
                type=DomainType.FINANCE,
                description="Financial operations and budget management",
                capabilities=["budgeting", "forecasting", "reporting"],
            ),
            DomainInfo(
                name="hr",
                type=DomainType.HR,
                description="Human resources and personnel management",
                capabilities=["recruiting", "onboarding", "performance"],
            ),
        ]
        for domain in default_domains:
            self.domains[domain.name] = domain

    def register_domain(self, domain: DomainInfo) -> None:
        """Register a new domain with the router.

        Args:
            domain: Domain information to register.
        """
        self.domains[domain.name] = domain
        logger.info("Registered domain: %s (type=%s)", domain.name, domain.type)

    def unregister_domain(self, domain_name: str) -> bool:
        """Remove a domain from the router.

        Args:
            domain_name: Name of the domain to remove.

        Returns:
            True if the domain was removed, False if not found.
        """
        if domain_name in self.domains:
            del self.domains[domain_name]
            logger.info("Unregistered domain: %s", domain_name)
            return True
        return False

    def get_domain(self, name: str) -> DomainInfo | None:
        """Get domain information by name.

        Args:
            name: Domain name.

        Returns:
            Domain information or None if not found.
        """
        return self.domains.get(name)

    def list_domains(self) -> list[DomainInfo]:
        """List all registered domains.

        Returns:
            List of all registered domain information.
        """
        return list(self.domains.values())

    def route(self, request: DomainRequest) -> DomainResponse:
        """Route a request to the appropriate domain.

        Args:
            request: The domain request to route.

        Returns:
            Domain response with routing result.
        """
        logger.info(
            "Routing request %s to domain %s (action=%s)",
            request.id,
            request.domain,
            request.action,
        )

        domain = self.domains.get(request.domain)
        if domain is None:
            logger.warning("Domain not found: %s", request.domain)
            return DomainResponse(
                request_id=request.id,
                domain=request.domain,
                success=False,
                error=f"Domain '{request.domain}' not found",
            )

        if domain.status != "active":
            logger.warning("Domain %s is not active (status=%s)", request.domain, domain.status)
            return DomainResponse(
                request_id=request.id,
                domain=request.domain,
                success=False,
                error=f"Domain '{request.domain}' is not active",
            )

        # Simulate domain processing
        logger.info(
            "Successfully routed request %s to domain %s",
            request.id,
            request.domain,
        )
        return DomainResponse(
            request_id=request.id,
            domain=request.domain,
            success=True,
            data={
                "routed": True,
                "domain_type": domain.type.value,
                "capabilities": domain.capabilities,
                "action": request.action,
            },
        )

    def find_best_domain(self, action: str, capabilities: list[str]) -> str | None:
        """Find the best domain for a given action and required capabilities.

        Args:
            action: The action to perform.
            capabilities: Required capabilities.

        Returns:
            Name of the best matching domain, or None if no match found.
        """
        best_domain: str | None = None
        best_score: int = 0

        for name, domain in self.domains.items():
            if domain.status != "active":
                continue
            score = sum(1 for cap in capabilities if cap in domain.capabilities)
            if score > best_score:
                best_score = score
                best_domain = name

        return best_domain
