"""Domain router.

Provides endpoints for domain routing and management.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from app.agents.domain_router import DomainRouterAgent
from app.models.domain import DomainInfo, DomainRequest, DomainResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# Module-level agent instance (in production, use dependency injection)
_domain_router = DomainRouterAgent()


@router.post("/route", response_model=DomainResponse)
async def route_domain_request(request: DomainRequest) -> DomainResponse:
    """Route a request to the appropriate domain.

    Args:
        request: Domain request to route.

    Returns:
        Domain routing response.
    """
    return _domain_router.route(request)


@router.get("", response_model=list[DomainInfo])
async def list_domains() -> list[DomainInfo]:
    """List all registered domains.

    Returns:
        List of all domains.
    """
    return _domain_router.list_domains()


@router.get("/{domain_name}", response_model=DomainInfo)
async def get_domain(domain_name: str) -> DomainInfo:
    """Get domain information by name.

    Args:
        domain_name: Domain name.

    Returns:
        Domain information.

    Raises:
        HTTPException: If the domain is not found.
    """
    domain = _domain_router.get_domain(domain_name)
    if domain is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domain '{domain_name}' not found",
        )
    return domain


@router.post("", response_model=DomainInfo, status_code=status.HTTP_201_CREATED)
async def register_domain(domain: DomainInfo) -> DomainInfo:
    """Register a new domain.

    Args:
        domain: Domain information to register.

    Returns:
        The registered domain.
    """
    _domain_router.register_domain(domain)
    return domain


@router.delete("/{domain_name}", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_domain(domain_name: str) -> None:
    """Unregister a domain.

    Args:
        domain_name: Domain name.

    Raises:
        HTTPException: If the domain is not found.
    """
    if not _domain_router.unregister_domain(domain_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domain '{domain_name}' not found",
        )


@router.post("/find-best")
async def find_best_domain(action: str, capabilities: list[str]) -> dict:
    """Find the best domain for an action.

    Args:
        action: The action to perform.
        capabilities: Required capabilities.

    Returns:
        Best matching domain information.
    """
    best = _domain_router.find_best_domain(action, capabilities)
    if best is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No suitable domain found",
        )
    return {"domain": best}
