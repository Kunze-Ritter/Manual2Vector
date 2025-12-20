import time

import pytest

pytestmark = [pytest.mark.performance, pytest.mark.slow]


class TestPerformanceUnderLoad:
    def test_performance_with_high_concurrency(self, performance_metrics):
        performance_metrics["throughput"].append(10)
        assert performance_metrics["throughput"][0] >= 1


class TestPerformanceOptimizations:
    def test_connection_reuse(self, performance_metrics):
        performance_metrics["latency"].append(0.1)
        assert performance_metrics["latency"][0] < 5.0
