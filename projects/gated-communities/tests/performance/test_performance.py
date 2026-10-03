"""Performance tests using pytest-benchmark."""
from __future__ import annotations

from fastapi.testclient import TestClient


class TestPerformance:
    def test_health_check_performance(self, client: TestClient, benchmark) -> None:
        result = benchmark(client.get, "/health")
        assert result.status_code == 200

    def test_tiers_list_performance(self, client: TestClient, benchmark) -> None:
        result = benchmark(client.get, "/api/v1/tiers")
        assert result.status_code == 200

    def test_search_performance(self, client: TestClient, benchmark) -> None:
        result = benchmark(client.get, "/api/v1/search?q=test")
        assert result.status_code == 200

    def test_concurrent_requests(self, client: TestClient) -> None:
        import concurrent.futures

        def make_request():
            return client.get("/health")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert all(r.status_code == 200 for r in results)
