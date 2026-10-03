"""Integration tests for transaction isolation and rollback."""

import asyncio

import pytest
import pytest_asyncio

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def db_pool():
    from recruitment_platform.db import create_pool

    pool = await create_pool(min_size=4, max_size=10)
    yield pool
    await pool.close()


@pytest_asyncio.fixture
async def tx_table(db_pool):
    """Create a table for transaction testing."""
    async with db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tx_accounts (
                id SERIAL PRIMARY KEY,
                owner TEXT NOT NULL,
                balance INTEGER NOT NULL DEFAULT 0
            )
        """)
        await conn.execute("TRUNCATE tx_accounts")
        await conn.execute(
            "INSERT INTO tx_accounts (owner, balance) VALUES ($1, $2)", "Alice", 1000
        )
        await conn.execute(
            "INSERT INTO tx_accounts (owner, balance) VALUES ($1, $2)", "Bob", 500
        )
    yield
    async with db_pool.acquire() as conn:
        await conn.execute("DROP TABLE IF EXISTS tx_accounts")


async def test_rollback_on_error(db_pool, tx_table):
    """Failed transaction should roll back all changes."""
    async with db_pool.acquire() as conn:
        try:
            async with conn.transaction():
                await conn.execute(
                    "UPDATE tx_accounts SET balance = balance - 100 WHERE owner = $1",
                    "Alice",
                )
                await conn.execute(
                    "UPDATE tx_accounts SET balance = balance + 100 WHERE owner = $1",
                    "Bob",
                )
                raise ValueError("Simulated failure")
        except ValueError:
            pass
        alice = await conn.fetchval(
            "SELECT balance FROM tx_accounts WHERE owner = $1", "Alice"
        )
        bob = await conn.fetchval(
            "SELECT balance FROM tx_accounts WHERE owner = $1", "Bob"
        )
        assert alice == 1000
        assert bob == 500


async def test_commit_persists_changes(db_pool, tx_table):
    """Successful transaction should persist all changes."""
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "UPDATE tx_accounts SET balance = balance - 200 WHERE owner = $1",
                "Alice",
            )
            await conn.execute(
                "UPDATE tx_accounts SET balance = balance + 200 WHERE owner = $1", "Bob"
            )
        alice = await conn.fetchval(
            "SELECT balance FROM tx_accounts WHERE owner = $1", "Alice"
        )
        bob = await conn.fetchval(
            "SELECT balance FROM tx_accounts WHERE owner = $1", "Bob"
        )
        assert alice == 800
        assert bob == 700


async def test_read_committed_isolation(db_pool, tx_table):
    """Uncommitted changes should not be visible to other connections."""
    conn1 = await db_pool.acquire()
    conn2 = await db_pool.acquire()
    try:
        tx = conn1.transaction()
        await tx.start()
        await conn1.execute(
            "UPDATE tx_accounts SET balance = 0 WHERE owner = $1", "Alice"
        )
        bob_balance = await conn2.fetchval(
            "SELECT balance FROM tx_accounts WHERE owner = $1", "Bob"
        )
        assert bob_balance == 500
        await tx.rollback()
    finally:
        db_pool.release(conn1)
        db_pool.release(conn2)


async def test_serializable_prevents_lost_update(db_pool, tx_table):
    """Serializable isolation should detect concurrent modification."""
    errors = []

    async def transfer():
        try:
            async with (
                db_pool.acquire() as conn,
                conn.transaction(isolation="serializable"),
            ):
                bal = await conn.fetchval(
                    "SELECT balance FROM tx_accounts WHERE owner = $1", "Alice"
                )
                await asyncio.sleep(0.01)
                await conn.execute(
                    "UPDATE tx_accounts SET balance = $1 WHERE owner = $2",
                    bal - 50,
                    "Alice",
                )
        except Exception as e:
            errors.append(e)

    await asyncio.gather(transfer(), transfer())
    final = await db_pool.fetchval(
        "SELECT balance FROM tx_accounts WHERE owner = $1", "Alice"
    )
    assert final >= 900


async def test_savepoint_partial_rollback(db_pool, tx_table):
    """Savepoints allow partial rollback within a transaction."""
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "UPDATE tx_accounts SET balance = 999 WHERE owner = $1", "Alice"
            )
            await conn.execute("SAVEPOINT sp1")
            await conn.execute(
                "UPDATE tx_accounts SET balance = 888 WHERE owner = $1", "Alice"
            )
            await conn.execute("ROLLBACK TO SAVEPOINT sp1")
            await conn.execute(
                "UPDATE tx_accounts SET balance = 777 WHERE owner = $1", "Bob"
            )
        alice = await conn.fetchval(
            "SELECT balance FROM tx_accounts WHERE owner = $1", "Alice"
        )
        bob = await conn.fetchval(
            "SELECT balance FROM tx_accounts WHERE owner = $1", "Bob"
        )
        assert alice == 999
        assert bob == 777
