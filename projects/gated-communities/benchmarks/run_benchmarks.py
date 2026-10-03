#!/usr/bin/env python3
"""Performance benchmarks for Gated Communities: API, DB, Frontend, Resources."""

from __future__ import annotations

import asyncio
import json
import os
import resource
import statistics
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

BASE_URL = os.getenv("BENCH_API_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("BENCH_FRONTEND_URL", "http://localhost:3000")
DATABASE_URL = os.getenv(
    "BENCH_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/gated_communities",
)
RESULTS_DIR = Path("/Users/ahmedhassan/GRC_Claw/analysis/w2-performance")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class BenchmarkResult:
    name: str
    metrics: dict[str, Any] = field(default_factory=dict)
    raw_data: list[float] = field(default_factory=list)


def _stats(times: list[float]) -> dict[str, float]:
    """Compute min/avg/max for positive timings."""
    valid = [t for t in times if t > 0]
    if not valid:
        return {"avg_ms": 0, "min_ms": 0, "max_ms": 0}
    return {
        "avg_ms": round(statistics.mean(valid), 2),
        "min_ms": round(min(valid), 2),
        "max_ms": round(max(valid), 2),
    }


def _pct(sorted_vals: list[float], p: float) -> float:
    """Return percentile from pre-sorted values."""
    if not sorted_vals:
        return 0
    return round(sorted_vals[min(int(len(sorted_vals) * p), len(sorted_vals) - 1)], 2)


async def benchmark_api() -> BenchmarkResult:
    """Measure API response time and throughput."""
    result = BenchmarkResult(name="API")
    endpoints = [
        "/health", "/api/v1/health", "/api/v1/ready",
        "/api/v1/live", "/api/v1/tiers", "/docs", "/openapi.json",
    ]
    response_times: dict[str, list[float]] = {}
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        for ep in endpoints:
            times: list[float] = []
            for _ in range(50):
                start = time.perf_counter()
                try:
                    await client.get(ep)
                    times.append((time.perf_counter() - start) * 1000)
                except Exception:
                    times.append(-1.0)
            response_times[ep] = times
        # Throughput: 200 concurrent requests
        start_total = time.perf_counter()
        responses = await asyncio.gather(
            *[client.get("/health") for _ in range(200)], return_exceptions=True
        )
        total_elapsed = time.perf_counter() - start_total
    successful = sum(1 for r in responses if not isinstance(r, Exception))
    all_times = [t for ts in response_times.values() for t in ts if t > 0]
    sorted_all = sorted(all_times)
    result.metrics = {
        "avg_response_ms": round(statistics.mean(all_times), 2) if all_times else 0,
        "p50_response_ms": _pct(sorted_all, 0.50),
        "p95_response_ms": _pct(sorted_all, 0.95),
        "p99_response_ms": _pct(sorted_all, 0.99),
        "throughput_rps": round(successful / total_elapsed, 2) if total_elapsed > 0 else 0,
        "total_requests": len(all_times),
        "failed_requests": sum(1 for ts in response_times.values() for t in ts if t < 0),
        "endpoint_breakdown": {ep: _stats(ts) for ep, ts in response_times.items()},
    }
    result.raw_data = all_times
    return result


def benchmark_database() -> BenchmarkResult:
    """Measure database query performance."""
    result = BenchmarkResult(name="Database")
    try:
        import asyncpg
    except ImportError:
        result.metrics = {"error": "asyncpg not available"}
        return result

    async def _run() -> dict[str, Any]:
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            queries = {
                "simple_select": "SELECT 1",
                "count_communities": "SELECT COUNT(*) FROM communities",
                "count_members": "SELECT COUNT(*) FROM members",
                "count_tiers": "SELECT COUNT(*) FROM tiers",
                "join_query": "SELECT c.name, COUNT(m.id) FROM communities c LEFT JOIN members m ON m.community_id = c.id GROUP BY c.name LIMIT 100",
                "jsonb_query": "SELECT id, name FROM communities WHERE settings != '{}'::jsonb LIMIT 50",
                "full_text_search": "SELECT id, name FROM communities WHERE search_vector @@ plainto_tsquery('english', 'test') LIMIT 20",
            }
            timings: dict[str, list[float]] = {}
            for name, query in queries.items():
                times: list[float] = []
                for _ in range(20):
                    start = time.perf_counter()
                    try:
                        await conn.fetch(query)
                        times.append((time.perf_counter() - start) * 1000)
                    except Exception:
                        times.append(-1.0)
                timings[name] = times
            pool_start = time.perf_counter()
            pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)
            pool_times: list[float] = []
            for _ in range(50):
                start = time.perf_counter()
                async with pool.acquire() as c:
                    await c.fetchval("SELECT 1")
                pool_times.append((time.perf_counter() - start) * 1000)
            await pool.close()
            pool_elapsed = (time.perf_counter() - pool_start) * 1000
            all_times = [t for ts in timings.values() for t in ts if t > 0]
            return {
                "avg_query_ms": round(statistics.mean(all_times), 2) if all_times else 0,
                "p95_query_ms": _pct(sorted(all_times), 0.95),
                "pool_avg_ms": round(statistics.mean(pool_times), 2) if pool_times else 0,
                "pool_total_ms": round(pool_elapsed, 2),
                "query_breakdown": {n: _stats(ts) for n, ts in timings.items()},
            }
        finally:
            await conn.close()

    try:
        result.metrics = asyncio.run(_run())
    except Exception as e:
        result.metrics = {"error": str(e)}
    return result


