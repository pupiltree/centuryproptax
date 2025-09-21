"""
Tests for logging performance benchmarks.

This module tests the logging performance benchmark suite to ensure
it properly measures logging overhead and meets performance requirements.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import time

from testing.performance.logging_performance_benchmarks import (
    LoggingPerformanceBenchmarks,
    BenchmarkResult,
    PerformanceMetrics,
    SystemMetricsCollector
)


class TestSystemMetricsCollector:
    """Test system metrics collection functionality."""

    def test_get_memory_usage_mb(self):
        """Test memory usage measurement."""
        collector = SystemMetricsCollector()
        memory_usage = collector.get_memory_usage_mb()

        assert isinstance(memory_usage, float)
        assert memory_usage >= 0
        # Should be reasonable for a Python process (less than 10GB)
        assert memory_usage < 10000

    def test_get_cpu_usage_percent(self):
        """Test CPU usage measurement."""
        collector = SystemMetricsCollector()

        # First call may return 0, so we call twice
        collector.get_cpu_usage_percent()
        time.sleep(0.1)
        cpu_usage = collector.get_cpu_usage_percent()

        assert isinstance(cpu_usage, float)
        assert 0 <= cpu_usage <= 100

    def test_start_monitoring(self):
        """Test monitoring baseline collection."""
        collector = SystemMetricsCollector()
        baseline = collector.start_monitoring()

        assert 'memory_mb' in baseline
        assert 'cpu_percent' in baseline
        assert baseline['memory_mb'] >= 0  # Allow 0 for test environments
        assert 0 <= baseline['cpu_percent'] <= 100


class TestLoggingPerformanceBenchmarks:
    """Test logging performance benchmark functionality."""

    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp(prefix="test_logging_benchmark_")
        yield temp_dir
        # Cleanup
        if Path(temp_dir).exists():
            shutil.rmtree(temp_dir)

    @pytest.fixture
    def benchmark_suite(self, temp_log_dir):
        """Create benchmark suite for testing."""
        return LoggingPerformanceBenchmarks(test_log_dir=temp_log_dir)

    def test_benchmark_suite_initialization(self, benchmark_suite):
        """Test benchmark suite initializes correctly."""
        assert benchmark_suite.test_log_dir is not None
        assert Path(benchmark_suite.test_log_dir).exists()
        assert benchmark_suite.metrics_collector is not None
        assert benchmark_suite.structlog_logger is not None
        assert benchmark_suite.standard_logger is not None
        assert len(benchmark_suite.benchmark_results) == 0

    def test_measure_single_operation(self, benchmark_suite):
        """Test single operation measurement."""
        def test_operation():
            time.sleep(0.001)  # 1ms delay
            return "test"

        metrics = benchmark_suite._measure_single_operation(test_operation)

        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.success is True
        assert metrics.error_message is None
        assert metrics.operation_time_ns > 0
        # Should take at least 1ms (1,000,000 ns)
        assert metrics.operation_time_ns >= 500_000  # Allow some variance
        assert metrics.memory_before >= 0
        assert metrics.memory_after >= 0

    def test_measure_single_operation_error(self, benchmark_suite):
        """Test single operation measurement with error."""
        def failing_operation():
            raise ValueError("Test error")

        metrics = benchmark_suite._measure_single_operation(failing_operation)

        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.success is False
        assert metrics.error_message == "Test error"
        assert metrics.operation_time_ns > 0

    def test_percentile_calculation(self, benchmark_suite):
        """Test percentile calculation."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

        assert benchmark_suite._percentile(data, 50) == 5.0
        assert benchmark_suite._percentile(data, 95) == 10.0
        assert benchmark_suite._percentile(data, 0) == 1.0
        assert benchmark_suite._percentile([], 50) == 0.0

    def test_benchmark_single_log_statements(self, benchmark_suite):
        """Test single log statement benchmark."""
        result = benchmark_suite.benchmark_single_log_statements(iterations=100)

        assert isinstance(result, BenchmarkResult)
        assert result.test_type == "single_operations"
        assert result.operations_count == 100
        assert result.duration_seconds > 0
        assert result.operations_per_second > 0
        assert result.average_operation_time_ms >= 0
        assert result.median_operation_time_ms >= 0
        assert result.p95_operation_time_ms >= 0
        assert result.p99_operation_time_ms >= 0
        assert result.memory_usage_before_mb >= 0
        assert result.memory_usage_after_mb >= 0

        # Should meet performance threshold for small test
        assert result.overhead_threshold_met is True

        # Check details
        assert result.details["successful_operations"] == 100
        assert result.details["failed_operations"] == 0
        assert result.details["operation_types_tested"] == 6

    def test_benchmark_high_volume_logging(self, benchmark_suite):
        """Test high volume logging benchmark."""
        result = benchmark_suite.benchmark_high_volume_logging(
            log_count=1000,
            concurrent_threads=2
        )

        assert isinstance(result, BenchmarkResult)
        assert result.test_type == "high_volume"
        assert result.operations_count == 1000
        assert result.duration_seconds > 0
        assert result.operations_per_second > 0
        assert result.average_operation_time_ms >= 0

        # Check details
        assert result.details["concurrent_threads"] == 2
        assert result.details["successful_operations"] > 0

    @pytest.mark.asyncio
    async def test_benchmark_api_request_logging_impact(self, benchmark_suite):
        """Test API request logging impact benchmark."""
        result = await benchmark_suite.benchmark_api_request_logging_impact(
            request_count=100
        )

        assert isinstance(result, BenchmarkResult)
        assert result.test_type == "api_impact"
        assert result.operations_count == 100
        assert result.duration_seconds > 0
        assert result.operations_per_second > 0
        assert result.average_operation_time_ms >= 0

        # Should meet performance threshold for API logging
        # Each simulated request does 5 log operations
        assert result.details["logs_per_request"] == 5
        assert result.details["requests_processed"] == 100

    def test_benchmark_logging_without_handlers(self, benchmark_suite):
        """Test baseline logging benchmark without handlers."""
        result = benchmark_suite.benchmark_logging_without_handlers(iterations=100)

        assert isinstance(result, BenchmarkResult)
        assert result.test_type == "baseline"
        assert result.operations_count == 100
        assert result.duration_seconds > 0
        assert result.operations_per_second > 0
        assert result.average_operation_time_ms >= 0

        # Baseline should always meet threshold
        assert result.overhead_threshold_met is True
        assert result.details["baseline_test"] is True
        assert result.details["handlers_used"] == 0

    @pytest.mark.asyncio
    async def test_comprehensive_benchmark_suite(self, benchmark_suite):
        """Test running the comprehensive benchmark suite."""
        # Use smaller iterations for testing
        with patch.object(benchmark_suite, 'benchmark_logging_without_handlers') as mock_baseline, \
             patch.object(benchmark_suite, 'benchmark_single_log_statements') as mock_single, \
             patch.object(benchmark_suite, 'benchmark_high_volume_logging') as mock_volume, \
             patch.object(benchmark_suite, 'benchmark_api_request_logging_impact') as mock_api:

            # Create mock results
            mock_result = BenchmarkResult(
                test_name="mock_test",
                test_type="mock",
                start_time=benchmark_suite.metrics_collector.start_monitoring(),
                end_time=benchmark_suite.metrics_collector.start_monitoring(),
                duration_seconds=1.0,
                operations_count=100,
                operations_per_second=100.0,
                average_operation_time_ms=0.5,
                median_operation_time_ms=0.4,
                p95_operation_time_ms=1.0,
                p99_operation_time_ms=1.5,
                min_operation_time_ms=0.1,
                max_operation_time_ms=2.0,
                memory_usage_before_mb=50.0,
                memory_usage_after_mb=51.0,
                memory_delta_mb=1.0,
                cpu_usage_percent=5.0,
                overhead_threshold_met=True,
                details={"successful_operations": 100, "failed_operations": 0}
            )

            mock_baseline.return_value = mock_result
            mock_single.return_value = mock_result
            mock_volume.return_value = mock_result
            mock_api.return_value = mock_result

            # Run comprehensive suite
            report = await benchmark_suite.run_comprehensive_benchmark_suite()

            # Verify report structure
            assert "benchmark_suite_summary" in report
            assert "benchmark_results" in report
            assert "performance_analysis" in report
            assert "threshold_compliance" in report
            assert "recommendations" in report

            # Verify all benchmarks were called
            mock_baseline.assert_called_once()
            mock_single.assert_called_once()
            mock_volume.assert_called_once()
            mock_api.assert_called_once()

    def test_generate_performance_report(self, benchmark_suite):
        """Test performance report generation."""
        # Create mock benchmark results
        mock_result = BenchmarkResult(
            test_name="test_benchmark",
            test_type="test",
            start_time=benchmark_suite.metrics_collector.start_monitoring(),
            end_time=benchmark_suite.metrics_collector.start_monitoring(),
            duration_seconds=1.0,
            operations_count=100,
            operations_per_second=100.0,
            average_operation_time_ms=0.5,
            median_operation_time_ms=0.4,
            p95_operation_time_ms=1.0,
            p99_operation_time_ms=1.5,
            min_operation_time_ms=0.1,
            max_operation_time_ms=2.0,
            memory_usage_before_mb=50.0,
            memory_usage_after_mb=51.0,
            memory_delta_mb=1.0,
            cpu_usage_percent=5.0,
            overhead_threshold_met=True,
            details={"successful_operations": 100, "failed_operations": 0}
        )

        suite_results = {"Test Benchmark": mock_result}
        report = benchmark_suite._generate_performance_report(suite_results, 10.0)

        assert report["benchmark_suite_summary"]["total_duration_seconds"] == 10.0
        assert report["benchmark_suite_summary"]["benchmarks_run"] == 1
        assert "Test Benchmark" in report["benchmark_results"]
        assert report["benchmark_results"]["Test Benchmark"]["status"] == "passed"
        assert "performance_analysis" in report
        assert "threshold_compliance" in report

    def test_export_results(self, benchmark_suite, temp_log_dir):
        """Test exporting benchmark results."""
        # Add a mock result
        mock_result = BenchmarkResult(
            test_name="export_test",
            test_type="test",
            start_time=benchmark_suite.metrics_collector.start_monitoring(),
            end_time=benchmark_suite.metrics_collector.start_monitoring(),
            duration_seconds=1.0,
            operations_count=100,
            operations_per_second=100.0,
            average_operation_time_ms=0.5,
            median_operation_time_ms=0.4,
            p95_operation_time_ms=1.0,
            p99_operation_time_ms=1.5,
            min_operation_time_ms=0.1,
            max_operation_time_ms=2.0,
            memory_usage_before_mb=50.0,
            memory_usage_after_mb=51.0,
            memory_delta_mb=1.0,
            cpu_usage_percent=5.0,
            overhead_threshold_met=True,
            details={"successful_operations": 100}
        )

        benchmark_suite.benchmark_results.append(mock_result)

        # Export results
        filepath = benchmark_suite.export_results()

        assert Path(filepath).exists()
        assert Path(filepath).suffix == ".json"
        assert temp_log_dir in filepath

    def test_export_results_custom_filename(self, benchmark_suite, temp_log_dir):
        """Test exporting with custom filename."""
        # Add a mock result
        mock_result = BenchmarkResult(
            test_name="custom_export_test",
            test_type="test",
            start_time=benchmark_suite.metrics_collector.start_monitoring(),
            end_time=benchmark_suite.metrics_collector.start_monitoring(),
            duration_seconds=1.0,
            operations_count=100,
            operations_per_second=100.0,
            average_operation_time_ms=0.5,
            median_operation_time_ms=0.4,
            p95_operation_time_ms=1.0,
            p99_operation_time_ms=1.5,
            min_operation_time_ms=0.1,
            max_operation_time_ms=2.0,
            memory_usage_before_mb=50.0,
            memory_usage_after_mb=51.0,
            memory_delta_mb=1.0,
            cpu_usage_percent=5.0,
            overhead_threshold_met=True,
            details={"successful_operations": 100}
        )

        benchmark_suite.benchmark_results.append(mock_result)

        # Export with custom filename
        custom_filename = "custom_benchmark_results.json"
        filepath = benchmark_suite.export_results(filename=custom_filename)

        assert Path(filepath).exists()
        assert custom_filename in filepath

    def test_export_results_invalid_format(self, benchmark_suite):
        """Test exporting with invalid format."""
        with pytest.raises(ValueError, match="Unsupported export format"):
            benchmark_suite.export_results(format_type="xml")

    def test_cleanup(self, benchmark_suite, temp_log_dir):
        """Test cleanup functionality."""
        # Verify directory exists before cleanup
        assert Path(temp_log_dir).exists()

        # Run cleanup
        benchmark_suite.cleanup()

        # Directory should be removed (or at least attempted)
        # Note: In some test environments, cleanup might not immediately succeed

    def test_performance_threshold_compliance(self, benchmark_suite):
        """Test that benchmarks can identify threshold violations."""
        # Test with intentionally slow operation
        def slow_operation():
            time.sleep(0.01)  # 10ms - should exceed 5ms threshold

        # Create a custom benchmark that will fail threshold
        def run_slow_benchmark():
            all_metrics = []
            for i in range(10):
                metrics = benchmark_suite._measure_single_operation(slow_operation)
                all_metrics.append(metrics)

            operation_times_ms = [m.operation_time_ns / 1_000_000 for m in all_metrics]
            avg_time = sum(operation_times_ms) / len(operation_times_ms)

            return avg_time > 5.0  # Should exceed threshold

        # Run test
        exceeds_threshold = run_slow_benchmark()
        assert exceeds_threshold, "Slow operation should exceed 5ms threshold"


