"""
Logging Performance Monitoring and Comparison Utilities.

This module provides tools for ongoing monitoring of logging performance
and comparison between different configurations or implementations.
"""

import time
import json
import statistics
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import tempfile

# Add paths for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # Add project root

from logging_performance_benchmarks import (
    LoggingPerformanceBenchmarks,
    BenchmarkResult
)


@dataclass
class PerformanceBaseline:
    """Baseline performance metrics for comparison."""
    test_name: str
    baseline_date: datetime
    average_operation_time_ms: float
    p95_operation_time_ms: float
    p99_operation_time_ms: float
    operations_per_second: float
    memory_usage_mb: float
    success_rate_percent: float
    configuration: Dict[str, Any]


@dataclass
class PerformanceComparison:
    """Comparison between current performance and baseline."""
    test_name: str
    current_result: BenchmarkResult
    baseline: PerformanceBaseline
    comparison_date: datetime
    time_change_ms: float
    time_change_percent: float
    throughput_change_percent: float
    memory_change_mb: float
    performance_status: str  # "improved", "stable", "degraded"
    exceeds_threshold: bool
    recommendations: List[str]


class LoggingPerformanceMonitor:
    """Monitor and track logging performance over time."""

    def __init__(self, baseline_file: Optional[str] = None):
        """Initialize performance monitor."""
        self.baseline_file = baseline_file or "logging_performance_baselines.json"
        self.baselines: Dict[str, PerformanceBaseline] = {}
        self.load_baselines()

    def load_baselines(self):
        """Load performance baselines from file."""
        try:
            if Path(self.baseline_file).exists():
                with open(self.baseline_file, 'r') as f:
                    baseline_data = json.load(f)

                for test_name, data in baseline_data.items():
                    self.baselines[test_name] = PerformanceBaseline(
                        test_name=data['test_name'],
                        baseline_date=datetime.fromisoformat(data['baseline_date']),
                        average_operation_time_ms=data['average_operation_time_ms'],
                        p95_operation_time_ms=data['p95_operation_time_ms'],
                        p99_operation_time_ms=data['p99_operation_time_ms'],
                        operations_per_second=data['operations_per_second'],
                        memory_usage_mb=data['memory_usage_mb'],
                        success_rate_percent=data['success_rate_percent'],
                        configuration=data.get('configuration', {})
                    )
        except Exception as e:
            print(f"Warning: Could not load baselines: {e}")

    def save_baselines(self):
        """Save performance baselines to file."""
        baseline_data = {}
        for test_name, baseline in self.baselines.items():
            baseline_data[test_name] = asdict(baseline)
            # Convert datetime to string for JSON serialization
            baseline_data[test_name]['baseline_date'] = baseline.baseline_date.isoformat()

        with open(self.baseline_file, 'w') as f:
            json.dump(baseline_data, f, indent=2)

    def establish_baseline(self, test_name: str, result: BenchmarkResult,
                          configuration: Optional[Dict[str, Any]] = None):
        """Establish a performance baseline for a test."""
        success_rate = (result.details.get('successful_operations', 0) /
                       result.operations_count * 100) if result.operations_count > 0 else 0

        baseline = PerformanceBaseline(
            test_name=test_name,
            baseline_date=datetime.now(),
            average_operation_time_ms=result.average_operation_time_ms,
            p95_operation_time_ms=result.p95_operation_time_ms,
            p99_operation_time_ms=result.p99_operation_time_ms,
            operations_per_second=result.operations_per_second,
            memory_usage_mb=result.memory_delta_mb,
            success_rate_percent=success_rate,
            configuration=configuration or {}
        )

        self.baselines[test_name] = baseline
        self.save_baselines()

        print(f"✅ Baseline established for '{test_name}':")
        print(f"   Average time: {baseline.average_operation_time_ms:.3f}ms")
        print(f"   P95 time: {baseline.p95_operation_time_ms:.3f}ms")
        print(f"   Throughput: {baseline.operations_per_second:.0f} ops/sec")

    def compare_with_baseline(self, test_name: str, current_result: BenchmarkResult) -> PerformanceComparison:
        """Compare current performance with established baseline."""
        if test_name not in self.baselines:
            raise ValueError(f"No baseline found for test '{test_name}'")

        baseline = self.baselines[test_name]

        # Calculate changes
        time_change_ms = current_result.average_operation_time_ms - baseline.average_operation_time_ms
        time_change_percent = (time_change_ms / baseline.average_operation_time_ms * 100) if baseline.average_operation_time_ms > 0 else 0

        throughput_change_percent = ((current_result.operations_per_second - baseline.operations_per_second) /
                                   baseline.operations_per_second * 100) if baseline.operations_per_second > 0 else 0

        memory_change_mb = current_result.memory_delta_mb - baseline.memory_usage_mb

        # Determine performance status
        if abs(time_change_percent) < 5:
            performance_status = "stable"
        elif time_change_percent < 0:
            performance_status = "improved"
        else:
            performance_status = "degraded"

        # Generate recommendations
        recommendations = []
        if time_change_percent > 20:
            recommendations.append("CRITICAL: Performance degraded by >20% - immediate investigation required")
        elif time_change_percent > 10:
            recommendations.append("WARNING: Performance degraded by >10% - optimization recommended")
        elif time_change_percent < -10:
            recommendations.append("EXCELLENT: Performance improved by >10%")

        if current_result.average_operation_time_ms > 5.0:
            recommendations.append("THRESHOLD VIOLATION: Logging overhead exceeds 5ms target")

        if memory_change_mb > 5.0:
            recommendations.append(f"Memory usage increased by {memory_change_mb:.1f}MB")

        return PerformanceComparison(
            test_name=test_name,
            current_result=current_result,
            baseline=baseline,
            comparison_date=datetime.now(),
            time_change_ms=time_change_ms,
            time_change_percent=time_change_percent,
            throughput_change_percent=throughput_change_percent,
            memory_change_mb=memory_change_mb,
            performance_status=performance_status,
            exceeds_threshold=current_result.average_operation_time_ms > 5.0,
            recommendations=recommendations
        )

    def run_performance_regression_check(self) -> Dict[str, Any]:
        """Run performance regression check against all baselines."""
        print("🔍 Running performance regression check...")

        # Create temporary benchmark suite with quiet logging
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up quiet logging for benchmarks
            import os
            os.environ['LOG_LEVEL'] = 'WARNING'  # Reduce log verbosity

            benchmarks = LoggingPerformanceBenchmarks(test_log_dir=temp_dir)

            regression_results = {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "passed",
                "tests_run": 0,
                "tests_passed": 0,
                "tests_failed": 0,
                "comparisons": {}
            }

            try:
                # Run lightweight versions of key benchmarks
                test_configs = [
                    ("single_log_statements", lambda: benchmarks.benchmark_single_log_statements(iterations=500)),
                    ("high_volume_logging", lambda: benchmarks.benchmark_high_volume_logging(log_count=1000, concurrent_threads=2)),
                ]

                for test_name, test_func in test_configs:
                    if test_name in self.baselines:
                        try:
                            print(f"  📊 Running {test_name}...")
                            result = test_func()
                            comparison = self.compare_with_baseline(test_name, result)

                            regression_results["tests_run"] += 1
                            regression_results["comparisons"][test_name] = {
                                "status": comparison.performance_status,
                                "time_change_percent": comparison.time_change_percent,
                                "exceeds_threshold": comparison.exceeds_threshold,
                                "recommendations": comparison.recommendations
                            }

                            if comparison.performance_status != "degraded" and not comparison.exceeds_threshold:
                                regression_results["tests_passed"] += 1
                                print(f"    ✅ {test_name}: {comparison.performance_status}")
                            else:
                                regression_results["tests_failed"] += 1
                                print(f"    ❌ {test_name}: {comparison.performance_status}")

                        except Exception as e:
                            print(f"    ⚠️  {test_name}: Failed - {e}")
                            regression_results["tests_failed"] += 1

            finally:
                benchmarks.cleanup()

            # Determine overall status
            if regression_results["tests_failed"] > 0:
                regression_results["overall_status"] = "failed"

            print(f"\n📋 Regression check complete:")
            print(f"   Status: {regression_results['overall_status']}")
            print(f"   Tests: {regression_results['tests_passed']}/{regression_results['tests_run']} passed")

            return regression_results

    def generate_performance_trend_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate performance trend report (placeholder for future implementation)."""
        # This would integrate with a time-series database or log files
        # to track performance trends over time
        return {
            "report_type": "performance_trends",
            "period_days": days,
            "message": "Trend analysis requires historical data collection - not implemented in this demo"
        }

    def export_monitoring_config(self) -> str:
        """Export monitoring configuration for CI/CD integration."""
        config = {
            "monitoring_config": {
                "baseline_file": self.baseline_file,
                "performance_thresholds": {
                    "max_operation_time_ms": 5.0,
                    "max_degradation_percent": 20.0,
                    "max_memory_increase_mb": 5.0
                },
                "regression_check_frequency": "daily",
                "alert_channels": ["console", "file"]
            },
            "cicd_integration": {
                "pre_commit_hook": "python -m testing.performance.logging_performance_monitor --regression-check",
                "build_pipeline_step": "python scripts/run_logging_performance_benchmarks.py quick",
                "monitoring_schedule": "0 2 * * *"  # Daily at 2 AM
            }
        }

        config_file = "logging_performance_monitoring_config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        return config_file


def compare_before_after_implementations(before_config: Dict[str, Any],
                                       after_config: Dict[str, Any],
                                       test_iterations: int = 1000) -> Dict[str, Any]:
    """Compare logging performance before and after implementation changes."""
    print("🔄 Running before/after performance comparison...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Run "before" configuration
        print("📊 Testing BEFORE configuration...")
        before_benchmarks = LoggingPerformanceBenchmarks(test_log_dir=temp_dir + "/before")

        # Simulate baseline/minimal logging
        before_result = before_benchmarks.benchmark_logging_without_handlers(iterations=test_iterations)

        # Run "after" configuration
        print("📊 Testing AFTER configuration...")
        after_benchmarks = LoggingPerformanceBenchmarks(test_log_dir=temp_dir + "/after")

        # Test with full logging configuration
        after_result = after_benchmarks.benchmark_single_log_statements(iterations=test_iterations)

        # Calculate comparison metrics
        time_change = after_result.average_operation_time_ms - before_result.average_operation_time_ms
        percent_change = (time_change / before_result.average_operation_time_ms) * 100 if before_result.average_operation_time_ms > 0 else 0

        throughput_change = after_result.operations_per_second - before_result.operations_per_second
        throughput_percent_change = (throughput_change / before_result.operations_per_second) * 100 if before_result.operations_per_second > 0 else 0

        memory_change = after_result.memory_delta_mb - before_result.memory_delta_mb

        # Determine impact assessment
        if abs(percent_change) < 5:
            impact_level = "minimal"
        elif abs(percent_change) < 15:
            impact_level = "moderate"
        else:
            impact_level = "significant"

        # Generate recommendations
        recommendations = []
        if after_result.average_operation_time_ms > 5.0:
            recommendations.append("WARNING: Logging implementation exceeds 5ms threshold")
        if percent_change > 25:
            recommendations.append("CRITICAL: Logging overhead increased by >25% - optimization required")
        elif percent_change > 10:
            recommendations.append("Logging overhead increased - consider optimization")
        elif percent_change < -5:
            recommendations.append("EXCELLENT: Logging performance improved")

        if after_result.overhead_threshold_met:
            recommendations.append("✅ Logging implementation meets performance requirements")

        comparison_report = {
            "comparison_summary": {
                "test_iterations": test_iterations,
                "comparison_date": datetime.now().isoformat(),
                "impact_level": impact_level
            },
            "before_performance": {
                "average_time_ms": before_result.average_operation_time_ms,
                "operations_per_second": before_result.operations_per_second,
                "memory_delta_mb": before_result.memory_delta_mb
            },
            "after_performance": {
                "average_time_ms": after_result.average_operation_time_ms,
                "operations_per_second": after_result.operations_per_second,
                "memory_delta_mb": after_result.memory_delta_mb,
                "threshold_met": after_result.overhead_threshold_met
            },
            "performance_changes": {
                "time_change_ms": time_change,
                "time_change_percent": percent_change,
                "throughput_change_ops_sec": throughput_change,
                "throughput_change_percent": throughput_percent_change,
                "memory_change_mb": memory_change
            },
            "recommendations": recommendations
        }

        print(f"\n📋 Before/After Comparison Results:")
        print(f"   Before: {before_result.average_operation_time_ms:.3f}ms")
        print(f"   After:  {after_result.average_operation_time_ms:.3f}ms")
        print(f"   Change: {time_change:+.3f}ms ({percent_change:+.1f}%)")
        print(f"   Impact: {impact_level}")
        print(f"   Threshold met: {after_result.overhead_threshold_met}")

        # Cleanup
        before_benchmarks.cleanup()
        after_benchmarks.cleanup()

        return comparison_report


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--regression-check":
        # CLI integration for regression checking
        monitor = LoggingPerformanceMonitor()
        results = monitor.run_performance_regression_check()

        if results["overall_status"] == "failed":
            print("❌ Performance regression detected!")
            sys.exit(1)
        else:
            print("✅ No performance regression detected")
            sys.exit(0)
    else:
        # Demo usage
        print("🧪 Logging Performance Monitoring Demo")

        monitor = LoggingPerformanceMonitor()

        # Example: Run before/after comparison
        before_config = {"logging_type": "baseline"}
        after_config = {"logging_type": "full_structured"}

        comparison = compare_before_after_implementations(before_config, after_config, test_iterations=500)

        # Export monitoring configuration
        config_file = monitor.export_monitoring_config()
        print(f"\n💾 Monitoring configuration exported to: {config_file}")

        print("\n🎯 Demo completed successfully!")