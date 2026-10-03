"""Endurance test: sustained load over time to detect memory leaks and degradation."""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

import httpx


@dataclass
class EnduranceResult:
    duration_seconds: float = 0.0
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    latencies: list[float] = field(default_factory=list)
    errors_over_time: list[tuple[float, int]] = field(default_factory=list)

    @property
    def avg_latency(self) -> float:
        return sum(self.latencies) / len(self.latencies) if self.latencies else 0.0

    @property
    def latency_trend(self) -> str:
        if len(self.latencies) < 10:
            return "insufficient_data"
        mid = len(self.latencies) // 2
        first_half = sum(self.latencies[:mid]) / mid
        second_half = sum(self.latencies[mid:]) / (len(self.latencies) - mid)
        if second_half > first_half * 1.2:
            return "degrading"
        return "stable"


async def _endurance_worker(
    client: httpx.AsyncClient,
    url: str,
    result: EnduranceResult,
    stop_event: asyncio.Event,
) -> None:
    while not stop_event.is_set():
        start = time.perf_counter()
        try:
            resp = await client.get(url, timeout=10.0)
            elapsed = time.perf_counter() - start
            result.latencies.append(elapsed)
            result.total_requests += 1
            if resp.status_code == 200:
                result.successful += 1
            else:
                result.failed += 1
                result.errors_over_time.append((time.time(), result.failed))
        except Exception:
            elapsed = time.perf_counter() - start
            result.latencies.append(elapsed)
            result.total_requests += 1
            result.failed += 1
            result.errors_over_time.append((time.time(), result.failed))
        await asyncio.sleep(0.01)


async def run_endurance_test(
    base_url: str,
    endpoint: str,
    duration_seconds: float,
    concurrent_workers: int = 10,
) -> EnduranceResult:
    result = EnduranceResult(duration_seconds=duration_seconds)
    url = f"{base_url}{endpoint}"
    stop_event = asyncio.Event()

    async with httpx.AsyncClient() as client:
        workers = [
            asyncio.create_task(_endurance_worker(client, url, result, stop_event))
            for _ in range(concurrent_workers)
        ]
        await asyncio.sleep(duration_seconds)
        stop_event.set()
        await asyncio.gather(*workers)

    return result


def test_endurance_short_burst() -> None:
    result = asyncio.run(
        run_endurance_test(
            "http://localhost:8000",
            "/health",
            duration_seconds=5.0,
            concurrent_workers=5,
        )
    )
    assert result.total_requests > 0
    assert result.failed == 0
    assert result.latency_trend in ("stable", "insufficient_data")


def test_endurance_sustained_load() -> None:
    result = asyncio.run(
        run_endurance_test(
            "http://localhost:8000",
            "/api/v1/tiers",
            duration_seconds=10.0,
            concurrent_workers=10,
        )
    )
    assert result.total_requests > 50
    assert result.latency_trend == "stable"
