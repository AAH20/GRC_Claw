"""Integration tests for database audit triggers."""

from datetime import datetime, timedelta

import pytest
import pytest_asyncio

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def db_pool():
    """Create a fresh database connection pool."""
    from recruitment_platform.db import create_pool

    pool = await create_pool(min_size=2, max_size=5)
    yield pool
    await pool.close()


@pytest_asyncio.fixture
async def audit_table(db_pool):
    """Ensure audit log table exists and is clean."""
    async with db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id SERIAL PRIMARY KEY,
                table_name TEXT NOT NULL,
                operation TEXT NOT NULL,
                record_id INTEGER,
                changed_at TIMESTAMPTZ DEFAULT NOW(),
                old_data JSONB,
                new_data JSONB
            )
        """)
        await conn.execute("TRUNCATE audit_log")
    yield
    async with db_pool.acquire() as conn:
        await conn.execute("TRUNCATE audit_log")


async def test_insert_trigger_creates_audit_entry(db_pool, audit_table):
    """INSERT on candidates table should fire audit trigger."""
    async with db_pool.acquire() as conn:
        result = await conn.fetchval(
            "INSERT INTO candidates (name, email) VALUES ($1, $2) RETURNING id",
            "Test User",
            "test@example.com",
        )
        audit = await conn.fetchrow(
            "SELECT * FROM audit_log WHERE table_name = 'candidates' AND record_id = $1",
            result,
        )
        assert audit is not None
        assert audit["operation"] == "INSERT"
        assert audit["new_data"]["name"] == "Test User"


async def test_update_trigger_captures_old_and_new(db_pool, audit_table):
    """UPDATE should record both old and new row state."""
    async with db_pool.acquire() as conn:
        cid = await conn.fetchval(
            "INSERT INTO candidates (name, email) VALUES ($1, $2) RETURNING id",
            "Old Name",
            "old@example.com",
        )
        await conn.execute(
            "UPDATE candidates SET name = $1 WHERE id = $2", "New Name", cid
        )
        audit = await conn.fetchrow(
            "SELECT * FROM audit_log WHERE operation = 'UPDATE' AND record_id = $1", cid
        )
        assert audit["old_data"]["name"] == "Old Name"
        assert audit["new_data"]["name"] == "New Name"


async def test_delete_trigger_preserves_record(db_pool, audit_table):
    """DELETE should archive the removed row in audit log."""
    async with db_pool.acquire() as conn:
        cid = await conn.fetchval(
            "INSERT INTO candidates (name, email) VALUES ($1, $2) RETURNING id",
            "Delete Me",
            "delete@example.com",
        )
        await conn.execute("DELETE FROM candidates WHERE id = $1", cid)
        audit = await conn.fetchrow(
            "SELECT * FROM audit_log WHERE operation = 'DELETE' AND record_id = $1", cid
        )
        assert audit["old_data"]["email"] == "delete@example.com"
        assert audit["new_data"] is None


async def test_trigger_skips_no_op_update(db_pool, audit_table):
    """UPDATE that changes nothing should not create audit entry."""
    async with db_pool.acquire() as conn:
        cid = await conn.fetchval(
            "INSERT INTO candidates (name, email) VALUES ($1, $2) RETURNING id",
            "Same",
            "same@example.com",
        )
        await conn.execute("UPDATE candidates SET name = $1 WHERE id = $2", "Same", cid)
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM audit_log WHERE record_id = $1", cid
        )
        assert count == 1  # Only the INSERT audit


async def test_audit_timestamp_is_recent(db_pool, audit_table):
    """Audit entries should have timestamps close to now."""
    async with db_pool.acquire() as conn:
        before = datetime.utcnow() - timedelta(seconds=5)
        await conn.execute(
            "INSERT INTO candidates (name, email) VALUES ($1, $2)",
            "Time Test",
            "time@example.com",
        )
        audit = await conn.fetchrow("SELECT changed_at FROM audit_log LIMIT 1")
        assert audit["changed_at"] >= before
