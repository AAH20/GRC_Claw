"""Database partition management for UGC Marketplace."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import text

from ugc_marketplace.config.logging_config import get_logger

logger = get_logger(__name__)


class PartitionManager:
    """Manages PostgreSQL table partitions for time-series data."""

    def __init__(self, engine: Any) -> None:
        self.engine = engine

    async def create_monthly_partition(
        self, table_name: str, year: int, month: int
    ) -> str:
        """Create a new monthly partition."""
        partition_name = f"{table_name}_{year}_{month:02d}"
        start_date = datetime(year, month, 1)
        end_date = (
            datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
        )

        async with self.engine.begin() as conn:
            await conn.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {partition_name}
                    PARTITION OF {table_name}
                    FOR VALUES FROM ('{start_date.isoformat()}')
                    TO ('{end_date.isoformat()}')
                """))
        logger.info("Created partition", partition=partition_name)
        return partition_name

    async def create_partitions_for_range(
        self, table_name: str, start_date: datetime, end_date: datetime
    ) -> list[str]:
        """Create partitions for a date range."""
        partitions: list[str] = []
        current = start_date
        while current < end_date:
            partition_name = await self.create_monthly_partition(
                table_name, current.year, current.month
            )
            partitions.append(partition_name)
            current = (
                datetime(current.year + 1, 1, 1)
                if current.month == 12
                else datetime(current.year, current.month + 1, 1)
            )
        return partitions

    async def drop_old_partitions(
        self, table_name: str, retention_months: int = 12
    ) -> list[str]:
        """Drop partitions older than retention period."""
        cutoff_date = datetime.utcnow() - timedelta(days=30 * retention_months)
        dropped: list[str] = []
        async with self.engine.begin() as conn:
            result = await conn.execute(
                text(
                    "SELECT tablename FROM pg_tables WHERE tablename LIKE :pattern ORDER BY tablename"
                ),
                {"pattern": f"{table_name}_%"},
            )
            partitions = [row[0] for row in result]
            for partition in partitions:
                try:
                    date_str = partition.replace(f"{table_name}_", "")
                    partition_date = datetime.strptime(date_str, "%Y_%m")
                    if partition_date < cutoff_date:
                        await conn.execute(text(f"DROP TABLE IF EXISTS {partition}"))
                        dropped.append(partition)
                        logger.info("Dropped old partition", partition=partition)
                except ValueError:
                    continue
        return dropped

    async def get_partition_stats(self, table_name: str) -> list[dict[str, Any]]:
        """Get statistics for all partitions."""
        async with self.engine.begin() as conn:
            result = await conn.execute(
                text("""
                    SELECT tablename, pg_total_relation_size(quote_ident(tablename)) as size_bytes
                    FROM pg_tables WHERE tablename LIKE :pattern ORDER BY tablename
                """),
                {"pattern": f"{table_name}_%"},
            )
            return [
                {
                    "partition": row[0],
                    "size_bytes": row[1],
                    "size_mb": round(row[1] / (1024 * 1024), 2),
                }
                for row in result
            ]

    async def ensure_future_partitions(
        self, table_name: str, months_ahead: int = 3
    ) -> list[str]:
        """Ensure partitions exist for future months."""
        now = datetime.utcnow()
        end_date = now + timedelta(days=30 * months_ahead)
        return await self.create_partitions_for_range(table_name, now, end_date)
