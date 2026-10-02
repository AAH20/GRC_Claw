"""Integration clients for external marketing platforms."""

from __future__ import annotations

from compliance.integrations.hubspot import HubSpotClient
from compliance.integrations.mailchimp import MailchimpClient
from compliance.integrations.salesforce import SalesforceClient

__all__ = ["HubSpotClient", "MailchimpClient", "SalesforceClient"]
