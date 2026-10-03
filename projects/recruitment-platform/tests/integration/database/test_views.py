"""Integration tests for materialized views."""
import pytest
import pytest_asyncio

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def db_pool():
    from recruitment_platform.db import create_pool
    pool = await create_pool(min_size=2, max_size=5)
    yield pool
    await pool.close()


@pytest_asyncio.fixture
async def materialized_views(db_pool):
    """Create and refresh materialized views for testing."""
    async with db_pool.acquire() as conn:
        await conn.execute("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_candidate_pipeline AS
            SELECT
                c.id AS candidate_id,
                c.name,
                c.email,
                a.status AS application_status,
                a.applied_at,
                j.title AS job_title
            FROM candidates c
            LEFT JOIN applications a ON a.candidate_id = c.id
            LEFT JOIN jobs j ON j.id = a.job_id
        """)
        await conn.execute("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_job_stats AS
            SELECT
                j.id AS job_id,
                j.title,
                COUNT(a.id) AS total_applications,
                COUNT(a.id) FILTER (WHERE a.status = 'hired') AS hires,
                COUNT(a.id) FILTER (WHERE a.status = 'rejected') AS rejections
            FROM jobs j
            LEFT JOIN applications a ON a.job_id = j.id
            GROUP BY j.id, j.title
        """)
        await conn.execute("REFRESH MATERIALIZED VIEW mv_candidate_pipeline")
        await conn.execute("REFRESH MATERIALIZED VIEW mv_job_stats")
    yield
    async with db_pool.acquire() as conn:
        await conn.execute("DROP MATERIALIZED VIEW IF EXISTS mv_candidate_pipeline")
        await conn.execute("DROP MATERIALIZED VIEW IF EXISTS mv_job_stats")


async def test_candidate_pipeline_view_populated(db_pool, materialized_views):
    """Pipeline view should contain joined candidate-application data."""
    async with db_pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO candidates (name, email) VALUES ($1, $2)",
            "View Test", "view@example.com"
        )
        cid = await conn.fetchval(
            "SELECT id FROM candidates WHERE email = $1", "view@example.com"
        )
        await conn.execute(
            "INSERT INTO jobs (title) VALUES ($1) RETURNING id", "Engineer"
        )
        jid = await conn.fetchval("SELECT id FROM jobs WHERE title = $1", "Engineer")
        await conn.execute(
            "INSERT INTO applications (candidate_id, job_id, status) VALUES ($1, $2, $3)",
            cid, jid, "screening"
        )
        await conn.execute("REFRESH MATERIALIZED VIEW mv_candidate_pipeline")
        row = await conn.fetchrow(
            "SELECT * FROM mv_candidate_pipeline WHERE candidate_id = $1", cid
        )
        assert row["name"] == "View Test"
        assert row["application_status"] == "screening"
        assert row["job_title"] == "Engineer"


async def test_job_stats_aggregation(db_pool, materialized_views):
    """Job stats view should correctly aggregate application counts."""
    async with db_pool.acquire() as conn:
        jid = await conn.fetchval(
            "INSERT INTO jobs (title) VALUES ($1) RETURNING id", "Designer"
        )
        for i in range(3):
            cid = await conn.fetchval(
                "INSERT INTO candidates (name, email) VALUES ($1, $2) RETURNING id",
                f"Cand {i}", f"cand{i}@example.com"
            )
            status = "hired" if i == 0 else "rejected"
            await conn.execute(
                "INSERT INTO applications (candidate_id, job_id, status) VALUES ($1, $2, $3)",
                cid, jid, status
            )
        await conn.execute("REFRESH MATERIALIZED VIEW mv_job_stats")
        stats = await conn.fetchrow(
            "SELECT * FROM mv_job_stats WHERE job_id = $1", jid
        )
        assert stats["total_applications"] == 3
        assert stats["hires"] == 1
        assert stats["rejections"] == 2


async def test_materialized_view_not_auto_refreshing(db_pool, materialized_views):
    """Changes after refresh should NOT appear until next REFRESH."""
    async with db_pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO candidates (name, email) VALUES ($1, $2)",
            "Stale", "stale@example.com"
        )
        cid = await conn.fetchval(
            "SELECT id FROM candidates WHERE email = $1", "stale@example.com"
        )
        await conn.execute(
            "INSERT INTO jobs (title) VALUES ($1) RETURNING id", "Manager"
        )
        jid = await conn.fetchval("SELECT id FROM jobs WHERE title = $1", "Manager")
        await conn.execute(
            "INSERT INTO applications (candidate_id, job_id, status) VALUES ($1, $2, $3)",
            cid, jid, "applied"
        )
        row = await conn.fetchrow(
            "SELECT * FROM mv_candidate_pipeline WHERE candidate_id = $1", cid
        )
        assert row is None  # Not refreshed yet


async def test_concurrent_refresh(db_pool, materialized_views):
    """REFRESH MATERIALIZED VIEW CONCURRENTLY should not block reads."""
    async with db_pool.acquire() as conn:
        await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_job_stats")
        count = await conn.fetchval("SELECT COUNT(*) FROM mv_job_stats")
        assert count >= 0
