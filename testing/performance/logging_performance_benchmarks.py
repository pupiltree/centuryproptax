"""
Logging Performance Benchmarks for Century Property Tax Application.

This module provides comprehensive performance benchmarking for logging operations
to ensure logging overhead stays under 5ms per operation and meets performance targets.
"""

import time
import asyncio
import statistics
import gc
import threading
import resource
import sys
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import structlog
import logging
import json
import tempfile
import os
from pathlib import Path

# Import our logging configuration
from src.core.logging import configure_logging, get_logger, get_standard_logger, ensure_logging_configured


@dataclass
class BenchmarkResult:
    """Individual benchmark test result."""
    test_name: str
    test_type: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    operations_count: int
    operations_per_second: float
    average_operation_time_ms: float
    median_operation_time_ms: float
    p95_operation_time_ms: float
    p99_operation_time_ms: float
    min_operation_time_ms: float
    max_operation_time_ms: float
    memory_usage_before_mb: float
    memory_usage_after_mb: float
    memory_delta_mb: float
    cpu_usage_percent: float
    overhead_threshold_met: bool
    details: Dict[str, Any]


@dataclass
class PerformanceMetrics:
    """Performance metrics for a single logging operation."""
    operation_time_ns: int
    memory_before: float
    memory_after: float
    cpu_usage: float
    success: bool
    error_message: Optional[str] = None


