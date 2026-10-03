"""Stress test: find the breaking point by ramping up concurrency."""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

import httpx


@dataclass
class StressResult:
    concurrency: int = 0
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    latencies: list[float] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def error_rate(self) -> float:
        return self.failed / self.total_requests if self.total_requests > 0 else 0.0

    @property
    def max_latency(self) -> float:
        return max(self.latencies) if self.latencies else 0.0


async def _single_request(
    client: httpx.AsyncClient, url: str, result: StressResult
) -> None:
    start = time.perf_counter()
    try:
        resp = await client.get(url, timeout=5.0)
        elapsed = time.perf_counter() - start
        result.latencies.append(elapsed)
        result.total_requests += 1
        if resp.status_code == 200:
            result.successful += 1
        else:
            result.failed += 1
            result.errors.append(f"HTTP {resp.status_code}")
    except Exception as exc:
        elapsed = time.perf_counter() - start
        result.latencies.append(elapsed)
        result.total_requests += 1
        result.failed += 1
        result.errors.append(str(exc))


async def _run_at_concurrency(
    url: str, concurrency: int, total_requests: int
) -> StressResult:
    result = StressResult(concurrency=concurrency)
    async with httpx.AsyncClient() as client:
        semaphore = asyncio.Semaphore(concurrency)

        async def bounded() -> None:
            async with semaphore:
                await _single_request(client, url, result)

        tasks = [asyncio.create_task(bounded()) for _ in range(total_requests)]
        await asyncio.gather(*tasks)
    return result


async def find_breaking_point(
    base_url: str,
    endpoint: str,
    start_concurrency: int = 10,
    max_concurrency: int = 500,
    step: int = 10,
    requests_per_level: int = 100,
) -> StressResult:
    url = f"{base_url}{endpoint}"
    breaking_point: StressResult | None = None

    for concurrency in range(start_concurrency, max_concurrency + 1, step):
        result = await _run_at_concurrency(url, concurrency, requests_per_level)
        if result.error_rate > 0.1 or result.max_latency > 5.0:
            breaking_point = result
            break

    return breaking_point or result


def test_stress_find_breaking_point() -> None:
    result = asyncio.run(
        find_breaking_point(
            "http://localhost:8000",
            "/health",
            start_concurrency=10,
            max_concurrency=200,
            step=20,
            requests_per_level=50,
        )
    )
    assert result.concurrency > 0
    assert result.total_requests > 0


def test_stress_sustained_burst() -> None:
    async def burst() -> StressResult:
        url = "http://localhost:8000/health"
        result = StressResult(concurrency=100)
        async with httpx.AsyncClient() as client:
            tasks = [
                asyncio.create_task(_single_request(client, url, result))
                for _ in range(100)
            ]
            await asyncio.gather(*tasks)
        return result

    result = asyncio.run(burst())
    assert result.total_requests == 100
    assert result.error_rate < 0.5