def benchmark_frontend() -> BenchmarkResult:
    """Measure frontend Core Web Vitals."""
    result = BenchmarkResult(name="Frontend")
    pages = ["/", "/login", "/register"]
    page_metrics: dict[str, Any] = {}
    for page in pages:
        url = f"{FRONTEND_URL}{page}"
        try:
            proc = subprocess.run(
                ["curl", "-o", "/dev/null", "-s", "-w",
                 "%{time_total},%{time_starttransfer},%{time_pretransfer},%{size_download},%{http_code}",
                 "--max-time", "10", url],
                capture_output=True, text=True, timeout=15,
            )
            if proc.returncode == 0 and proc.stdout:
                p = proc.stdout.strip().split(",")
                if len(p) >= 5:
                    page_metrics[page] = {
                        "total_time_ms": round(float(p[0]) * 1000, 2),
                        "ttfb_ms": round(float(p[1]) * 1000, 2),
                        "pretransfer_ms": round(float(p[2]) * 1000, 2),
                        "size_kb": round(float(p[3]) / 1024, 2),
                        "status_code": int(p[4]),
                    }
        except Exception as e:
            page_metrics[page] = {"error": str(e)}
    next_dir = Path("/Users/ahmedhassan/GRC_Claw/projects/gated-communities/frontend/.next")
    build_size = sum(f.stat().st_size for f in next_dir.rglob("*") if f.is_file()) if next_dir.exists() else 0
    static_dir = next_dir / "static"
    static_size = sum(f.stat().st_size for f in static_dir.rglob("*") if f.is_file()) if static_dir.exists() else 0
    result.metrics = {
        "page_metrics": page_metrics,
        "build_size_mb": round(build_size / (1024 * 1024), 2),
        "static_size_mb": round(static_size / (1024 * 1024), 2),
        "estimated_lcp_ms": page_metrics.get("/", {}).get("ttfb_ms", 0),
        "estimated_fcp_ms": page_metrics.get("/", {}).get("pretransfer_ms", 0),
    }
    return result


