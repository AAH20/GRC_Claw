"""
Usage Metering Engine for GRC_Claw.

Captures, stores, and aggregates usage events across all metering dimensions.
Supports real-time metering, batch ingestion, and usage analytics.
"""

from __future__ import annotations

import threading
from datetime import UTC, datetime

from .models import (
    MeteringDimension,
    PricingTierConfig,
    UsageAggregation,
    UsageRecord,
)


class UsageMeteringEngine:
    """
    Core usage metering engine that records and aggregates usage events.

    Thread-safe for concurrent usage recording. Supports in-memory storage
    with optional persistence hooks for production deployments.
    """

    def __init__(self):
        self._records: list[UsageRecord] = []
        self._lock = threading.Lock()
        self._pricing_configs: dict[MeteringDimension, PricingTierConfig] = {}
        self._listeners: list[callable] = []

    def register_pricing_config(self, config: PricingTierConfig) -> None:
        """Register a pricing configuration for a metering dimension."""
        self._pricing_configs[config.dimension] = config

    def get_pricing_config(self, dimension: MeteringDimension) -> PricingTierConfig | None:
        """Get the pricing configuration for a dimension."""
        return self._pricing_configs.get(dimension)

    def record_usage(
        self,
        tenant_id: str,
        dimension: MeteringDimension,
        quantity: float,
        unit: str = "count",
        timestamp: str | None = None,
        metadata: dict | None = None,
        resource_id: str | None = None,
        agent_id: str | None = None,
        policy_id: str | None = None,
        cost_center: str | None = None,
        tags: list[str] | None = None,
    ) -> UsageRecord:
        """
        Record a single usage event.

        Args:
            tenant_id: The tenant/organization identifier.
            dimension: The metering dimension.
            quantity: The amount of usage.
            unit: The unit of measurement.
            timestamp: ISO format timestamp (defaults to now).
            metadata: Additional metadata for the event.
            resource_id: Optional resource identifier.
            agent_id: Optional agent identifier.
            policy_id: Optional policy identifier.
            cost_center: Optional cost center for chargebacks.
            tags: Optional tags for categorization.

        Returns:
            The created UsageRecord.
        """
        if quantity < 0:
            raise ValueError("quantity must be >= 0")

        record = UsageRecord(
            tenant_id=tenant_id,
            dimension=dimension,
            quantity=quantity,
            unit=unit,
            timestamp=timestamp or datetime.now(UTC).isoformat(),
            metadata=metadata or {},
            resource_id=resource_id,
            agent_id=agent_id,
            policy_id=policy_id,
            cost_center=cost_center,
            tags=tags or [],
        )

        with self._lock:
            self._records.append(record)

        # Notify listeners
        for listener in self._listeners:
            try:
                listener(record)
            except Exception:
                pass

        return record

    def record_batch(self, records: list[UsageRecord]) -> list[UsageRecord]:
        """Record multiple usage events in a batch."""
        with self._lock:
            self._records.extend(records)

        for record in records:
            for listener in self._listeners:
                try:
                    listener(record)
                except Exception:
                    pass

        return records

    def add_listener(self, listener: callable) -> None:
        """Add a listener callback for usage events."""
        self._listeners.append(listener)

    def remove_listener(self, listener: callable) -> None:
        """Remove a listener callback."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def get_records(
        self,
        tenant_id: str | None = None,
        dimension: MeteringDimension | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        agent_id: str | None = None,
        policy_id: str | None = None,
        cost_center: str | None = None,
        tags: list[str] | None = None,
    ) -> list[UsageRecord]:
        """
        Query usage records with filters.

        All filters are optional and combined with AND logic.
        """
        results = self._records

        if tenant_id:
            results = [r for r in results if r.tenant_id == tenant_id]
        if dimension:
            results = [r for r in results if r.dimension == dimension]
        if start_time:
            results = [r for r in results if r.timestamp >= start_time]
        if end_time:
            results = [r for r in results if r.timestamp <= end_time]
        if agent_id:
            results = [r for r in results if r.agent_id == agent_id]
        if policy_id:
            results = [r for r in results if r.policy_id == policy_id]
        if cost_center:
            results = [r for r in results if r.cost_center == cost_center]
        if tags:
            results = [r for r in results if any(t in r.tags for t in tags)]

        return results

    def aggregate(
        self,
        tenant_id: str,
        dimension: MeteringDimension,
        period_start: str,
        period_end: str,
    ) -> UsageAggregation:
        """
        Aggregate usage for a tenant over a time period and dimension.

        Args:
            tenant_id: The tenant identifier.
            dimension: The metering dimension.
            period_start: ISO format start timestamp.
            period_end: ISO format end timestamp.

        Returns:
            UsageAggregation with totals and statistics.
        """
        records = self.get_records(
            tenant_id=tenant_id,
            dimension=dimension,
            start_time=period_start,
            end_time=period_end,
        )

        total_quantity = sum(r.quantity for r in records)
        record_count = len(records)

        # Calculate average per day
        try:
            start_dt = datetime.fromisoformat(period_start.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(period_end.replace("Z", "+00:00"))
            days = max((end_dt - start_dt).total_seconds() / 86400, 1)
            average_per_day = total_quantity / days
        except (ValueError, TypeError):
            average_per_day = total_quantity

        # Find peak
        peak_quantity = 0.0
        peak_timestamp = None
        for r in records:
            if r.quantity > peak_quantity:
                peak_quantity = r.quantity
                peak_timestamp = r.timestamp

        # Determine unit from records or pricing config
        unit = records[0].unit if records else "count"
        config = self._pricing_configs.get(dimension)
        if config and not records:
            unit = config.unit

        return UsageAggregation(
            tenant_id=tenant_id,
            dimension=dimension,
            period_start=period_start,
            period_end=period_end,
            total_quantity=total_quantity,
            unit=unit,
            record_count=record_count,
            average_per_day=average_per_day,
            peak_quantity=peak_quantity,
            peak_timestamp=peak_timestamp,
        )

    def aggregate_by_dimension(
        self,
        tenant_id: str,
        period_start: str,
        period_end: str,
    ) -> dict[MeteringDimension, UsageAggregation]:
        """Aggregate usage for all dimensions for a tenant."""
        results = {}
        for dim in MeteringDimension:
            agg = self.aggregate(tenant_id, dim, period_start, period_end)
            if agg.record_count > 0:
                results[dim] = agg
        return results

    def get_tenant_usage_summary(
        self,
        tenant_id: str,
        period_start: str,
        period_end: str,
    ) -> dict:
        """Get a comprehensive usage summary for a tenant."""
        aggregations = self.aggregate_by_dimension(tenant_id, period_start, period_end)
        return {
            "tenant_id": tenant_id,
            "period_start": period_start,
            "period_end": period_end,
            "dimensions": {
                dim.value: {
                    "total_quantity": agg.total_quantity,
                    "unit": agg.unit,
                    "record_count": agg.record_count,
                    "average_per_day": agg.average_per_day,
                    "peak_quantity": agg.peak_quantity,
                }
                for dim, agg in aggregations.items()
            },
            "total_records": sum(agg.record_count for agg in aggregations.values()),
        }

    def calculate_tiered_price(
        self,
        dimension: MeteringDimension,
        quantity: float,
    ) -> float:
        """
        Calculate price for a quantity using tiered pricing.

        Args:
            dimension: The metering dimension.
            quantity: The total quantity to price.

        Returns:
            The calculated price.
        """
        config = self._pricing_configs.get(dimension)
        if not config:
            return 0.0

        # If quantity is within included amount, return base price
        if quantity <= config.included_quantity:
            return config.base_price

        # Calculate overage
        overage = quantity - config.included_quantity
        price = config.base_price

        if config.tiers:
            # Apply tiered pricing
            remaining = overage
            for tier in config.tiers:
                tier_min = tier.get("min", 0)
                tier_max = tier.get("max", float("inf"))
                tier_price = tier.get("unit_price", 0)

                if remaining <= 0:
                    break

                tier_quantity = min(remaining, tier_max - tier_min)
                if tier_quantity > 0:
                    price += tier_quantity * tier_price
                    remaining -= tier_quantity
        else:
            # Simple overage pricing
            price += overage * config.overage_unit_price

        return price

    def clear_records(self, tenant_id: str | None = None) -> int:
        """
        Clear usage records, optionally filtered by tenant.

        Returns:
            Number of records cleared.
        """
        with self._lock:
            if tenant_id:
                original_count = len(self._records)
                self._records = [r for r in self._records if r.tenant_id != tenant_id]
                return original_count - len(self._records)
            else:
                count = len(self._records)
                self._records.clear()
                return count

    def get_record_count(self) -> int:
        """Get the total number of stored records."""
        return len(self._records)

    def export_records(
        self,
        tenant_id: str | None = None,
        format: str = "json",
    ) -> list[dict]:
        """
        Export usage records as dictionaries.

        Args:
            tenant_id: Optional tenant filter.
            format: Export format (currently only 'json' supported).

        Returns:
            List of record dictionaries.
        """
        records = self.get_records(tenant_id=tenant_id)
        return [
            {
                "record_id": r.record_id,
                "tenant_id": r.tenant_id,
                "dimension": r.dimension.value,
                "quantity": r.quantity,
                "unit": r.unit,
                "timestamp": r.timestamp,
                "metadata": r.metadata,
                "resource_id": r.resource_id,
                "agent_id": r.agent_id,
                "policy_id": r.policy_id,
                "cost_center": r.cost_center,
                "tags": r.tags,
            }
            for r in records
        ]
