"""Base agent class for all recruitment agents."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")
R = TypeVar("R")


class BaseAgent(ABC, Generic[T, R]):
    """Abstract base class for all recruitment agents.

    All agents must inherit from this class and implement the `process` method.
    Agents are the core processing units that perform specific recruitment tasks.

    Type Parameters:
        T: The input type the agent accepts.
        R: The output type the agent produces.
    """

    def __init__(self, name: str, **kwargs: Any) -> None:
        """Initialize the base agent.

        Args:
            name: Human-readable name for the agent.
            **kwargs: Additional configuration parameters.
        """
        self.name = name
        self.config = kwargs
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def process(self, input_data: T) -> R:
        """Process the input data and return the result.

        Args:
            input_data: The input data to process.

        Returns:
            The processed result.

        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError

    async def validate(self, input_data: T) -> bool:
        """Validate input data before processing.

        Args:
            input_data: The input data to validate.

        Returns:
            True if the input is valid, False otherwise.
        """
        return input_data is not None

    async def execute(self, input_data: T) -> R:
        """Execute the agent with validation and error handling.

        Args:
            input_data: The input data to process.

        Returns:
            The processed result.

        Raises:
            ValueError: If the input data is invalid.
            Exception: If processing fails.
        """
        self._logger.info(f"Executing agent: {self.name}")

        if not await self.validate(input_data):
            raise ValueError(f"Invalid input for agent {self.name}")

        try:
            result = await self.process(input_data)
            self._logger.info(f"Agent {self.name} completed successfully")
            return result
        except Exception as e:
            self._logger.error(f"Agent {self.name} failed: {e}")
            raise

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
