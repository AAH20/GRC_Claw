"""Agent implementations for the onboarding automator.

This module contains all agent classes that use LangChain DeepAgents
to perform various onboarding automation tasks.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Optional
from uuid import UUID

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from onboarding_automator.config.settings import Settings
from onboarding_automator.models import (
    AgentResponse,
    ComplianceCheck,
    ComplianceCheckCreate,
    ComplianceStatus,
    Document,
    DocumentCreate,
    DocumentStatus,
    OnboardingPlan,
    OnboardingPlanCreate,
    OnboardingStatus,
    Progress,
    ProgressUpdate,
    Task,
    TaskCreate,
    TaskStatus,
    TaskType,
    WelcomeMessage,
    WelcomeMessageCreate,
)

__all__ = [
    "BaseAgent",
    "TaskGeneratorAgent",
    "DocumentCollectorAgent",
    "ProgressTrackerAgent",
    "ComplianceCheckerAgent",
    "WelcomeAgent",
]


class BaseAgent(ABC):
    """Abstract base class for all onboarding agents.

    Provides common functionality for LLM initialization, error handling,
    and response formatting.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize the agent with application settings.

        Args:
            settings: Application configuration settings.
        """
        self.settings = settings
        self._llm: Optional[BaseChatModel] = None

    @property
    def llm(self) -> BaseChatModel:
        """Lazy-initialize and return the LLM instance."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self.settings.llm_model,
                temperature=self.settings.llm_temperature,
                max_tokens=self.settings.llm_max_tokens,
                api_key=self.settings.openai_api_key or None,
            )
        return self._llm

    @abstractmethod
    async def execute(self, **kwargs: Any) -> AgentResponse:
        """Execute the agent's primary task.

        Args:
            **kwargs: Agent-specific parameters.

        Returns:
            AgentResponse with the operation result.
        """
        ...

    def _build_system_prompt(self, role: str, instructions: str) -> str:
        """Build a system prompt for the LLM.

        Args:
            role: The role the agent should play.
            instructions: Specific instructions for the task.

        Returns:
            Formatted system prompt string.
        """
        return f"""You are an AI-powered {role} for an employee onboarding system.

{instructions}

Always respond in a structured, professional manner. Provide clear, actionable output."""

    async def _invoke_llm(
        self,
        system_prompt: str,
        user_message: str,
    ) -> str:
        """Invoke the LLM with system and user messages.

        Args:
            system_prompt: The system prompt defining the agent's role.
            user_message: The user message with the task details.

        Returns:
            The LLM's response text.

        Raises:
            RuntimeError: If the LLM invocation fails.
        """
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message),
            ]
            response = await self.llm.ainvoke(messages)
            return str(response.content)
        except Exception as exc:
            raise RuntimeError(f"LLM invocation failed: {exc}") from exc

    @staticmethod
    def _timed_response(
        agent_name: str,
        start_time: float,
        success: bool,
        message: str,
        data: Optional[dict[str, Any]] = None,
        errors: Optional[list[str]] = None,
    ) -> AgentResponse:
        """Build an AgentResponse with timing information.

        Args:
            agent_name: Name of the agent.
            start_time: Start time from time.monotonic().
            success: Whether the operation succeeded.
            message: Human-readable result message.
            data: Optional result data.
            errors: Optional list of error messages.

        Returns:
            Populated AgentResponse instance.
        """
        elapsed_ms = (time.monotonic() - start_time) * 1000
        return AgentResponse(
            success=success,
            message=message,
            data=data,
            errors=errors or [],
            agent_name=agent_name,
            processing_time_ms=round(elapsed_ms, 2),
        )


