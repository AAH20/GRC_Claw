"""Load test: concurrent users hitting the API simultaneously."""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

import httpx


@dataclass
class LoadResult:
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    latencies: list[float] = field(default_factory=list)

    @property
    def avg_latency(self) -> float:
        return sum(self.latencies) / len(self.latencies) if self.latencies else 0.0

    @property
    def p95_latency(self) -> float:
        if not self.latencies:
            return 0.0
        sorted_lat = sorted(self.latencies)
        idx = int(len(sorted_lat) * 0.95)
        return sorted_lat[min(idx, len(sorted_lat) - 1)]

    @property
    def throughput(self) -> float:
        total_time = sum(self.latencies)
        return self.successful / total_time if total_time > 0 else 0.0


async def _hit_endpoint(
    client: httpx.AsyncClient, url: str, results: LoadResult
) -> None:
    start = time.perf_counter()
    try:
        resp = await client.get(url, timeout=10.0)
        elapsed = time.perf_counter() - start
        results.latencies.append(elapsed)
        results.total_requests += 1
        if resp.status_code == 200:
            results.successful += 1
        else:
            results.failed += 1
    except Exception:
        elapsed = time.perf_counter() - start
        results.latencies.append(elapsed)
        results.total_requests += 1
        results.failed += 1


async def run_load_test(
    base_url: str,
    endpoint: str,
    concurrent_users: int,
    requests_per_user: int,
) -> LoadResult:
    results = LoadResult()
    url = f"{base_url}{endpoint}"
    async with httpx.AsyncClient() as client:
        tasks = []
        for _ in range(concurrent_users):
            for _ in range(requests_per_user):
                tasks.append(_hit_endpoint(client, url, results))
        await asyncio.gather(*tasks)
    return results


def test_load_health_endpoint() -> None:
    result = asyncio.run(
        run_load_test("http://localhost:8000", "/health", concurrent_users=50, requests_per_user=20)
    )
    assert result.failed == 0, f"{result.failed} requests failed"
    assert result.total_requests == 1000
    assert result.p95_latency < 1.0, f"P95 latency {result.p95_latency:.3f}s exceeds 1s threshold"


def test_load_tiers_endpoint() -> None:
    result = asyncio.run(
        run_load_test("http://localhost:8000", "/api/v1/tiers", concurrent_users=30, requests_per_user=10)
    )
    assert result.failed == 0
    assert result.total_requests == 300
    assert result.throughput > 50, f"Throughput {result.throughput:.1f} req/s below 50"


def test_load_search_endpoint() -> None:
    result = asyncio.run(
        run_load_test("http://localhost:8000", "/api/v1/search?q=test", concurrent_users=20, requests_per_user=5)
    )
    assert result.failed == 0
    assert result.total_requests == 100
    assert result.avg_latency < 0.5, f"Avg latency {result.avg_latency:.3f}s exceeds 0.5s"
