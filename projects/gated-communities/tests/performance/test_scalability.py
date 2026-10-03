"""Scalability test: horizontal scaling behavior across multiple instances."""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

import httpx


@dataclass
class ScalabilityResult:
    instances: int = 0
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    latencies: list[float] = field(default_factory=list)
    per_instance_throughput: dict[int, float] = field(default_factory=dict)

    @property
    def total_throughput(self) -> float:
        return sum(self.per_instance_throughput.values())

    @property
    def scaling_efficiency(self) -> float:
        if not self.per_instance_throughput or self.instances <= 1:
            return 1.0
        throughputs = list(self.per_instance_throughput.values())
        avg_throughput = sum(throughputs) / len(throughputs)
        max_throughput = max(throughputs)
        return avg_throughput / max_throughput if max_throughput > 0 else 0.0


async def _probe_instance(
    base_url: str, instance_id: int, num_requests: int
) -> tuple[int, float, float]:
    url = f"{base_url}/health"
    success = 0
    latencies: list[float] = []
    async with httpx.AsyncClient() as client:
        for _ in range(num_requests):
            start = time.perf_counter()
            try:
                resp = await client.get(url, timeout=5.0)
                elapsed = time.perf_counter() - start
                latencies.append(elapsed)
                if resp.status_code == 200:
                    success += 1
            except Exception:
                elapsed = time.perf_counter() - start
                latencies.append(elapsed)
    total_time = sum(latencies)
    throughput = success / total_time if total_time > 0 else 0.0
    return success, throughput, max(latencies) if latencies else 0.0


async def run_scalability_test(
    base_urls: list[str],
    requests_per_instance: int = 50,
) -> ScalabilityResult:
    result = ScalabilityResult(instances=len(base_urls))
    tasks = [
        asyncio.create_task(_probe_instance(url, i, requests_per_instance))
        for i, url in enumerate(base_urls)
    ]
    outcomes = await asyncio.gather(*tasks)

    for instance_id, (success, throughput, max_lat) in enumerate(outcomes):
        result.successful += success
        result.total_requests += requests_per_instance
        result.failed += requests_per_instance - success
        result.per_instance_throughput[instance_id] = throughput

    return result


def test_scalability_single_instance() -> None:
    result = asyncio.run(
        run_scalability_test(["http://localhost:8000"], requests_per_instance=50)
    )
    assert result.instances == 1
    assert result.successful == 50
    assert result.total_throughput > 0


def test_scalability_multiple_instances() -> None:
    urls = [
        "http://localhost:8000",
        "http://localhost:8001",
        "http://localhost:8002",
    ]
    result = asyncio.run(run_scalability_test(urls, requests_per_instance=30))
    assert result.instances == 3
    assert result.total_requests == 90
    assert result.scaling_efficiency > 0.5


def test_scalability_linear_growth() -> None:
    async def measure_at_scale(num_instances: int) -> float:
        urls = [f"http://localhost:{8000 + i}" for i in range(num_instances)]
        res = await run_scalability_test(urls, requests_per_instance=20)
        return res.total_throughput

    throughput_1 = asyncio.run(measure_at_scale(1))
    throughput_2 = asyncio.run(measure_at_scale(2))
    if throughput_1 > 0:
        ratio = throughput_2 / throughput_1
        assert ratio > 1.2, f"Scaling ratio {ratio:.2f} indicates poor horizontal scaling"