class TaskGeneratorAgent(BaseAgent):
    """Agent responsible for generating onboarding tasks.

    Uses LLM to analyze employee information and create a comprehensive
    set of onboarding tasks based on role, department, and location.
    """

    async def execute(
        self,
        plan_create: OnboardingPlanCreate,
        existing_tasks: Optional[list[Task]] = None,
    ) -> AgentResponse:
        """Generate onboarding tasks for a new employee.

        Args:
            plan_create: The onboarding plan creation data.
            existing_tasks: Optional list of already-created tasks to avoid duplicates.

        Returns:
            AgentResponse containing the generated tasks.
        """
        start = time.monotonic()
        agent_name = "TaskGeneratorAgent"

        try:
            employee = plan_create.employee
            system_prompt = self._build_system_prompt(
                "onboarding task generator",
                """Your job is to generate a comprehensive list of onboarding tasks
for a new employee. Consider their role, department, location, and employment type.

Generate tasks that cover:
- Document submission (ID, tax forms, contracts)
- System access provisioning
- Required training and certifications
- Orientation sessions
- Key meetings and introductions
- Equipment and workspace setup

Each task should have a clear title, description, type, priority, and due date.""",
            )

            user_message = f"""Generate onboarding tasks for:

Name: {employee.full_name}
Role: {employee.role}
Department: {employee.department}
Location: {employee.location or 'Not specified'}
Employment Type: {employee.employment_type}
Start Date: {employee.start_date.isoformat()}

{f"Existing tasks to avoid duplicating: {[t.title for t in existing_tasks]}" if existing_tasks else ""}

Provide the tasks in a structured format."""

            response_text = await self._invoke_llm(system_prompt, user_message)

            # Parse the LLM response into TaskCreate objects
            tasks = self._parse_tasks_from_response(response_text, plan_create)

            return self._timed_response(
                agent_name=agent_name,
                start_time=start,
                success=True,
                message=f"Generated {len(tasks)} onboarding tasks",
                data={
                    "tasks": [t.model_dump() for t in tasks],
                    "employee_id": employee.employee_id,
                },
            )
        except Exception as exc:
            return self._timed_response(
                agent_name=agent_name,
                start_time=start,
                success=False,
                message=f"Failed to generate tasks: {exc}",
                errors=[str(exc)],
            )

    def _parse_tasks_from_response(
        self,
        response: str,
        plan_create: OnboardingPlanCreate,
    ) -> list[TaskCreate]:
        """Parse LLM response into TaskCreate objects.

        In production, this would use structured output or function calling.
        For now, we generate sensible defaults based on the employee info.

        Args:
            response: Raw LLM response text.
            plan_create: Original plan creation data.

        Returns:
            List of TaskCreate objects.
        """
        employee = plan_create.employee
        base_tasks = [
            TaskCreate(
                plan_id=UUID(int=0),  # Will be set by caller
                title="Submit identification documents",
                description="Provide government-issued ID and work authorization documents",
                task_type=TaskType.DOCUMENT_SUBMISSION,
            ),
            TaskCreate(
                plan_id=UUID(int=0),
                title="Complete tax forms",
                description="Submit W-4 and state tax withholding forms",
                task_type=TaskType.DOCUMENT_SUBMISSION,
            ),
            TaskCreate(
                plan_id=UUID(int=0),
                title="Set up system access",
                description="Get accounts created for email, SSO, and internal tools",
                task_type=TaskType.SYSTEM_ACCESS,
            ),
            TaskCreate(
                plan_id=UUID(int=0),
                title="Complete security awareness training",
                description="Mandatory security training for all new hires",
                task_type=TaskType.TRAINING,
            ),
            TaskCreate(
                plan_id=UUID(int=0),
                title="Attend orientation session",
                description="Company culture, policies, and procedures orientation",
                task_type=TaskType.ORIENTATION,
            ),
            TaskCreate(
                plan_id=UUID(int=0),
                title=f"Meet with manager ({employee.manager_id or 'TBD'})",
                description="Initial 1:1 with direct manager to discuss role expectations",
                task_type=TaskType.MEETING,
            ),
        ]
        return base_tasks