def benchmark_resources() -> BenchmarkResult:
    """Measure CPU, memory, and disk usage."""
    result = BenchmarkResult(name="Resources")
    usage = resource.getrusage(resource.RUSAGE_SELF)
    project_dir = Path("/Users/ahmedhassan/GRC_Claw/projects/gated-communities")
    skip_dirs = {".venv", "node_modules", ".next", "__pycache__"}
    total_size = sum(
        f.stat().st_size
        for f in project_dir.rglob("*")
        if f.is_file() and not any(d in f.parts for d in skip_dirs)
    )
    def _cmd(args: list[str]) -> str:
        try:
            return subprocess.run(args, capture_output=True, text=True).stdout.strip()
        except Exception:
            return "N/A"
    result.metrics = {
        "process_memory_mb": round(usage.ru_maxrss / 1024, 2),
        "project_size_mb": round(total_size / (1024 * 1024), 2),
        "python_processes": len(_cmd(["pgrep", "-f", "gated_communities"]).split("\n")) if _cmd(["pgrep", "-f", "gated_communities"]) else 0,
        "system_load": _cmd(["sysctl", "-n", "vm.loadavg"]),
        "cpu": _cmd(["sysctl", "-n", "machdep.cpu.brand_string"]),
        "user_time_s": round(usage.ru_utime, 2),
        "system_time_s": round(usage.ru_stime, 2),
    }
    return result


def _table_row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def generate_report(data: dict[str, Any]) -> str:
    """Generate markdown report from benchmark data."""
    api = data["benchmarks"].get("API", {})
    db = data["benchmarks"].get("Database", {})
    fe = data["benchmarks"].get("Frontend", {})
    res = data["benchmarks"].get("Resources", {})
    lines = [
        "# Gated Communities — Performance Benchmark Report",
        "",
        f"**Date:** {data.get('timestamp', 'N/A')}",
        "",
        "## 1. API Performance",
        "",
        _table_row(["Metric", "Value"]),
        _table_row(["--------", "-------"]),
        _table_row(["Avg Response Time", f"{api.get('avg_response_ms', 'N/A')} ms"]),
        _table_row(["P50 Response Time", f"{api.get('p50_response_ms', 'N/A')} ms"]),
        _table_row(["P95 Response Time", f"{api.get('p95_response_ms', 'N/A')} ms"]),
        _table_row(["P99 Response Time", f"{api.get('p99_response_ms', 'N/A')} ms"]),
        _table_row(["Throughput", f"{api.get('throughput_rps', 'N/A')} req/s"]),
        _table_row(["Total Requests", str(api.get('total_requests', 'N/A'))]),
        _table_row(["Failed Requests", str(api.get('failed_requests', 'N/A'))]),
        "",
        "### Endpoint Breakdown",
        "",
        _table_row(["Endpoint", "Avg (ms)", "Min (ms)", "Max (ms)"]),
        _table_row(["----------", "----------", "----------", "----------"]),
    ]
    for ep, v in api.get("endpoint_breakdown", {}).items():
        lines.append(_table_row([ep, str(v["avg_ms"]), str(v["min_ms"]), str(v["max_ms"])]))
    lines += [
        "",
        "## 2. Database Performance",
        "",
        _table_row(["Metric", "Value"]),
        _table_row(["--------", "-------"]),
        _table_row(["Avg Query Time", f"{db.get('avg_query_ms', 'N/A')} ms"]),
        _table_row(["P95 Query Time", f"{db.get('p95_query_ms', 'N/A')} ms"]),
        _table_row(["Pool Avg Time", f"{db.get('pool_avg_ms', 'N/A')} ms"]),
        _table_row(["Pool Total (50 ops)", f"{db.get('pool_total_ms', 'N/A')} ms"]),
        "",
        "### Query Breakdown",
        "",
        _table_row(["Query", "Avg (ms)", "Min (ms)", "Max (ms)"]),
        _table_row(["-------", "----------", "----------", "----------"]),
    ]
    for q, v in db.get("query_breakdown", {}).items():
        lines.append(_table_row([q, str(v["avg_ms"]), str(v["min_ms"]), str(v["max_ms"])]))
    lines += [
        "",
        "## 3. Frontend Performance (Core Web Vitals)",
        "",
        _table_row(["Page", "Total (ms)", "TTFB (ms)", "Size (KB)", "Status"]),
        _table_row(["------", "------------", "-----------", "-----------", "--------"]),
    ]
    for page, v in fe.get("page_metrics", {}).items():
        if "error" in v:
            lines.append(_table_row([page, f"Error: {v['error']}", "-", "-", "-"]))
        else:
            lines.append(_table_row([page, str(v["total_time_ms"]), str(v["ttfb_ms"]), str(v["size_kb"]), str(v["status_code"])]))
    lines += [
        "",
        f"**Build Size:** {fe.get('build_size_mb', 'N/A')} MB",
        f"**Static Assets:** {fe.get('static_size_mb', 'N/A')} MB",
        f"**Estimated LCP:** {fe.get('estimated_lcp_ms', 'N/A')} ms",
        f"**Estimated FCP:** {fe.get('estimated_fcp_ms', 'N/A')} ms",
        "",
        "## 4. Resource Usage",
        "",
        _table_row(["Metric", "Value"]),
        _table_row(["--------", "-------"]),
        _table_row(["Process Memory", f"{res.get('process_memory_mb', 'N/A')} MB"]),
        _table_row(["Project Size", f"{res.get('project_size_mb', 'N/A')} MB"]),
        _table_row(["Python Processes", str(res.get('python_processes', 'N/A'))]),
        _table_row(["System Load", str(res.get('system_load', 'N/A'))]),
        _table_row(["CPU", str(res.get('cpu', 'N/A'))]),
        _table_row(["User Time", f"{res.get('user_time_s', 'N/A')} s"]),
        _table_row(["System Time", f"{res.get('system_time_s', 'N/A')} s"]),
        "",
        "## Summary",
        "",
        f"- API avg response: **{api.get('avg_response_ms', 'N/A')}ms** with **{api.get('throughput_rps', 'N/A')} req/s** throughput",
        f"- Database avg query: **{db.get('avg_query_ms', 'N/A')}ms**",
        f"- Frontend build size: **{fe.get('build_size_mb', 'N/A')}MB**",
        f"- Memory usage: **{res.get('process_memory_mb', 'N/A')}MB**",
        "",
    ]
    return "\n".join(lines)