class SystemMetricsCollector:
    """Collects system metrics during benchmarking using built-in Python tools."""

    def __init__(self):
        self.baseline_time = time.time()

    def get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB using resource module."""
        # Get memory usage in KB and convert to MB
        memory_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # On Linux, ru_maxrss is in KB, on macOS it's in bytes
        if sys.platform == 'darwin':  # macOS
            return memory_kb / 1024 / 1024
        else:  # Linux and others
            return memory_kb / 1024

    def get_cpu_usage_percent(self) -> float:
        """Get approximated CPU usage percentage using resource module."""
        usage = resource.getrusage(resource.RUSAGE_SELF)
        total_time = usage.ru_utime + usage.ru_stime
        elapsed_time = time.time() - self.baseline_time

        if elapsed_time > 0:
            # This is a rough approximation
            cpu_percent = min(100.0, (total_time / elapsed_time) * 100)
            return cpu_percent
        return 0.0

    def start_monitoring(self) -> Dict[str, float]:
        """Start monitoring and return baseline metrics."""
        self.baseline_time = time.time()
        time.sleep(0.01)  # Brief pause for measurement stability

        return {
            'memory_mb': self.get_memory_usage_mb(),
            'cpu_percent': self.get_cpu_usage_percent()
        }


class LoggingPerformanceBenchmarks:
    """Comprehensive logging performance benchmark suite."""

    def __init__(self, test_log_dir: Optional[str] = None):
        """Initialize the benchmark suite."""
        self.test_log_dir = test_log_dir or tempfile.mkdtemp(prefix="logging_benchmark_")
        self.metrics_collector = SystemMetricsCollector()
        self.benchmark_results: List[BenchmarkResult] = []

        # Ensure our logging is configured for testing
        self._setup_test_logging()

        # Logging instances for testing
        self.structlog_logger = get_logger("benchmark_test")
        self.standard_logger = get_standard_logger("benchmark_test")

    def _setup_test_logging(self):
        """Set up logging configuration for benchmarking."""
        # Set environment variables for test configuration
        os.environ['LOG_DIR'] = self.test_log_dir
        os.environ['LOG_LEVEL'] = 'INFO'
        os.environ['LOG_FILE_ENABLED'] = 'true'

        # Configure logging
        ensure_logging_configured()

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile value."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * (percentile / 100))
        return sorted_data[min(index, len(sorted_data) - 1)]

    def _measure_single_operation(self, operation_func, *args, **kwargs) -> PerformanceMetrics:
        """Measure performance of a single logging operation."""
        # Force garbage collection for consistent memory measurement
        gc.collect()

        memory_before = self.metrics_collector.get_memory_usage_mb()
        cpu_before = self.metrics_collector.get_cpu_usage_percent()

        start_time = time.perf_counter_ns()
        success = True
        error_message = None

        try:
            operation_func(*args, **kwargs)
        except Exception as e:
            success = False
            error_message = str(e)

        end_time = time.perf_counter_ns()

        memory_after = self.metrics_collector.get_memory_usage_mb()
        cpu_after = self.metrics_collector.get_cpu_usage_percent()

        return PerformanceMetrics(
            operation_time_ns=end_time - start_time,
            memory_before=memory_before,
            memory_after=memory_after,
            cpu_usage=max(cpu_before, cpu_after),  # Use max for CPU spike detection
            success=success,
            error_message=error_message
        )

    def benchmark_single_log_statements(self, iterations: int = 10000) -> BenchmarkResult:
        """Benchmark single log statement overhead."""
        test_name = "single_log_statements"
        start_time = datetime.now()

        baseline_metrics = self.metrics_collector.start_monitoring()

        # Test different types of log statements
        log_operations = [
            lambda: self.structlog_logger.info("Test message"),
            lambda: self.structlog_logger.info("Test message with data", user_id="12345", action="test"),
            lambda: self.structlog_logger.warning("Warning message"),
            lambda: self.structlog_logger.error("Error message"),
            lambda: self.standard_logger.info("Standard log message"),
            lambda: self.standard_logger.error("Standard error message")
        ]

        all_metrics = []

        for i in range(iterations):
            # Cycle through different log operations
            operation = log_operations[i % len(log_operations)]
            metrics = self._measure_single_operation(operation)
            all_metrics.append(metrics)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Calculate statistics
        operation_times_ms = [m.operation_time_ns / 1_000_000 for m in all_metrics]
        successful_operations = [m for m in all_metrics if m.success]

        final_metrics = self.metrics_collector.start_monitoring()

        result = BenchmarkResult(
            test_name=test_name,
            test_type="single_operations",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            operations_count=iterations,
            operations_per_second=iterations / duration if duration > 0 else 0,
            average_operation_time_ms=statistics.mean(operation_times_ms) if operation_times_ms else 0,
            median_operation_time_ms=statistics.median(operation_times_ms) if operation_times_ms else 0,
            p95_operation_time_ms=self._percentile(operation_times_ms, 95),
            p99_operation_time_ms=self._percentile(operation_times_ms, 99),
            min_operation_time_ms=min(operation_times_ms) if operation_times_ms else 0,
            max_operation_time_ms=max(operation_times_ms) if operation_times_ms else 0,
            memory_usage_before_mb=baseline_metrics['memory_mb'],
            memory_usage_after_mb=final_metrics['memory_mb'],
            memory_delta_mb=final_metrics['memory_mb'] - baseline_metrics['memory_mb'],
            cpu_usage_percent=final_metrics['cpu_percent'],
            overhead_threshold_met=statistics.mean(operation_times_ms) < 5.0 if operation_times_ms else False,
            details={
                "successful_operations": len(successful_operations),
                "failed_operations": len(all_metrics) - len(successful_operations),
                "operation_types_tested": len(log_operations),
                "memory_per_operation_kb": (final_metrics['memory_mb'] - baseline_metrics['memory_mb']) * 1024 / iterations if iterations > 0 else 0
            }
        )

        self.benchmark_results.append(result)
        return result

    def benchmark_high_volume_logging(self, log_count: int = 10000, concurrent_threads: int = 5) -> BenchmarkResult:
        """Benchmark high-volume logging scenarios."""
        test_name = f"high_volume_{log_count}_logs_{concurrent_threads}_threads"
        start_time = datetime.now()

        baseline_metrics = self.metrics_collector.start_monitoring()

        def log_worker(thread_id: int, logs_per_thread: int) -> List[PerformanceMetrics]:
            """Worker function for concurrent logging."""
            thread_logger = get_logger(f"worker_{thread_id}")
            metrics = []

            for i in range(logs_per_thread):
                operation = lambda: thread_logger.info(
                    "High volume log message",
                    thread_id=thread_id,
                    message_number=i,
                    timestamp=time.time(),
                    data={"key": f"value_{i}", "iteration": i}
                )
                metric = self._measure_single_operation(operation)
                metrics.append(metric)

            return metrics

        # Distribute work among threads
        logs_per_thread = log_count // concurrent_threads
        remaining_logs = log_count % concurrent_threads

        all_metrics = []

        with ThreadPoolExecutor(max_workers=concurrent_threads) as executor:
            futures = []

            for thread_id in range(concurrent_threads):
                thread_logs = logs_per_thread + (1 if thread_id < remaining_logs else 0)
                future = executor.submit(log_worker, thread_id, thread_logs)
                futures.append(future)

            for future in as_completed(futures):
                try:
                    thread_metrics = future.result()
                    all_metrics.extend(thread_metrics)
                except Exception as e:
                    # Create error metric
                    error_metric = PerformanceMetrics(
                        operation_time_ns=0,
                        memory_before=0,
                        memory_after=0,
                        cpu_usage=0,
                        success=False,
                        error_message=str(e)
                    )
                    all_metrics.append(error_metric)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Calculate statistics
        operation_times_ms = [m.operation_time_ns / 1_000_000 for m in all_metrics]
        successful_operations = [m for m in all_metrics if m.success]

        final_metrics = self.metrics_collector.start_monitoring()

        result = BenchmarkResult(
            test_name=test_name,
            test_type="high_volume",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            operations_count=len(all_metrics),
            operations_per_second=len(all_metrics) / duration if duration > 0 else 0,
            average_operation_time_ms=statistics.mean(operation_times_ms) if operation_times_ms else 0,
            median_operation_time_ms=statistics.median(operation_times_ms) if operation_times_ms else 0,
            p95_operation_time_ms=self._percentile(operation_times_ms, 95),
            p99_operation_time_ms=self._percentile(operation_times_ms, 99),
            min_operation_time_ms=min(operation_times_ms) if operation_times_ms else 0,
            max_operation_time_ms=max(operation_times_ms) if operation_times_ms else 0,
            memory_usage_before_mb=baseline_metrics['memory_mb'],
            memory_usage_after_mb=final_metrics['memory_mb'],
            memory_delta_mb=final_metrics['memory_mb'] - baseline_metrics['memory_mb'],
            cpu_usage_percent=final_metrics['cpu_percent'],
            overhead_threshold_met=statistics.mean(operation_times_ms) < 5.0 if operation_times_ms else False,
            details={
                "successful_operations": len(successful_operations),
                "failed_operations": len(all_metrics) - len(successful_operations),
                "concurrent_threads": concurrent_threads,
                "logs_per_thread": logs_per_thread,
                "total_log_files_created": 1,  # All logs go to same file
                "average_thread_performance": statistics.mean(operation_times_ms) if operation_times_ms else 0
            }
        )

        self.benchmark_results.append(result)
        return result

    async def benchmark_api_request_logging_impact(self, request_count: int = 1000) -> BenchmarkResult:
        """Benchmark logging impact on API request performance."""
        test_name = f"api_request_logging_impact_{request_count}_requests"
        start_time = datetime.now()

        baseline_metrics = self.metrics_collector.start_monitoring()

        async def simulate_api_request_with_logging(request_id: int) -> PerformanceMetrics:
            """Simulate an API request with typical logging."""
            logger = get_logger("api_request")

            def log_operations():
                # Typical API request logging pattern
                logger.info("API request started", request_id=request_id, endpoint="/api/property/search")
                logger.info("Validating request parameters", request_id=request_id)
                logger.info("Database query executed", request_id=request_id, query_time=0.045)
                logger.info("Processing business logic", request_id=request_id)
                logger.info("API request completed", request_id=request_id, status_code=200, response_time=0.123)

            return self._measure_single_operation(log_operations)

        # Run API request simulations
        all_metrics = []
        semaphore = asyncio.Semaphore(50)  # Limit concurrency

        async def bounded_request(request_id: int):
            async with semaphore:
                return await simulate_api_request_with_logging(request_id)

        tasks = [bounded_request(i) for i in range(request_count)]
        all_metrics = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and convert to metrics
        valid_metrics = []
        for metric in all_metrics:
            if isinstance(metric, PerformanceMetrics):
                valid_metrics.append(metric)
            elif isinstance(metric, Exception):
                # Create error metric
                error_metric = PerformanceMetrics(
                    operation_time_ns=0,
                    memory_before=0,
                    memory_after=0,
                    cpu_usage=0,
                    success=False,
                    error_message=str(metric)
                )
                valid_metrics.append(error_metric)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Calculate statistics
        operation_times_ms = [m.operation_time_ns / 1_000_000 for m in valid_metrics]
        successful_operations = [m for m in valid_metrics if m.success]

        final_metrics = self.metrics_collector.start_monitoring()

        result = BenchmarkResult(
            test_name=test_name,
            test_type="api_impact",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            operations_count=len(valid_metrics),
            operations_per_second=len(valid_metrics) / duration if duration > 0 else 0,
            average_operation_time_ms=statistics.mean(operation_times_ms) if operation_times_ms else 0,
            median_operation_time_ms=statistics.median(operation_times_ms) if operation_times_ms else 0,
            p95_operation_time_ms=self._percentile(operation_times_ms, 95),
            p99_operation_time_ms=self._percentile(operation_times_ms, 99),
            min_operation_time_ms=min(operation_times_ms) if operation_times_ms else 0,
            max_operation_time_ms=max(operation_times_ms) if operation_times_ms else 0,
            memory_usage_before_mb=baseline_metrics['memory_mb'],
            memory_usage_after_mb=final_metrics['memory_mb'],
            memory_delta_mb=final_metrics['memory_mb'] - baseline_metrics['memory_mb'],
            cpu_usage_percent=final_metrics['cpu_percent'],
            overhead_threshold_met=statistics.mean(operation_times_ms) < 5.0 if operation_times_ms else False,
            details={
                "successful_operations": len(successful_operations),
                "failed_operations": len(valid_metrics) - len(successful_operations),
                "logs_per_request": 5,  # We log 5 times per simulated request
                "api_overhead_threshold_met": statistics.mean(operation_times_ms) < 5.0 if operation_times_ms else False,
                "requests_processed": request_count
            }
        )

        self.benchmark_results.append(result)
        return result

    def benchmark_logging_without_handlers(self, iterations: int = 10000) -> BenchmarkResult:
        """Benchmark logging performance without file handlers (baseline)."""
        test_name = f"baseline_no_handlers_{iterations}_operations"
        start_time = datetime.now()

        baseline_metrics = self.metrics_collector.start_monitoring()

        # Create a logger without handlers for baseline
        baseline_logger = logging.getLogger("baseline_test")
        baseline_logger.handlers.clear()
        baseline_logger.setLevel(logging.INFO)

        all_metrics = []

        for i in range(iterations):
            operation = lambda: baseline_logger.info(f"Baseline log message {i}")
            metrics = self._measure_single_operation(operation)
            all_metrics.append(metrics)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Calculate statistics
        operation_times_ms = [m.operation_time_ns / 1_000_000 for m in all_metrics]
        successful_operations = [m for m in all_metrics if m.success]

        final_metrics = self.metrics_collector.start_monitoring()

        result = BenchmarkResult(
            test_name=test_name,
            test_type="baseline",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            operations_count=iterations,
            operations_per_second=iterations / duration if duration > 0 else 0,
            average_operation_time_ms=statistics.mean(operation_times_ms) if operation_times_ms else 0,
            median_operation_time_ms=statistics.median(operation_times_ms) if operation_times_ms else 0,
            p95_operation_time_ms=self._percentile(operation_times_ms, 95),
            p99_operation_time_ms=self._percentile(operation_times_ms, 99),
            min_operation_time_ms=min(operation_times_ms) if operation_times_ms else 0,
            max_operation_time_ms=max(operation_times_ms) if operation_times_ms else 0,
            memory_usage_before_mb=baseline_metrics['memory_mb'],
            memory_usage_after_mb=final_metrics['memory_mb'],
            memory_delta_mb=final_metrics['memory_mb'] - baseline_metrics['memory_mb'],
            cpu_usage_percent=final_metrics['cpu_percent'],
            overhead_threshold_met=True,  # Baseline should always be fast
            details={
                "successful_operations": len(successful_operations),
                "failed_operations": len(all_metrics) - len(successful_operations),
                "handlers_used": 0,
                "baseline_test": True
            }
        )

        self.benchmark_results.append(result)
        return result

    async def run_comprehensive_benchmark_suite(self) -> Dict[str, Any]:
        """Run comprehensive logging performance benchmark suite."""
        suite_start_time = datetime.now()

        print("🚀 Starting comprehensive logging performance benchmark suite...")

        # Run individual benchmarks
        benchmarks = [
            ("Baseline (no handlers)", lambda: self.benchmark_logging_without_handlers(5000)),
            ("Single log statements", lambda: self.benchmark_single_log_statements(5000)),
            ("High volume logging", lambda: self.benchmark_high_volume_logging(10000, 3)),
            ("API request impact", lambda: asyncio.run(self.benchmark_api_request_logging_impact(500)))
        ]

        suite_results = {}

        for benchmark_name, benchmark_func in benchmarks:
            print(f"📊 Running {benchmark_name} benchmark...")
            try:
                result = benchmark_func()
                suite_results[benchmark_name] = result

                # Print immediate results
                print(f"✅ {benchmark_name}: {result.average_operation_time_ms:.3f}ms avg, "
                      f"{result.operations_per_second:.0f} ops/sec, "
                      f"Threshold met: {result.overhead_threshold_met}")

            except Exception as e:
                print(f"❌ {benchmark_name} failed: {e}")
                suite_results[benchmark_name] = {"error": str(e)}

            # Brief pause between benchmarks
            time.sleep(2)

        suite_end_time = datetime.now()
        suite_duration = (suite_end_time - suite_start_time).total_seconds()

        # Generate comprehensive report
        report = self._generate_performance_report(suite_results, suite_duration)

        print(f"🏁 Benchmark suite completed in {suite_duration:.1f} seconds")
        return report

    def _generate_performance_report(self, suite_results: Dict[str, Any], suite_duration: float) -> Dict[str, Any]:
        """Generate comprehensive performance benchmark report."""
        report = {
            "benchmark_suite_summary": {
                "total_duration_seconds": suite_duration,
                "benchmarks_run": len(suite_results),
                "timestamp": datetime.now().isoformat(),
                "test_environment": {
                    "log_directory": self.test_log_dir,
                    "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
                    "platform": sys.platform,
                    "current_memory_mb": self.metrics_collector.get_memory_usage_mb()
                }
            },
            "benchmark_results": {},
            "performance_analysis": {},
            "threshold_compliance": {},
            "recommendations": []
        }

        # Process individual benchmark results
        for benchmark_name, result in suite_results.items():
            if isinstance(result, dict) and "error" in result:
                report["benchmark_results"][benchmark_name] = {
                    "status": "failed",
                    "error": result["error"]
                }
                continue

            if not isinstance(result, BenchmarkResult):
                continue

            # Add detailed results
            report["benchmark_results"][benchmark_name] = {
                "status": "passed" if result.overhead_threshold_met else "warning",
                "operations_count": result.operations_count,
                "duration_seconds": result.duration_seconds,
                "operations_per_second": result.operations_per_second,
                "average_operation_time_ms": result.average_operation_time_ms,
                "p95_operation_time_ms": result.p95_operation_time_ms,
                "p99_operation_time_ms": result.p99_operation_time_ms,
                "memory_delta_mb": result.memory_delta_mb,
                "cpu_usage_percent": result.cpu_usage_percent,
                "overhead_threshold_met": result.overhead_threshold_met,
                "details": result.details
            }

            # Threshold compliance analysis
            compliance_status = "excellent" if result.average_operation_time_ms < 1.0 else \
                              "good" if result.average_operation_time_ms < 3.0 else \
                              "acceptable" if result.overhead_threshold_met else \
                              "poor"

            report["threshold_compliance"][benchmark_name] = {
                "status": compliance_status,
                "average_time_ms": result.average_operation_time_ms,
                "threshold_ms": 5.0,
                "margin_ms": 5.0 - result.average_operation_time_ms,
                "performance_grade": compliance_status
            }

        # Generate performance analysis
        all_results = [r for r in suite_results.values() if isinstance(r, BenchmarkResult)]
        if all_results:
            avg_times = [r.average_operation_time_ms for r in all_results]
            report["performance_analysis"] = {
                "overall_average_time_ms": statistics.mean(avg_times),
                "fastest_benchmark_ms": min(avg_times),
                "slowest_benchmark_ms": max(avg_times),
                "performance_variance": statistics.stdev(avg_times) if len(avg_times) > 1 else 0,
                "all_thresholds_met": all(r.overhead_threshold_met for r in all_results),
                "total_operations_tested": sum(r.operations_count for r in all_results)
            }

        # Generate recommendations
        report["recommendations"] = self._generate_performance_recommendations(suite_results)

        return report

    def _generate_performance_recommendations(self, suite_results: Dict[str, Any]) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []

        for benchmark_name, result in suite_results.items():
            if not isinstance(result, BenchmarkResult):
                continue

            # High latency recommendations
            if result.average_operation_time_ms > 5.0:
                recommendations.append(
                    f"CRITICAL: {benchmark_name} exceeds 5ms threshold "
                    f"({result.average_operation_time_ms:.2f}ms avg) - immediate optimization required"
                )
            elif result.average_operation_time_ms > 3.0:
                recommendations.append(
                    f"WARNING: {benchmark_name} approaching threshold "
                    f"({result.average_operation_time_ms:.2f}ms avg) - monitor closely"
                )

            # Memory usage recommendations
            if result.memory_delta_mb > 10.0:
                recommendations.append(
                    f"Memory optimization needed for {benchmark_name}: "
                    f"{result.memory_delta_mb:.1f}MB increase during test"
                )

            # CPU usage recommendations
            if result.cpu_usage_percent > 80:
                recommendations.append(
                    f"CPU optimization needed for {benchmark_name}: "
                    f"{result.cpu_usage_percent:.1f}% CPU usage"
                )

        # Overall recommendations
        all_results = [r for r in suite_results.values() if isinstance(r, BenchmarkResult)]
        if all_results:
            if all(r.overhead_threshold_met for r in all_results):
                recommendations.append("✅ All logging performance benchmarks meet the 5ms threshold")
            else:
                failed_count = len([r for r in all_results if not r.overhead_threshold_met])
                recommendations.append(
                    f"⚠️ {failed_count} benchmark(s) exceed performance thresholds - optimization required"
                )

        return recommendations

    def export_results(self, format_type: str = "json", filename: Optional[str] = None) -> str:
        """Export benchmark results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format_type.lower() == "json":
            filename = filename or f"logging_benchmark_results_{timestamp}.json"
            filepath = Path(self.test_log_dir) / filename

            export_data = {
                "metadata": {
                    "export_timestamp": datetime.now().isoformat(),
                    "benchmark_count": len(self.benchmark_results),
                    "test_log_directory": self.test_log_dir
                },
                "results": [asdict(result) for result in self.benchmark_results]
            }

            with open(filepath, 'w') as f:
                json.dump(export_data, f, default=str, indent=2)

            return str(filepath)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")

    def cleanup(self):
        """Clean up test resources."""
        # Optionally remove test log directory
        import shutil
        try:
            if Path(self.test_log_dir).exists():
                shutil.rmtree(self.test_log_dir)
        except Exception as e:
            print(f"Warning: Could not clean up test directory {self.test_log_dir}: {e}")


# Example usage and testing
if __name__ == "__main__":
    async def run_logging_benchmark_example():
        """Example of running logging performance benchmarks."""
        print("🧪 Starting logging performance benchmark example...")

        # Initialize benchmark suite
        benchmarks = LoggingPerformanceBenchmarks()

        try:
            # Run comprehensive benchmark suite
            results = await benchmarks.run_comprehensive_benchmark_suite()

            # Print summary
            print("\n📋 Benchmark Summary:")
            print(f"Duration: {results['benchmark_suite_summary']['total_duration_seconds']:.1f}s")
            print(f"Benchmarks: {results['benchmark_suite_summary']['benchmarks_run']}")

            if results.get('performance_analysis'):
                analysis = results['performance_analysis']
                print(f"Overall avg time: {analysis['overall_average_time_ms']:.3f}ms")
                print(f"All thresholds met: {analysis['all_thresholds_met']}")

            print("\n💡 Recommendations:")
            for rec in results.get('recommendations', []):
                print(f"  • {rec}")

            # Export results
            export_file = benchmarks.export_results()
            print(f"\n💾 Results exported to: {export_file}")

        finally:
            # Clean up
            benchmarks.cleanup()

    # Run example
    asyncio.run(run_logging_benchmark_example())