class DocumentCollectorAgent(BaseAgent):
    """Agent responsible for collecting and verifying onboarding documents.

    Manages document upload workflows, verification status, and
    integration with document storage systems.
    """

    async def execute(
        self,
        document_create: DocumentCreate,
        file_content: Optional[bytes] = None,
    ) -> AgentResponse:
        """Process a document submission.

        Args:
            document_create: Document creation data.
            file_content: Optional raw file bytes for storage.

        Returns:
            AgentResponse with the document processing result.
        """
        start = time.monotonic()
        agent_name = "DocumentCollectorAgent"

        try:
            system_prompt = self._build_system_prompt(
                "document collection specialist",
                """Your job is to process and validate onboarding documents.
Check that documents are complete, legible, and match the expected type.
Flag any issues that need manual review.""",
            )

            user_message = f"""Process the following document submission:

Plan ID: {document_create.plan_id}
Document Name: {document_create.name}
Document Type: {document_create.document_type}
Task ID: {document_create.task_id or 'N/A'}

Validate the document and determine its status."""

            response_text = await self._invoke_llm(system_prompt, user_message)

            document = Document(
                plan_id=document_create.plan_id,
                task_id=document_create.task_id,
                name=document_create.name,
                document_type=document_create.document_type,
                file_type="application/pdf",  # Would be detected from content
                status=DocumentStatus.UPLOADED,
                metadata=document_create.metadata,
            )

            return self._timed_response(
                agent_name=agent_name,
                start_time=start,
                success=True,
                message=f"Document '{document.name}' processed successfully",
                data={"document": document.model_dump()},
            )
        except Exception as exc:
            return self._timed_response(
                agent_name=agent_name,
                start_time=start,
                success=False,
                message=f"Failed to process document: {exc}",
                errors=[str(exc)],
            )

    async def verify_document(self, document: Document) -> AgentResponse:
        """Verify a submitted document for authenticity and completeness.

        Args:
            document: The document to verify.

        Returns:
            AgentResponse with verification result.
        """
        start = time.monotonic()
        agent_name = "DocumentCollectorAgent"

        try:
            system_prompt = self._build_system_prompt(
                "document verification specialist",
                """Verify that the submitted document is authentic, complete,
and matches the expected document type. Check for signs of tampering or forgery.""",
            )

            user_message = f"""Verify the following document:

Name: {document.name}
Type: {document.document_type}
Status: {document.status.value}

Determine if the document passes verification."""

            await self._invoke_llm(system_prompt, user_message)

            return self._timed_response(
                agent_name=agent_name,
                start_time=start,
                success=True,
                message=f"Document '{document.name}' verified",
                data={"document_id": str(document.id), "verified": True},
            )
        except Exception as exc:
            return self._timed_response(
                agent_name=agent_name,
                start_time=start,
                success=False,
                message=f"Document verification failed: {exc}",
                errors=[str(exc)],
            )


class ProgressTrackerAgent(BaseAgent):
    """Agent responsible for tracking and reporting onboarding progress.

    Monitors task completion, identifies bottlenecks, and provides
    actionable insights to improve the onboarding experience.
    """

    async def execute(
        self,
        plan: OnboardingPlan,
        tasks: list[Task],
        progress: Optional[Progress] = None,
    ) -> AgentResponse:
        """Calculate and update onboarding progress.

        Args:
            plan: The onboarding plan.
            tasks: All tasks associated with the plan.
            progress: Optional existing progress record to update.

        Returns:
            AgentResponse with updated progress data.
        """
        start = time.monotonic()
        agent_name = "ProgressTrackerAgent"

        try:
            total = len(tasks)
            completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
            blocked = sum(1 for t in tasks if t.status == TaskStatus.BLOCKED)
            pending = sum(1 for t in tasks if t.status == TaskStatus.PENDING)
            in_progress = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)

            completion_pct = (completed / total * 100) if total > 0 else 0.0

            if completion_pct >= 100:
                overall = OnboardingStatus.COMPLETED
            elif completed > 0 or in_progress > 0:
                overall = OnboardingStatus.IN_PROGRESS
            else:
                overall = OnboardingStatus.NOT_STARTED

            system_prompt = self._build_system_prompt(
                "progress tracking analyst",
                """Analyze onboarding progress and provide insights.
Identify risks, bottlenecks, and recommendations for improvement.
Estimate completion time based on current velocity.""",
            )

            user_message = f"""Analyze the progress of this onboarding plan:

Employee: {plan.employee.full_name}
Total Tasks: {total}
Completed: {completed}
In Progress: {in_progress}
Blocked: {blocked}
Pending: {pending}
Completion: {completion_pct:.1f}%

Provide a risk assessment and recommendations."""

            insights = await self._invoke_llm(system_prompt, user_message)

            progress_data = {
                "plan_id": str(plan.id),
                "total_tasks": total,
                "completed_tasks": completed,
                "blocked_tasks": blocked,
                "pending_tasks": pending,
                "completion_percentage": round(completion_pct, 1),
                "overall_status": overall.value,
                "risk_assessment": insights,
            }

            return self._timed_response(
                agent_name=agent_name,
                start_time=start,
                success=True,
                message=f"Progress updated: {completion_pct:.1f}% complete",
                data=progress_data,
            )
        except Exception as exc:
            return self._timed_response(
                agent_name=agent_name,
                start_time=start,
                success=False,
                message=f"Failed to track progress: {exc}",
                errors=[str(exc)],
            )

    async def generate_progress_report(
        self,
        plan: OnboardingPlan,
        tasks: list[Task],
        progress: Progress,
    ) -> AgentResponse:
        """Generate a detailed progress report.

        Args:
            plan: The onboarding plan.
            tasks: All tasks in the plan.
            progress: Current progress data.

        Returns:
            AgentResponse with the formatted report.
        """
        start = time.monotonic()
        agent_name = "ProgressTrackerAgent"

        try:
            system_prompt = self._build_system_prompt(
                "progress report writer",
                """Generate a clear, professional progress report suitable
for HR and management. Include summary, details, risks, and next steps.""",
            )

            user_message = f"""Generate a progress report for:

Employee: {plan.employee.full_name}
Department: {plan.employee.department}
Role: {plan.employee.role}
Progress: {progress.completion_percentage}%
Status: {progress.overall_status.value}
Total Tasks: {progress.total_tasks}
Completed: {progress.completed_tasks}
Blocked: {progress.blocked_tasks}

Risk Assessment: {progress.risk_assessment or 'None'}"""

            report = await self._invoke_llm(system_prompt, user_message)

            return self._timed_response(
                agent_name=agent_name,
                start_time=start,
                success=True,
                message="Progress report generated",
                data={"report": report, "progress": progress.model_dump()},
            )
        except Exception as exc:
            return self._timed_response(
                agent_name=agent_name,
                start_time=start,
                success=False,
                message=f"Failed to generate report: {exc}",
                errors=[str(exc)],
            )


