#!/usr/bin/env python3
"""
Quick Logging Performance Summary Script.

This script provides a quick, quiet performance test to verify
logging meets the <5ms threshold without verbose output.
"""

import time
import sys
import os
import tempfile
import logging
from pathlib import Path

# Suppress verbose logging during benchmarks
logging.getLogger().setLevel(logging.ERROR)
os.environ['LOG_LEVEL'] = 'ERROR'

# Add project paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "testing" / "performance"))

from logging_performance_benchmarks import LoggingPerformanceBenchmarks


def run_quiet_performance_test():
    """Run a quiet performance test with minimal output."""
    print("🚀 Logging Performance Summary Test")
    print("🎯 Target: <5ms per logging operation")
    print("-" * 50)

    with tempfile.TemporaryDirectory() as temp_dir:
        benchmarks = LoggingPerformanceBenchmarks(test_log_dir=temp_dir)

        try:
            # Test 1: Single log operations (small test)
            print("📊 Testing single log operations...")
            single_result = benchmarks.benchmark_single_log_statements(iterations=100)

            status = "✅ PASS" if single_result.overhead_threshold_met else "❌ FAIL"
            print(f"   {status} - Average: {single_result.average_operation_time_ms:.3f}ms")
            print(f"   P95: {single_result.p95_operation_time_ms:.3f}ms")
            print(f"   Throughput: {single_result.operations_per_second:.0f} ops/sec")

            # Test 2: High volume logging
            print("\n📊 Testing high volume logging...")
            volume_result = benchmarks.benchmark_high_volume_logging(log_count=500, concurrent_threads=2)

            status = "✅ PASS" if volume_result.overhead_threshold_met else "❌ FAIL"
            print(f"   {status} - Average: {volume_result.average_operation_time_ms:.3f}ms")
            print(f"   P95: {volume_result.p95_operation_time_ms:.3f}ms")
            print(f"   Throughput: {volume_result.operations_per_second:.0f} ops/sec")

            # Overall assessment
            print("\n" + "=" * 50)
            all_passed = single_result.overhead_threshold_met and volume_result.overhead_threshold_met

            if all_passed:
                print("🎉 LOGGING PERFORMANCE: EXCELLENT")
                print("   All tests meet the <5ms threshold")
                print("   Logging system is ready for production")
            else:
                print("⚠️  LOGGING PERFORMANCE: NEEDS OPTIMIZATION")
                print("   Some tests exceed the 5ms threshold")
                print("   Consider optimizing logging configuration")

            # Performance characteristics summary
            print("\n📋 Performance Characteristics:")
            print(f"   • Single operation overhead: {single_result.average_operation_time_ms:.3f}ms")
            print(f"   • High-volume performance: {volume_result.average_operation_time_ms:.3f}ms")
            print(f"   • Peak throughput: {max(single_result.operations_per_second, volume_result.operations_per_second):.0f} ops/sec")
            print(f"   • Memory efficiency: {volume_result.memory_delta_mb:.2f}MB for 500 operations")

            return all_passed

        finally:
            benchmarks.cleanup()


if __name__ == "__main__":
    try:
        success = run_quiet_performance_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        sys.exit(1)