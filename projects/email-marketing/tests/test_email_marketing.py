"""Tests for the Email Marketing platform."""

from __future__ import annotations

import pytest


def test_email_marketing_import():
    """Test that the email_marketing package can be imported."""
    import email_marketing
    assert email_marketing.__version__ == "0.1.0"


def test_email_marketing_agents_exist():
    """Test that the agents module exists."""
    from email_marketing import agents
    assert agents is not None


def test_email_marketing_api_exists():
    """Test that the api module exists."""
    from email_marketing import api
    assert api is not None


def test_email_marketing_integrations_exist():
    """Test that the integrations module exists."""
    from email_marketing import integrations
    assert integrations is not None
