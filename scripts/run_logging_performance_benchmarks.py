#!/usr/bin/env python3
"""
Script to run logging performance benchmarks for Century Property Tax Application.

This script runs comprehensive logging performance tests and generates reports
to ensure logging overhead meets the <5ms per operation requirement.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from testing.performance.logging_performance_benchmarks import LoggingPerformanceBenchmarks


def print_banner():
    """Print benchmark suite banner."""
    print("=" * 80)
    print("🚀 LOGGING PERFORMANCE BENCHMARK SUITE")
    print("   Century Property Tax Application")
    print("=" * 80)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Target: <5ms logging overhead per operation")
    print("=" * 80)


def print_benchmark_header(name: str, description: str):
    """Print header for individual benchmark."""
    print(f"\n📊 {name}")
    print(f"   {description}")
    print("-" * 60)


def print_benchmark_result(result):
    """Print individual benchmark result."""
    status_emoji = "✅" if result.overhead_threshold_met else "❌"

    print(f"{status_emoji} Results:")
    print(f"   Operations: {result.operations_count:,}")
    print(f"   Duration: {result.duration_seconds:.2f}s")
    print(f"   Ops/sec: {result.operations_per_second:.0f}")
    print(f"   Avg time: {result.average_operation_time_ms:.3f}ms")
    print(f"   P95 time: {result.p95_operation_time_ms:.3f}ms")
    print(f"   P99 time: {result.p99_operation_time_ms:.3f}ms")
    print(f"   Memory Δ: {result.memory_delta_mb:.2f}MB")
    print(f"   Threshold met: {result.overhead_threshold_met}")

    if result.details:
        success_rate = (result.details.get('successful_operations', 0) /
                       result.operations_count * 100) if result.operations_count > 0 else 0
        print(f"   Success rate: {success_rate:.1f}%")


def print_summary_report(report):
    """Print comprehensive summary report."""
    print("\n" + "=" * 80)
    print("📋 COMPREHENSIVE PERFORMANCE REPORT")
    print("=" * 80)

    summary = report['benchmark_suite_summary']
    print(f"⏱️  Total Duration: {summary['total_duration_seconds']:.1f}s")
    print(f"🧪 Benchmarks Run: {summary['benchmarks_run']}")

    if 'performance_analysis' in report:
        analysis = report['performance_analysis']
        print(f"📈 Overall Avg Time: {analysis['overall_average_time_ms']:.3f}ms")
        print(f"🎯 All Thresholds Met: {analysis['all_thresholds_met']}")
        print(f"🔢 Total Operations: {analysis['total_operations_tested']:,}")

    # Print threshold compliance
    print("\n🎯 THRESHOLD COMPLIANCE:")
    for benchmark_name, compliance in report.get('threshold_compliance', {}).items():
        status_emoji = "✅" if compliance['status'] in ['excellent', 'good', 'acceptable'] else "❌"
        print(f"   {status_emoji} {benchmark_name}: {compliance['status']} "
              f"({compliance['average_time_ms']:.3f}ms)")

    # Print recommendations
    print("\n💡 RECOMMENDATIONS:")
    for rec in report.get('recommendations', []):
        if rec.startswith('✅'):
            print(f"   {rec}")
        elif rec.startswith('CRITICAL'):
            print(f"   🚨 {rec}")
        elif rec.startswith('WARNING'):
            print(f"   ⚠️  {rec}")
        else:
            print(f"   • {rec}")


async def run_quick_benchmark():
    """Run a quick benchmark suite for development/testing."""
    print_banner()
    print("🏃 Running Quick Benchmark Suite (reduced iterations for speed)")

    benchmarks = LoggingPerformanceBenchmarks()

    try:
        # Quick baseline test
        print_benchmark_header("Baseline Performance", "Logging without file handlers")
        baseline_result = benchmarks.benchmark_logging_without_handlers(iterations=1000)
        print_benchmark_result(baseline_result)

        # Quick single operations test
        print_benchmark_header("Single Log Operations", "Individual log statement overhead")
        single_result = benchmarks.benchmark_single_log_statements(iterations=1000)
        print_benchmark_result(single_result)

        # Quick high volume test
        print_benchmark_header("High Volume Logging", "Concurrent logging performance")
        volume_result = benchmarks.benchmark_high_volume_logging(log_count=2000, concurrent_threads=2)
        print_benchmark_result(volume_result)

        # Quick API impact test
        print_benchmark_header("API Request Impact", "Logging overhead in API requests")
        api_result = await benchmarks.benchmark_api_request_logging_impact(request_count=200)
        print_benchmark_result(api_result)

        # Generate quick report
        suite_results = {
            "Baseline": baseline_result,
            "Single Operations": single_result,
            "High Volume": volume_result,
            "API Impact": api_result
        }

        report = benchmarks._generate_performance_report(suite_results,
                                                       sum([r.duration_seconds for r in suite_results.values()]))
        print_summary_report(report)

        # Export results
        export_file = benchmarks.export_results(filename="quick_benchmark_results.json")
        print(f"\n💾 Results exported to: {export_file}")

        return report

    finally:
        benchmarks.cleanup()


async def run_comprehensive_benchmark():
    """Run comprehensive benchmark suite with full iterations."""
    print_banner()
    print("🔬 Running Comprehensive Benchmark Suite (full iterations)")

    benchmarks = LoggingPerformanceBenchmarks()

    try:
        # Run comprehensive suite
        report = await benchmarks.run_comprehensive_benchmark_suite()
        print_summary_report(report)

        # Export comprehensive results
        export_file = benchmarks.export_results(filename="comprehensive_benchmark_results.json")
        print(f"\n💾 Comprehensive results exported to: {export_file}")

        return report

    finally:
        benchmarks.cleanup()


def benchmark_comparison_demo():
    """Demonstrate before/after comparison capabilities."""
    print_banner()
    print("🔄 Running Before/After Comparison Demo")

    benchmarks = LoggingPerformanceBenchmarks()

    try:
        # Simulate "before" - baseline without handlers
        print_benchmark_header("BEFORE", "Baseline logging performance")
        before_result = benchmarks.benchmark_logging_without_handlers(iterations=2000)
        print_benchmark_result(before_result)

        # Simulate "after" - with our logging configuration
        print_benchmark_header("AFTER", "Optimized logging with handlers")
        after_result = benchmarks.benchmark_single_log_statements(iterations=2000)
        print_benchmark_result(after_result)

        # Calculate improvement/regression
        print("\n📊 COMPARISON ANALYSIS:")
        time_change = after_result.average_operation_time_ms - before_result.average_operation_time_ms
        percent_change = (time_change / before_result.average_operation_time_ms) * 100 if before_result.average_operation_time_ms > 0 else 0

        if time_change > 0:
            print(f"   ⚠️  Performance Regression: +{time_change:.3f}ms ({percent_change:+.1f}%)")
        else:
            print(f"   ✅ Performance Improvement: {time_change:.3f}ms ({percent_change:+.1f}%)")

        print(f"   Before: {before_result.average_operation_time_ms:.3f}ms")
        print(f"   After:  {after_result.average_operation_time_ms:.3f}ms")

        # Memory comparison
        memory_change = after_result.memory_delta_mb - before_result.memory_delta_mb
        print(f"   Memory impact: {memory_change:+.2f}MB difference")

        # Export comparison results
        comparison_data = {
            "comparison_type": "before_after_logging_optimization",
            "timestamp": datetime.now().isoformat(),
            "before_result": before_result.__dict__,
            "after_result": after_result.__dict__,
            "analysis": {
                "time_change_ms": time_change,
                "percent_change": percent_change,
                "memory_change_mb": memory_change,
                "regression": time_change > 0,
                "significant_change": abs(percent_change) > 10
            }
        }

        comparison_file = Path(benchmarks.test_log_dir) / "comparison_results.json"
        with open(comparison_file, 'w') as f:
            json.dump(comparison_data, f, default=str, indent=2)

        print(f"\n💾 Comparison results exported to: {comparison_file}")

    finally:
        benchmarks.cleanup()


def main():
    """Main function to run selected benchmark."""
    if len(sys.argv) < 2:
        print("Usage: python run_logging_performance_benchmarks.py [quick|comprehensive|comparison]")
        print("  quick       - Fast benchmark with reduced iterations")
        print("  comprehensive - Full benchmark suite with complete iterations")
        print("  comparison  - Before/after comparison demo")
        sys.exit(1)

    mode = sys.argv[1].lower()

    if mode == "quick":
        asyncio.run(run_quick_benchmark())
    elif mode == "comprehensive":
        asyncio.run(run_comprehensive_benchmark())
    elif mode == "comparison":
        benchmark_comparison_demo()
    else:
        print(f"Unknown mode: {mode}")
        print("Available modes: quick, comprehensive, comparison")
        sys.exit(1)


if __name__ == "__main__":
    main()