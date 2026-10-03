"""Tests for role management workflows."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from access_control.agents.role_manager import RoleManagerAgent
from access_control.config import Settings
from access_control.models.enums import RoleStatus
from access_control.models.schemas import Permission, RoleCreate


@pytest.fixture
def mock_llm() -> MagicMock:
    """Create a mock LLM."""
    return MagicMock()


@pytest.fixture
def settings() -> Settings:
    """Create test settings."""
    return Settings(app_env="development", secret_key="test", openai_api_key="test")


class TestRoles:
    """Test suite for role management workflows."""

    @pytest.mark.asyncio
    async def test_create_role(self, mock_llm: MagicMock, settings: Settings) -> None:
        """Test creating a role."""
        mock_response = MagicMock()
        mock_response.content = '{"success": true, "role": {"name": "test-role", "status": "active"}, "message": "Created"}'  # noqa: E501
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_response)

        agent = RoleManagerAgent(llm=mock_llm, settings=settings)
        agent._build_agent = MagicMock(return_value=mock_chain)

        role_create = RoleCreate(
            name="test-role",
            description="Test role",
            permissions=[Permission(resource="documents", action="read")],
        )
        role = await agent.create_role(role_create)

        assert role.name == "test-role"
        assert role.status == RoleStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_create_role_failure(
        self, mock_llm: MagicMock, settings: Settings
    ) -> None:
        """Test role creation failure."""
        mock_response = MagicMock()
        mock_response.content = '{"success": false, "message": "Invalid permissions"}'
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_response)

        agent = RoleManagerAgent(llm=mock_llm, settings=settings)
        agent._build_agent = MagicMock(return_value=mock_chain)

        role_create = RoleCreate(name="test-role")

        with pytest.raises(ValueError, match="Role creation failed"):
            await agent.create_role(role_create)

    @pytest.mark.asyncio
    async def test_update_role(self, mock_llm: MagicMock, settings: Settings) -> None:
        """Test updating a role."""
        mock_response = MagicMock()
        mock_response.content = '{"success": true, "role": {"name": "updated-role", "status": "active"}, "message": "Updated"}'  # noqa: E501
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_response)

        agent = RoleManagerAgent(llm=mock_llm, settings=settings)
        agent._build_agent = MagicMock(return_value=mock_chain)

        from access_control.models.schemas import RoleUpdate

        role_update = RoleUpdate(name="updated-role")
        role = await agent.update_role("role-1", role_update)

        assert role.name == "updated-role"

    @pytest.mark.asyncio
    async def test_validate_role(self, mock_llm: MagicMock, settings: Settings) -> None:
        """Test role validation."""
        mock_response = MagicMock()
        mock_response.content = '{"success": true, "validation_errors": []}'
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_response)

        agent = RoleManagerAgent(llm=mock_llm, settings=settings)
        agent._build_agent = MagicMock(return_value=mock_chain)

        permissions = [Permission(resource="documents", action="read")]
        errors = await agent.validate_role(permissions)

        assert errors == []

    @pytest.mark.asyncio
    async def test_suggest_permissions(
        self, mock_llm: MagicMock, settings: Settings
    ) -> None:
        """Test permission suggestions."""
        mock_response = MagicMock()
        mock_response.content = '{"success": true, "role": {"permissions": [{"resource": "documents", "action": "read"}]}}'  # noqa: E501
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_response)

        agent = RoleManagerAgent(llm=mock_llm, settings=settings)
        agent._build_agent = MagicMock(return_value=mock_chain)

        suggestions = await agent.suggest_permissions("viewer", "Can view documents")

        assert len(suggestions) > 0
        assert suggestions[0].resource == "documents"