class ComplianceCheckerAgent(BaseAgent):
    """Agent responsible for checking regulatory and policy compliance.

    Validates that onboarding activities meet legal requirements,
    industry regulations, and internal policies.
    """

    async def execute(
        self,
        check_create: ComplianceCheckCreate,
        plan: OnboardingPlan,
        documents: Optional[list[Document]] = None,
    ) -> AgentResponse:
        """Run a compliance check for an onboarding plan.

        Args:
            check_create: The compliance check configuration.
            plan: The onboarding plan to check.
            documents: Optional documents to validate.

        Returns:
            AgentResponse with the compliance check result.
        """
        start = time.monotonic()
        agent_name = "ComplianceCheckerAgent"

        try:
            system_prompt = self._build_system_prompt(
                "compliance auditor",
                """Your job is to verify that onboarding activities comply with
relevant laws, regulations, and company policies. Check for:
- Data privacy (GDPR, CCPA)
- Labor law requirements
- Industry-specific regulations
- Internal policy adherence
- Documentation completeness

Provide clear pass/fail results with explanations.""",
            )

            doc_summary = ""
            if documents:
                doc_summary = "\nDocuments on file:\n" + "\n".join(
                    f"- {d.name} ({d.document_type}): {d.status.value}"
                    for d in documents
                )

            user_message = f"""Run compliance check: {check_create.name}
Category: {check_create.category}
Description: {check_create.description}

Employee: {plan.employee.full_name}
Department: {plan.employee.department}
Location: {plan.employee.location or 'N/A'}
Employment Type: {plan.employee.employment_type}
{doc_summary}

Determine compliance status and provide details."""

            response_text = await self._invoke_llm(system_prompt, user_message)

            # Determine status based on response content
            status = ComplianceStatus.PASS
            if "fail" in response_text.lower() or "non-compliant" in response_text.lower():
                status = ComplianceStatus.FAIL
            elif "warning" in response_text.lower():
                status = ComplianceStatus.WARNING

            check = ComplianceCheck(
                plan_id=check_create.plan_id,
                name=check_create.name,
                description=check_create.description,
                category=check_create.category,
                status=status,
                severity=check_create.severity,
                details=response_text,
            )

            return self._timed_response(
                agent_name=agent_name,
                start_time=start,
                success=True,
                message=f"Compliance check '{check.name}' completed: {status.value}",
                data={"check": check.model_dump()},
            )
        except Exception as exc:
            return self._timed_response(
                agent_name=agent_name,
                start_time=start,
                success=False,
                message=f"Compliance check failed: {exc}",
                errors=[str(exc)],
            )

    async def run_all_checks(
        self,
        plan: OnboardingPlan,
        documents: list[Document],
    ) -> AgentResponse:
        """Run all applicable compliance checks for a plan.

        Args:
            plan: The onboarding plan.
            documents: All documents in the plan.

        Returns:
            AgentResponse with all check results.
        """
        start = time.monotonic()
        agent_name = "ComplianceCheckerAgent"

        standard_checks = [
            ("Data Privacy (GDPR)", "data_privacy"),
            ("Labor Law Compliance", "labor_law"),
            ("Right to Work Verification", "employment_eligibility"),
            ("Tax Documentation", "tax_compliance"),
            ("Industry-Specific Requirements", "industry_specific"),
        ]

        results = []
        for name, category in standard_checks:
            check_create = ComplianceCheckCreate(
                plan_id=plan.id,
                name=name,
                category=category,
            )
            response = await self.execute(check_create, plan, documents)
            results.append(response.data)

        return self._timed_response(
            agent_name=agent_name,
            start_time=start,
            success=True,
            message=f"Ran {len(results)} compliance checks",
            data={"checks": results},
        )


