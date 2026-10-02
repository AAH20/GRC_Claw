"""Data Collection Agent - collects sales data from CRM and ERP systems."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

import structlog

from sales_forecaster.core.exceptions import DataCollectionError, IntegrationError
from sales_forecaster.core.metrics import record_agent_error, record_data_collected
from sales_forecaster.core.models import DataSource, SalesRecord
from sales_forecaster.core.retry import async_retry

if TYPE_CHECKING:
    from collections.abc import Callable
if TYPE_CHECKING:
    from sales_forecaster.integrations.hubspot import HubSpotIntegration
    from sales_forecaster.integrations.salesforce import SalesforceIntegration
    from sales_forecaster.integrations.sap import SAPIntegration

logger = structlog.get_logger(__name__)


class DataCollectionAgent:
    """Agent responsible for collecting sales data from multiple sources.

    This agent orchestrates data collection from Salesforce, HubSpot, and SAP,
    normalizing the data into a unified SalesRecord format for downstream agents.
    """

    def __init__(
        self,
        salesforce: SalesforceIntegration | None = None,
        hubspot: HubSpotIntegration | None = None,
        sap: SAPIntegration | None = None,
        batch_size: int = 500,
    ) -> None:
        """Initialize the Data Collection Agent.

        Args:
            salesforce: Salesforce integration instance.
            hubspot: HubSpot integration instance.
            sap: SAP integration instance.
            batch_size: Number of records to fetch per batch.
        """
        self.salesforce = salesforce
        self.hubspot = hubspot
        self.sap = sap
        self.batch_size = batch_size
        self._progress_callbacks: list[Callable[[str, int, int], None]] = []

    def register_progress_callback(
        self, callback: Callable[[str, int, int], None]
    ) -> None:
        """Register a callback for collection progress updates.

        Args:
            callback: Function called with (source, current, total).
        """
        self._progress_callbacks.append(callback)

    def _notify_progress(self, source: str, current: int, total: int) -> None:
        """Notify all registered progress callbacks.

        Args:
            source: Data source name.
            current: Current record count.
            total: Total expected records.
        """
        for callback in self._progress_callbacks:
            try:
                callback(source, current, total)
            except Exception as exc:
                logger.warning("Progress callback failed", error=str(exc))

    @async_retry(
        max_attempts=3,
        base_delay=1.0,
        retryable_exceptions=(ConnectionError, TimeoutError, IntegrationError),
    )
    async def collect_from_source(
        self,
        source: DataSource,
        start_date: datetime,
        end_date: datetime,
        **kwargs: Any,
    ) -> list[SalesRecord]:
        """Collect data from a single source.

        Args:
            source: The data source to collect from.
            start_date: Start date for data collection.
            end_date: End date for data collection.
            **kwargs: Additional source-specific parameters.

        Returns:
            List of normalized sales records.

        Raises:
            DataCollectionError: If collection from the source fails.
        """
        logger.info(
            "Collecting data from source",
            source=source.value,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )

        try:
            if source == DataSource.SALESFORCE:
                if not self.salesforce:
                    raise DataCollectionError(
                        "Salesforce integration not configured",
                        source="salesforce",
                    )
                records = await self._collect_salesforce(start_date, end_date, **kwargs)
            elif source == DataSource.HUBSPOT:
                if not self.hubspot:
                    raise DataCollectionError(
                        "HubSpot integration not configured",
                        source="hubspot",
                    )
                records = await self._collect_hubspot(start_date, end_date, **kwargs)
            elif source == DataSource.SAP:
                if not self.sap:
                    raise DataCollectionError(
                        "SAP integration not configured",
                        source="sap",
                    )
                records = await self._collect_sap(start_date, end_date, **kwargs)
            else:
                raise DataCollectionError(
                    f"Unknown data source: {source}",
                    source=str(source),
                )

            record_data_collected(source.value, len(records))
            logger.info(
                "Data collection complete",
                source=source.value,
                record_count=len(records),
            )
            return records

        except DataCollectionError:
            raise
        except Exception as exc:
            record_agent_error("data_collection")
            logger.error(
                "Data collection failed",
                source=source.value,
                error=str(exc),
                exc_info=True,
            )
            raise DataCollectionError(
                f"Failed to collect data from {source.value}: {exc}",
                source=source.value,
            ) from exc

    async def _collect_salesforce(
        self, start_date: datetime, end_date: datetime, **kwargs: Any
    ) -> list[SalesRecord]:
        """Collect opportunities from Salesforce.

        Args:
            start_date: Start date for data collection.
            end_date: End date for data collection.
            **kwargs: Additional parameters.

        Returns:
            List of sales records from Salesforce.
        """
        assert self.salesforce is not None
        opportunities = await self.salesforce.get_opportunities(
            start_date, end_date, limit=kwargs.get("limit", self.batch_size)
        )
        return [self._normalize_salesforce_record(opp) for opp in opportunities]

    async def _collect_hubspot(
        self, start_date: datetime, end_date: datetime, **kwargs: Any
    ) -> list[SalesRecord]:
        """Collect deals from HubSpot.

        Args:
            start_date: Start date for data collection.
            end_date: End date for data collection.
            **kwargs: Additional parameters.

        Returns:
            List of sales records from HubSpot.
        """
        assert self.hubspot is not None
        deals = await self.hubspot.get_deals(
            start_date, end_date, limit=kwargs.get("limit", self.batch_size)
        )
        return [self._normalize_hubspot_record(deal) for deal in deals]

    async def _collect_sap(
        self, start_date: datetime, end_date: datetime, **kwargs: Any
    ) -> list[SalesRecord]:
        """Collect sales orders from SAP.

        Args:
            start_date: Start date for data collection.
            end_date: End date for data collection.
            **kwargs: Additional parameters.

        Returns:
            List of sales records from SAP.
        """
        assert self.sap is not None
        orders = await self.sap.get_sales_orders(
            start_date, end_date, limit=kwargs.get("limit", self.batch_size)
        )
        return [self._normalize_sap_record(order) for order in orders]

    def _normalize_salesforce_record(self, opp: dict[str, Any]) -> SalesRecord:
        """Normalize a Salesforce opportunity to a SalesRecord.

        Args:
            opp: Raw Salesforce opportunity data.

        Returns:
            Normalized SalesRecord.
        """
        return SalesRecord(
            id=f"sf_{opp['Id']}",
            source=DataSource.SALESFORCE,
            amount=float(opp.get("Amount", 0)),
            currency=opp.get("CurrencyIsoCode", "USD"),
            date=datetime.fromisoformat(opp["CloseDate"].replace("Z", "+00:00")),
            customer_id=opp.get("AccountId"),
            product_id=opp.get("Product2Id"),
            region=opp.get("Region__c"),
            sales_rep_id=opp.get("OwnerId"),
            stage=opp.get("StageName"),
            probability=float(opp.get("Probability", 0)) / 100,
            metadata={"opportunity_name": opp.get("Name", "")},
        )

    def _normalize_hubspot_record(self, deal: dict[str, Any]) -> SalesRecord:
        """Normalize a HubSpot deal to a SalesRecord.

        Args:
            deal: Raw HubSpot deal data.

        Returns:
            Normalized SalesRecord.
        """
        props = deal.get("properties", {})
        return SalesRecord(
            id=f"hs_{deal['id']}",
            source=DataSource.HUBSPOR,
            amount=float(props.get("amount", 0)),
            currency=props.get("hs_currency_code", "USD"),
            date=datetime.fromisoformat(
                props.get("closedate", props.get("createdate", "")).replace("Z", "+00:00")
            ),
            customer_id=props.get("associated_company_id"),
            product_id=props.get("product_id"),
            region=props.get("region"),
            sales_rep_id=props.get("hubspot_owner_id"),
            stage=props.get("dealstage"),
            probability=float(props.get("probability", 0)) / 100,
            metadata={"deal_name": props.get("dealname", "")},
        )

    def _normalize_sap_record(self, order: dict[str, Any]) -> SalesRecord:
        """Normalize a SAP sales order to a SalesRecord.

        Args:
            order: Raw SAP sales order data.

        Returns:
            Normalized SalesRecord.
        """
        return SalesRecord(
            id=f"sap_{order['SalesOrder']}",
            source=DataSource.SAP,
            amount=float(order.get("TotalNetAmount", 0)),
            currency=order.get("TransactionCurrency", "USD"),
            date=datetime.fromisoformat(order["CreationDate"].replace("Z", "+00:00")),
            customer_id=order.get("SoldToParty"),
            product_id=order.get("Material"),
            region=order.get("SalesOrganization"),
            sales_rep_id=order.get("SalesEmployee"),
            stage=order.get("OverallSDProcessStatus"),
            probability=None,
            metadata={"order_type": order.get("SalesOrderType", "")},
        )

    async def collect_all(
        self,
        sources: list[DataSource] | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        **kwargs: Any,
    ) -> list[SalesRecord]:
        """Collect data from all configured sources concurrently.

        Args:
            sources: List of sources to collect from. Defaults to all configured.
            start_date: Start date. Defaults to 1 year ago.
            end_date: End date. Defaults to now.
            **kwargs: Additional source-specific parameters.

        Returns:
            Combined list of sales records from all sources.
        """
        if sources is None:
            sources = []
            if self.salesforce:
                sources.append(DataSource.SALESFORCE)
            if self.hubspot:
                sources.append(DataSource.HUBSPOT)
            if self.sap:
                sources.append(DataSource.SAP)

        if not sources:
            logger.warning("No data sources configured")
            return []

        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=365)

        tasks = [
            self.collect_from_source(source, start_date, end_date, **kwargs)
            for source in sources
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_records: list[SalesRecord] = []
        for source, result in zip(sources, results, strict=True):
            if isinstance(result, Exception):
                logger.error(
                    "Source collection failed",
                    source=source.value,
                    error=str(result),
                )
                continue
            all_records.extend(result)

        logger.info(
            "All sources collected",
            total_records=len(all_records),
            source_count=len(sources),
        )
        return all_records
