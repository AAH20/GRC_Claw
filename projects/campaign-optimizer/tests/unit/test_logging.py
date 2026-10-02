"""Unit tests for structured logging."""

from __future__ import annotations

import logging

from core.logging import configure_logging, get_logger


class TestLogging:
    """Tests for logging configuration."""

    def test_configure_logging_json(self) -> None:
        """Test JSON logging configuration."""
        configure_logging(log_level="INFO", json_format=True)
        logger = get_logger("test")
        assert logger is not None

    def test_configure_logging_console(self) -> None:
        """Test console logging configuration."""
        configure_logging(log_level="DEBUG", json_format=False)
        logger = get_logger("test")
        assert logger is not None

    def test_get_logger(self) -> None:
        """Test logger retrieval."""
        logger = get_logger("test.module")
        assert logger is not None
        assert logger.name == "test.module"

    def test_logger_levels(self) -> None:
        """Test different log levels."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            configure_logging(log_level=level, json_format=True)
            logger = get_logger(f"test_{level.lower()}")
            assert logger is not None