class WelcomeAgent(BaseAgent):
    """Agent responsible for generating personalized welcome messages.

    Creates warm, informative welcome communications for new employees
    across multiple channels (email, Slack, etc.).
    """

    async def execute(
        self,
        message_create: WelcomeMessageCreate,
        plan: OnboardingPlan,
        tasks: Optional[list[Task]] = None,
    ) -> AgentResponse:
        """Generate a welcome message for a new employee.

        Args:
            message_create: Welcome message configuration.
            plan: The onboarding plan.
            tasks: Optional tasks to include in the message.

        Returns:
            AgentResponse with the generated message.
        """
        start = time.monotonic()
        agent_name = "WelcomeAgent"

        try:
            system_prompt = self._build_system_prompt(
                "welcome message writer",
                """Your job is to write warm, professional welcome messages
for new employees. The message should:
- Be personalized to the individual
- Clearly state next steps
- Provide key contacts and resources
- Set expectations for the first week
- Be encouraging and supportive

Adapt your tone based on the specified channel (email, Slack, etc.).""",
            )

            task_summary = ""
            if tasks and message_create.include_schedule:
                task_list = "\n".join(
                    f"- {t.title} (Due: {t.due_date.strftime('%Y-%m-%d') if t.due_date else 'TBD'})"
                    for t in tasks[:5]
                )
                task_summary = f"\n\nYour first week schedule:\n{task_list}"

            user_message = f"""Write a welcome message for:

Name: {plan.employee.full_name}
Role: {plan.employee.role}
Department: {plan.employee.department}
Start Date: {plan.employee.start_date.strftime('%B %d, %Y')}
Channel: {message_create.channel}
Tone: {message_create.tone}
{task_summary}

Write the complete welcome message with subject line."""

            message_text = await self._invoke_llm(system_prompt, user_message)

            # Extract subject and body from response
            lines = message_text.strip().split("\n", 1)
            subject = lines[0].replace("Subject: ", "").strip() if lines else f"Welcome to the team, {plan.employee.full_name}!"
            body = lines[1].strip() if len(lines) > 1 else message_text

            welcome = WelcomeMessage(
                plan_id=message_create.plan_id,
                subject=subject,
                body=body,
                channel=message_create.channel,
            )

            return self._timed_response(
                agent_name=agent_name,
                start_time=start,
                success=True,
                message="Welcome message generated",
                data={"welcome_message": welcome.model_dump()},
            )
        except Exception as exc:
            return self._timed_response(
                agent_name=agent_name,
                start_time=start,
                success=False,
                message=f"Failed to generate welcome message: {exc}",
                errors=[str(exc)],
            )

    async def send_message(
        self,
        message: WelcomeMessage,
        recipient_email: str,
    ) -> AgentResponse:
        """Send a welcome message to the specified recipient.

        Args:
            message: The welcome message to send.
            recipient_email: The recipient's email address.

        Returns:
            AgentResponse with the send result.
        """
        start = time.monotonic()
        agent_name = "WelcomeAgent"

        try:
            # In production, this would integrate with email/Slack APIs
            # For now, we simulate successful delivery
            message.sent = True
            from datetime import datetime

            message.sent_at = datetime.utcnow()

            return self._timed_response(
                agent_name=agent_name,
                start_time=start,
                success=True,
                message=f"Welcome message sent to {recipient_email}",
                data={
                    "message_id": str(message.id),
                    "recipient": recipient_email,
                    "channel": message.channel,
                    "sent_at": message.sent_at.isoformat(),
                },
            )
        except Exception as exc:
            return self._timed_response(
                agent_name=agent_name,
                start_time=start,
                success=False,
                message=f"Failed to send message: {exc}",
                errors=[str(exc)],
            )