async def main() -> None:
    print("Running Gated Communities Performance Benchmarks...")
    print("=" * 60)
    results: list[BenchmarkResult] = []
    print("\n[1/4] API Benchmark...")
    api_result = await benchmark_api()
    results.append(api_result)
    print(f"  Avg response: {api_result.metrics.get('avg_response_ms', 'N/A')}ms")
    print(f"  Throughput: {api_result.metrics.get('throughput_rps', 'N/A')} req/s")
    print("\n[2/4] Database Benchmark...")
    db_result = benchmark_database()
    results.append(db_result)
    print(f"  Avg query: {db_result.metrics.get('avg_query_ms', 'N/A')}ms")
    print("\n[3/4] Frontend Benchmark...")
    fe_result = benchmark_frontend()
    results.append(fe_result)
    print(f"  Build size: {fe_result.metrics.get('build_size_mb', 'N/A')}MB")
    print("\n[4/4] Resource Usage...")
    res_result = benchmark_resources()
    results.append(res_result)
    print(f"  Memory: {res_result.metrics.get('process_memory_mb', 'N/A')}MB")
    output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "benchmarks": {r.name: r.metrics for r in results},
    }
    results_file = RESULTS_DIR / "benchmark_results.json"
    results_file.write_text(json.dumps(output, indent=2))
    print(f"\nResults saved to: {results_file}")
    report_path = RESULTS_DIR / "gated-communities.md"
    report_path.write_text(generate_report(output))
    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
