"""Integration module for Customer Service AI Platform."""

from customer_service.integrations.intercom import IntercomClient
from customer_service.integrations.salesforce import SalesforceClient
from customer_service.integrations.zendesk import ZendeskClient

__all__ = [
    "ZendeskClient",
    "IntercomClient",
    "SalesforceClient",
]
