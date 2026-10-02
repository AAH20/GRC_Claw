"""Salesforce API connector."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .base import APIResponse, BaseConnector, ConnectorConfig, ConnectorError
from .oauth import OAuth2Handler

logger = logging.getLogger(__name__)


class SalesforceConnector(BaseConnector):
    """Salesforce REST API connector.

    Supports accounts, contacts, leads, opportunities, and custom objects.
    Uses OAuth 2.0 for authentication.
    """

    DEFAULT_BASE_URL = "https://login.salesforce.com"
    API_VERSION = "v59.0"

    def __init__(
        self,
        username: str,
        password: str,
        security_token: str = "",
        client_id: str = "",
        client_secret: str = "",
        *,
        sandbox: bool = False,
        config: Optional[ConnectorConfig] = None,
    ) -> None:
        if config is None:
            base_url = "https://test.salesforce.com" if sandbox else self.DEFAULT_BASE_URL
            config = ConnectorConfig(
                base_url=base_url,
                extra_headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        super().__init__(config)
        self.username = username
        self.password = password + security_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.sandbox = sandbox
        self._instance_url: Optional[str] = None
        self._oauth_handler: Optional[OAuth2Handler] = None

    async def authenticate(self) -> None:
        """Authenticate with Salesforce using username-password OAuth flow."""
        self._state = self._state.AUTHENTICATING
        try:
            data = {
                "grant_type": "password",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "username": self.username,
                "password": self.password,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.config.base_url}/services/oauth2/token",
                    data=data,
                ) as resp:
                    body = await resp.json()
                    if resp.status != 200:
                        error = body.get("error", "unknown")
                        description = body.get("error_description", "")
                        raise ConnectorError(
                            f"Salesforce auth failed: {error} - {description}",
                            status_code=resp.status,
                        )
                    self._auth_token = body["access_token"]
                    self._instance_url = body.get("instance_url", "")
                    self._state = self._state.AUTHENTICATED
        except Exception as e:
            self._state = self._state.ERROR
            raise ConnectorError(f"Salesforce authentication failed: {e}") from e

    async def refresh_auth(self) -> None:
        """Refresh the Salesforce OAuth token."""
        if not self._oauth_handler:
            self._oauth_handler = OAuth2Handler(
                client_id=self.client_id,
                client_secret=self.client_secret,
                token_url=f"{self.config.base_url}/services/oauth2/token",
            )
        token = await self._oauth_handler.refresh(session=self._session)
        self._auth_token = token.access_token

    async def health_check(self) -> bool:
        """Check if Salesforce API is reachable."""
        try:
            response = await self.get("/services/data/")
            return response.is_success
        except Exception:
            return False

    def _api_url(self, path: str) -> str:
        """Build full API URL."""
        base = self._instance_url or self.config.base_url
        return f"{base}/services/data/{self.API_VERSION}/{path.lstrip('/')}"

    # ─── SOQL Queries ───────────────────────────────────────────────────

    async def query(self, soql: str) -> Dict[str, Any]:
        """Execute a SOQL query.

        Args:
            soql: SOQL query string.

        Returns:
            Query result with 'records', 'totalSize', 'done'.
        """
        response = await self.get(
            self._api_url("query"),
            params={"q": soql},
        )
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def query_all(self, soql: str) -> List[Dict[str, Any]]:
        """Execute a SOQL query and return all records (handles pagination).

        Args:
            soql: SOQL query string.

        Returns:
            List of all records.
        """
        all_records: List[Dict[str, Any]] = []
        result = await self.query(soql)
        all_records.extend(result.get("records", []))

        while not result.get("done", True):
            next_url = result.get("nextRecordsUrl")
            if next_url:
                response = await self.get(next_url)
                if isinstance(response.data, dict):
                    result = response.data
                    all_records.extend(result.get("records", []))
            else:
                break

        return all_records

    # ─── Accounts ───────────────────────────────────────────────────────

    async def get_accounts(
        self,
        *,
        where: Optional[str] = None,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """Get accounts.

        Args:
            where: Optional WHERE clause.
            limit: Maximum number of records.

        Returns:
            List of account records.
        """
        soql = "SELECT Id, Name, Type, Industry, BillingCity, BillingCountry, Phone, Website FROM Account"
        if where:
            soql += f" WHERE {where}"
        soql += f" LIMIT {limit}"
        return await self.query_all(soql)

    async def get_account(self, account_id: str) -> Dict[str, Any]:
        """Get a single account by ID.

        Args:
            account_id: The Salesforce account ID.

        Returns:
            Account record.
        """
        response = await self.get(self._api_url(f"sobjects/Account/{account_id}"))
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def create_account(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new account.

        Args:
            data: Account field values.

        Returns:
            Created account with ID.
        """
        response = await self.post(self._api_url("sobjects/Account"), data=data)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def update_account(self, account_id: str, data: Dict[str, Any]) -> bool:
        """Update an existing account.

        Args:
            account_id: The Salesforce account ID.
            data: Fields to update.

        Returns:
            True if update was successful.
        """
        response = await self.patch(
            self._api_url(f"sobjects/Account/{account_id}"),
            data=data,
        )
        return response.is_success

    async def delete_account(self, account_id: str) -> bool:
        """Delete an account.

        Args:
            account_id: The Salesforce account ID.

        Returns:
            True if deletion was successful.
        """
        response = await self.delete(self._api_url(f"sobjects/Account/{account_id}"))
        return response.is_success

    # ─── Contacts ───────────────────────────────────────────────────────

    async def get_contacts(
        self,
        *,
        account_id: Optional[str] = None,
        where: Optional[str] = None,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """Get contacts.

        Args:
            account_id: Optional account ID to filter by.
            where: Optional WHERE clause.
            limit: Maximum number of records.

        Returns:
            List of contact records.
        """
        soql = "SELECT Id, FirstName, LastName, Email, Phone, Title, AccountId FROM Contact"
        conditions = []
        if account_id:
            conditions.append(f"AccountId = '{account_id}'")
        if where:
            conditions.append(where)
        if conditions:
            soql += " WHERE " + " AND ".join(conditions)
        soql += f" LIMIT {limit}"
        return await self.query_all(soql)

    async def create_contact(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new contact.

        Args:
            data: Contact field values.

        Returns:
            Created contact with ID.
        """
        response = await self.post(self._api_url("sobjects/Contact"), data=data)
        if isinstance(response.data, dict):
            return response.data
        return {}

    # ─── Leads ──────────────────────────────────────────────────────────

    async def get_leads(
        self,
        *,
        status: Optional[str] = None,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """Get leads.

        Args:
            status: Optional lead status to filter by.
            limit: Maximum number of records.

        Returns:
            List of lead records.
        """
        soql = "SELECT Id, FirstName, LastName, Email, Company, Status, LeadSource, Rating FROM Lead"
        if status:
            soql += f" WHERE Status = '{status}'"
        soql += f" LIMIT {limit}"
        return await self.query_all(soql)

    async def create_lead(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new lead.

        Args:
            data: Lead field values.

        Returns:
            Created lead with ID.
        """
        response = await self.post(self._api_url("sobjects/Lead"), data=data)
        if isinstance(response.data, dict):
            return response.data
        return {}

    # ─── Opportunities ──────────────────────────────────────────────────

    async def get_opportunities(
        self,
        *,
        stage: Optional[str] = None,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """Get opportunities.

        Args:
            stage: Optional stage name to filter by.
            limit: Maximum number of records.

        Returns:
            List of opportunity records.
        """
        soql = "SELECT Id, Name, Amount, StageName, CloseDate, Probability, AccountId FROM Opportunity"
        if stage:
            soql += f" WHERE StageName = '{stage}'"
        soql += f" LIMIT {limit}"
        return await self.query_all(soql)

    async def create_opportunity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new opportunity.

        Args:
            data: Opportunity field values.

        Returns:
            Created opportunity with ID.
        """
        response = await self.post(self._api_url("sobjects/Opportunity"), data=data)
        if isinstance(response.data, dict):
            return response.data
        return {}

    # ─── Custom Objects ─────────────────────────────────────────────────

    async def get_object_metadata(self, object_name: str) -> Dict[str, Any]:
        """Get metadata for a custom or standard object.

        Args:
            object_name: API name of the object.

        Returns:
            Object metadata.
        """
        response = await self.get(self._api_url(f"sobjects/{object_name}/describe"))
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def get_custom_object(
        self,
        object_name: str,
        record_id: str,
    ) -> Dict[str, Any]:
        """Get a record from a custom object.

        Args:
            object_name: API name of the custom object.
            record_id: The record ID.

        Returns:
            Record data.
        """
        response = await self.get(self._api_url(f"sobjects/{object_name}/{record_id}"))
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def create_custom_object(
        self,
        object_name: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a record in a custom object.

        Args:
            object_name: API name of the custom object.
            data: Field values.

        Returns:
            Created record with ID.
        """
        response = await self.post(self._api_url(f"sobjects/{object_name}"), data=data)
        if isinstance(response.data, dict):
            return response.data
        return {}