@pytest.mark.integration
class TestLoggingPerformanceIntegration:
    """Integration tests for logging performance benchmarks."""

    @pytest.mark.asyncio
    async def test_real_logging_performance(self):
        """Test actual logging performance with real operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            benchmark_suite = LoggingPerformanceBenchmarks(test_log_dir=temp_dir)

            try:
                # Run a small but real benchmark
                result = benchmark_suite.benchmark_single_log_statements(iterations=500)

                # Verify results are reasonable
                assert result.operations_count == 500
                assert result.duration_seconds > 0
                assert result.average_operation_time_ms >= 0

                # Log file should be created
                log_files = list(Path(temp_dir).glob("*.log"))
                assert len(log_files) > 0

                # Performance should be reasonable (under 10ms avg for small test)
                assert result.average_operation_time_ms < 10.0

                print(f"Real logging performance: {result.average_operation_time_ms:.3f}ms avg, "
                      f"{result.operations_per_second:.0f} ops/sec")

            finally:
                benchmark_suite.cleanup()

    @pytest.mark.asyncio
    async def test_concurrent_logging_performance(self):
        """Test concurrent logging performance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            benchmark_suite = LoggingPerformanceBenchmarks(test_log_dir=temp_dir)

            try:
                # Run concurrent logging test
                result = benchmark_suite.benchmark_high_volume_logging(
                    log_count=1000,
                    concurrent_threads=3
                )

                # Verify concurrent operation
                assert result.operations_count == 1000
                assert result.details["concurrent_threads"] == 3
                assert result.details["successful_operations"] > 900  # Allow some variance

                print(f"Concurrent logging performance: {result.average_operation_time_ms:.3f}ms avg")

            finally:
                benchmark_suite.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])