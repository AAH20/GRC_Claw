"""Role Manager Agent — manages role lifecycle using AI assistance."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from access_control.agents.base import AgentContext, BaseAgent
from access_control.config import Settings
from access_control.models.enums import RoleStatus
from access_control.models.schemas import Permission, Role, RoleCreate, RoleUpdate


class RoleManagerInput(BaseModel):
    """Input for the role manager agent."""

    operation: str = Field(..., description="Operation to perform: create, update, delete, validate, suggest")
    role_data: dict[str, Any] = Field(default_factory=dict)
    existing_roles: list[dict[str, Any]] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)


class RoleManagerOutput(BaseModel):
    """Output from the role manager agent."""

    success: bool
    role: dict[str, Any] | None = None
    message: str = ""
    suggestions: list[str] = Field(default_factory=list)
    validation_errors: list[str] = Field(default_factory=list)


class RoleManagerAgent(BaseAgent[RoleManagerInput, RoleManagerOutput]):
    """Agent that manages the full lifecycle of roles.

    Uses LangChain DeepAgents to assist with role creation, validation,
    updates, deletion, and permission suggestions based on organizational
    patterns and least-privilege principles.
    """

    def __init__(self, llm: BaseLanguageModel, settings: Settings) -> None:
        super().__init__(
            llm=llm,
            settings=settings,
            name="role_manager",
            description="Manages role lifecycle with AI-assisted validation and suggestions",
        )

    def _build_agent(self) -> Any:
        """Build the LangChain DeepAgents instance for role management."""
        system_prompt = """You are a role management engine for an access control system.
You help create, update, validate, and suggest roles following least-privilege principles.
When creating roles, ensure permissions are minimal and necessary.
When validating, check for conflicts, redundancies, and security issues.
Respond with a JSON object containing: success, role, message, suggestions, validation_errors."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])

        chain = prompt | self.llm
        return chain

    async def run(
        self, payload: RoleManagerInput, context: AgentContext | None = None
    ) -> RoleManagerOutput:
        """Execute a role management operation.

        Args:
            payload: The operation and associated data.
            context: Optional execution context.

        Returns:
            The result of the role management operation.
        """
        agent = self._build_agent()

        input_data = {
            "input": json.dumps({
                "operation": payload.operation,
                "role_data": payload.role_data,
                "existing_roles": payload.existing_roles,
                "context": payload.context,
            })
        }

        response = await agent.ainvoke(input_data)

        if hasattr(response, "content"):
            content = response.content
        else:
            content = str(response)

        try:
            parsed = json.loads(content)
            return RoleManagerOutput(**parsed)
        except (json.JSONDecodeError, TypeError):
            return RoleManagerOutput(
                success=False,
                message="Failed to parse agent response",
            )

    async def create_role(self, role_create: RoleCreate) -> Role:
        """Create a new role with AI-assisted validation.

        Args:
            role_create: The role creation payload.

        Returns:
            The newly created role.
        """
        payload = RoleManagerInput(
            operation="create",
            role_data=role_create.model_dump(mode="json"),
        )
        output = await self.run(payload)

        if not output.success or output.role is None:
            raise ValueError(f"Role creation failed: {output.message}")

        return Role(**output.role)

    async def update_role(self, role_id: str, role_update: RoleUpdate) -> Role:
        """Update an existing role.

        Args:
            role_id: The ID of the role to update.
            role_update: The update payload.

        Returns:
            The updated role.
        """
        payload = RoleManagerInput(
            operation="update",
            role_data={"id": role_id, **role_update.model_dump(mode="json", exclude_unset=True)},
        )
        output = await self.run(payload)

        if not output.success or output.role is None:
            raise ValueError(f"Role update failed: {output.message}")

        return Role(**output.role)

    async def validate_role(self, permissions: list[Permission]) -> list[str]:
        """Validate a set of permissions for a role.

        Args:
            permissions: The permissions to validate.

        Returns:
            A list of validation error messages (empty if valid).
        """
        payload = RoleManagerInput(
            operation="validate",
            role_data={"permissions": [p.model_dump(mode="json") for p in permissions]},
        )
        output = await self.run(payload)
        return output.validation_errors

    async def suggest_permissions(
        self, role_name: str, description: str, existing_roles: list[Role] | None = None
    ) -> list[Permission]:
        """Suggest permissions for a role based on its purpose.

        Args:
            role_name: The name of the role.
            description: A description of the role's purpose.
            existing_roles: Existing roles for context.

        Returns:
            A list of suggested permissions.
        """
        payload = RoleManagerInput(
            operation="suggest",
            role_data={"name": role_name, "description": description},
            existing_roles=[r.model_dump(mode="json") for r in (existing_roles or [])],
        )
        output = await self.run(payload)

        if output.role and "permissions" in output.role:
            return [Permission(**p) for p in output.role["permissions"]]
        return []
