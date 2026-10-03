"""Integration tests for query performance benchmarks."""
import pytest
import pytest_asyncio
import time

pytestmark = pytest.mark.asyncio

MAX_QUERY_TIME_MS = 500
MAX_BULK_INSERT_TIME_S = 5.0


@pytest_asyncio.fixture
async def db_pool():
    from recruitment_platform.db import create_pool
    pool = await create_pool(min_size=2, max_size=10)
    yield pool
    await pool.close()


@pytest_asyncio.fixture
async def seeded_data(db_pool):
    """Seed database with test data for performance tests."""
    async with db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS perf_candidates (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute("TRUNCATE perf_candidates")
        await conn.executemany(
            "INSERT INTO perf_candidates (name, email) VALUES ($1, $2)",
            [(f"User {i}", f"user{i}@perf.com") for i in range(1000)]
        )
    yield
    async with db_pool.acquire() as conn:
        await conn.execute("DROP TABLE IF EXISTS perf_candidates")


async def test_indexed_lookup_under_threshold(db_pool, seeded_data):
    """Indexed email lookup should complete within threshold."""
    async with db_pool.acquire() as conn:
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_perf_email ON perf_candidates(email)"
        )
        start = time.monotonic()
        row = await conn.fetchrow(
            "SELECT * FROM perf_candidates WHERE email = $1", "user500@perf.com"
        )
        elapsed_ms = (time.monotonic() - start) * 1000
        assert row is not None
        assert elapsed_ms < MAX_QUERY_TIME_MS


async def test_full_scan_within_bounds(db_pool, seeded_data):
    """Full table scan of 1000 rows should be fast."""
    async with db_pool.acquire() as conn:
        start = time.monotonic()
        count = await conn.fetchval("SELECT COUNT(*) FROM perf_candidates")
        elapsed_ms = (time.monotonic() - start) * 1000
        assert count == 1000
        assert elapsed_ms < MAX_QUERY_TIME_MS * 2


async def test_bulk_insert_performance(db_pool, seeded_data):
    """Bulk insert of 500 rows should complete within time budget."""
    async with db_pool.acquire() as conn:
        start = time.monotonic()
        await conn.executemany(
            "INSERT INTO perf_candidates (name, email) VALUES ($1, $2)",
            [(f"Bulk {i}", f"bulk{i}@perf.com") for i in range(500)]
        )
        elapsed = time.monotonic() - start
        assert elapsed < MAX_BULK_INSERT_TIME_S


async def test_join_query_performance(db_pool, seeded_data):
    """Join between candidates and applications should be optimized."""
    async with db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS perf_applications (
                id SERIAL PRIMARY KEY,
                candidate_id INTEGER REFERENCES perf_candidates(id),
                status TEXT,
                applied_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute("TRUNCATE perf_applications")
        await conn.executemany(
            "INSERT INTO perf_applications (candidate_id, status) VALUES ($1, $2)",
            [(i, "applied") for i in range(1, 501)]
        )
        start = time.monotonic()
        rows = await conn.fetch("""
            SELECT c.name, a.status
            FROM perf_candidates c
            JOIN perf_applications a ON a.candidate_id = c.id
            WHERE a.status = 'applied'
            LIMIT 100
        """)
        elapsed_ms = (time.monotonic() - start) * 1000
        assert len(rows) == 100
        assert elapsed_ms < MAX_QUERY_TIME_MS * 3


async def test_aggregation_performance(db_pool, seeded_data):
    """GROUP BY aggregation over 1000 rows should be efficient."""
    async with db_pool.acquire() as conn:
        start = time.monotonic()
        result = await conn.fetchval("""
            SELECT COUNT(DISTINCT substr(email, 1, 4)) FROM perf_candidates
        """)
        elapsed_ms = (time.monotonic() - start) * 1000
        assert result > 0
        assert elapsed_ms < MAX_QUERY_TIME_MS * 2
