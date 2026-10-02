"""Agent testing framework for validating AI agent behavior.

This module provides a comprehensive testing framework for AI agents including:
- Agent response validation
- Tool call verification
- Multi-turn conversation testing
- Agent state validation
- Error handling and recovery testing
"""

from __future__ import annotations

import asyncio
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine, Generic, TypeVar

T = TypeVar("T")


class TestResult(Enum):
    """Enumeration of possible test outcomes."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class AgentTestCase:
    """Represents a single agent test case.

    Attributes:
        name: Human-readable test name.
        description: Detailed description of what the test validates.
        input_data: Input data to send to the agent.
        expected_output: Expected output pattern or value.
        timeout_seconds: Maximum time allowed for the test.
        tags: Optional tags for categorizing tests.
        metadata: Additional metadata for the test case.
    """

    name: str
    description: str
    input_data: dict[str, Any]
    expected_output: dict[str, Any] | None = None
    timeout_seconds: float = 30.0
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentTestResult:
    """Result of executing an agent test case.

    Attributes:
        test_case: The test case that was executed.
        result: Outcome of the test.
        actual_output: Actual output from the agent.
        execution_time_seconds: Time taken to execute the test.
        error_message: Error message if the test failed.
        metadata: Additional result metadata.
    """

    test_case: AgentTestCase
    result: TestResult
    actual_output: dict[str, Any] | None = None
    execution_time_seconds: float = 0.0
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentInterface(ABC):
    """Abstract interface for AI agents being tested."""

    @abstractmethod
    async def respond(self, message: dict[str, Any]) -> dict[str, Any]:
        """Send a message to the agent and return its response.

        Args:
            message: The message to send to the agent.

        Returns:
            The agent's response.

        Raises:
            AgentError: If the agent fails to respond.
        """
        ...

    @abstractmethod
    async def reset(self) -> None:
        """Reset the agent to its initial state."""
        ...

    @abstractmethod
    async def get_state(self) -> dict[str, Any]:
        """Get the current state of the agent.

        Returns:
            Dictionary containing the agent's current state.
        """
        ...


class AgentError(Exception):
    """Exception raised when an agent encounters an error."""

    def __init__(self, message: str, recoverable: bool = False) -> None:
        """Initialize AgentError.

        Args:
            message: Error message.
            recoverable: Whether the error is recoverable.
        """
        super().__init__(message)
        self.recoverable = recoverable


class AgentValidator:
    """Validates agent responses against expected outputs."""

    def __init__(self, strict: bool = False) -> None:
        """Initialize AgentValidator.

        Args:
            strict: If True, requires exact match; otherwise uses fuzzy matching.
        """
        self.strict = strict

    def validate(
        self, actual: dict[str, Any], expected: dict[str, Any]
    ) -> tuple[bool, list[str]]:
        """Validate actual output against expected output.

        Args:
            actual: The actual output from the agent.
            expected: The expected output pattern.

        Returns:
            Tuple of (is_valid, list_of_discrepancies).
        """
        discrepancies: list[str] = []

        for key, expected_value in expected.items():
            if key not in actual:
                discrepancies.append(f"Missing key: {key}")
                continue

            actual_value = actual[key]

            if self.strict:
                if actual_value != expected_value:
                    discrepancies.append(
                        f"Value mismatch for '{key}': "
                        f"expected {expected_value!r}, got {actual_value!r}"
                    )
            else:
                if not self._fuzzy_match(actual_value, expected_value):
                    discrepancies.append(
                        f"Fuzzy match failed for '{key}': "
                        f"expected pattern {expected_value!r}, got {actual_value!r}"
                    )

        return len(discrepancies) == 0, discrepancies

    def _fuzzy_match(self, actual: Any, expected: Any) -> bool:
        """Perform fuzzy matching between actual and expected values.

        Args:
            actual: The actual value.
            expected: The expected value or pattern.

        Returns:
            True if the values match fuzzily.
        """
        if isinstance(expected, str) and isinstance(actual, str):
            return expected.lower() in actual.lower()
        if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
            return abs(actual - expected) < 1e-6
        return actual == expected


class AgentTestRunner:
    """Runner for executing agent test cases."""

    def __init__(
        self,
        agent: AgentInterface,
        validator: AgentValidator | None = None,
        max_concurrent: int = 5,
    ) -> None:
        """Initialize AgentTestRunner.

        Args:
            agent: The agent to test.
            validator: Optional custom validator.
            max_concurrent: Maximum number of concurrent tests.
        """
        self.agent = agent
        self.validator = validator or AgentValidator()
        self.max_concurrent = max_concurrent
        self._results: list[AgentTestResult] = []

    async def run_test(self, test_case: AgentTestCase) -> AgentTestResult:
        """Run a single test case.

        Args:
            test_case: The test case to execute.

        Returns:
            The result of the test execution.
        """
        start_time = time.monotonic()

        try:
            await self.agent.reset()
            actual_output = await asyncio.wait_for(
                self.agent.respond(test_case.input_data),
                timeout=test_case.timeout_seconds,
            )

            if test_case.expected_output is not None:
                is_valid, discrepancies = self.validator.validate(
                    actual_output, test_case.expected_output
                )
                result = TestResult.PASSED if is_valid else TestResult.FAILED
                error_msg = "; ".join(discrepancies) if discrepancies else None
            else:
                result = TestResult.PASSED
                error_msg = None

            execution_time = time.monotonic() - start_time

            return AgentTestResult(
                test_case=test_case,
                result=result,
                actual_output=actual_output,
                execution_time_seconds=execution_time,
                error_message=error_msg,
            )

        except asyncio.TimeoutError:
            return AgentTestResult(
                test_case=test_case,
                result=TestResult.TIMEOUT,
                execution_time_seconds=time.monotonic() - start_time,
                error_message=f"Test timed out after {test_case.timeout_seconds}s",
            )
        except AgentError as e:
            return AgentTestResult(
                test_case=test_case,
                result=TestResult.ERROR,
                execution_time_seconds=time.monotonic() - start_time,
                error_message=str(e),
            )
        except Exception as e:
            return AgentTestResult(
                test_case=test_case,
                result=TestResult.ERROR,
                execution_time_seconds=time.monotonic() - start_time,
                error_message=f"Unexpected error: {type(e).__name__}: {e}",
            )

    async def run_tests(
        self, test_cases: list[AgentTestCase]
    ) -> list[AgentTestResult]:
        """Run multiple test cases concurrently.

        Args:
            test_cases: List of test cases to execute.

        Returns:
            List of test results.
        """
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def run_with_semaphore(tc: AgentTestCase) -> AgentTestResult:
            async with semaphore:
                return await self.run_test(tc)

        tasks = [run_with_semaphore(tc) for tc in test_cases]
        self._results = await asyncio.gather(*tasks, return_exceptions=False)
        return self._results

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of test results.

        Returns:
            Dictionary with test summary statistics.
        """
        if not self._results:
            return {"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0}

        summary: dict[str, Any] = {"total": len(self._results)}
        for result in TestResult:
            summary[result.value] = sum(
                1 for r in self._results if r.result == result
            )
        summary["pass_rate"] = (
            summary["passed"] / summary["total"] if summary["total"] > 0 else 0.0
        )
        summary["total_execution_time"] = sum(
            r.execution_time_seconds for r in self._results
        )
        return summary


class AgentTestSuite:
    """A suite of agent test cases with setup and teardown."""

    def __init__(self, name: str, description: str = "") -> None:
        """Initialize AgentTestSuite.

        Args:
            name: Name of the test suite.
            description: Description of the test suite.
        """
        self.name = name
        self.description = description
        self.test_cases: list[AgentTestCase] = []
        self._setup: Callable[[], Coroutine[Any, Any, None]] | None = None
        self._teardown: Callable[[], Coroutine[Any, Any, None]] | None = None

    def add_test(self, test_case: AgentTestCase) -> None:
        """Add a test case to the suite.

        Args:
            test_case: The test case to add.
        """
        self.test_cases.append(test_case)

    def setup(self, func: Callable[[], Coroutine[Any, Any, None]]) -> Callable:
        """Decorator to set the setup function.

        Args:
            func: The setup function.

        Returns:
            The decorated function.
        """
        self._setup = func
        return func

    def teardown(self, func: Callable[[], Coroutine[Any, Any, None]]) -> Callable:
        """Decorator to set the teardown function.

        Args:
            func: The teardown function.

        Returns:
            The decorated function.
        """
        self._teardown = func
        return func

    async def run(
        self, runner: AgentTestRunner
    ) -> tuple[list[AgentTestResult], dict[str, Any]]:
        """Run the entire test suite.

        Args:
            runner: The test runner to use.

        Returns:
            Tuple of (test results, summary).
        """
        if self._setup:
            await self._setup()

        try:
            results = await runner.run_tests(self.test_cases)
        finally:
            if self._teardown:
                await self._teardown()

        summary = runner.get_summary()
        return results, summary


class MockAgent(AgentInterface):
    """A mock agent for testing purposes."""

    def __init__(self, responses: dict[str, dict[str, Any]] | None = None) -> None:
        """Initialize MockAgent.

        Args:
            responses: Mapping of input patterns to responses.
        """
        self.responses = responses or {}
        self._state: dict[str, Any] = {"message_count": 0}
        self._default_response: dict[str, Any] = {"response": "default"}

    async def respond(self, message: dict[str, Any]) -> dict[str, Any]:
        """Return a mock response.

        Args:
            message: The input message.

        Returns:
            A mock response.
        """
        self._state["message_count"] += 1
        for pattern, response in self.responses.items():
            if pattern in json.dumps(message):
                return response
        return self._default_response

    async def reset(self) -> None:
        """Reset the mock agent state."""
        self._state = {"message_count": 0}

    async def get_state(self) -> dict[str, Any]:
        """Get the current state.

        Returns:
            The current state.
        """
        return self._state.copy()
