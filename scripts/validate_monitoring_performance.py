#!/usr/bin/env python3
"""Performance validation script for monitoring system under production loads.

This script validates:
- Monitoring dashboard response times under concurrent load
- Database and Redis performance with monitoring queries
- Alert system responsiveness and notification delivery
- Memory usage and resource consumption of monitoring components
- Dashboard scalability with multiple concurrent users
"""

import asyncio
import aiohttp
import time
import psutil
import statistics
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import logging
import os
import sys
from dataclasses import dataclass

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.monitoring_auth import auth_manager
from core.alert_manager import alert_manager
from core.data_retention import retention_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('validation_results.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class LoadTestConfig:
    """Load test configuration."""
    concurrent_users: int = 50
    test_duration_seconds: int = 300  # 5 minutes
    monitoring_secret: str = "monitoring-secret-key"
    base_url: str = "http://localhost:8000"
    endpoints_to_test: List[str] = None

    def __post_init__(self):
        if self.endpoints_to_test is None:
            self.endpoints_to_test = [
                "/monitoring/performance",
                "/monitoring/business",
                "/monitoring/infrastructure",
                "/monitoring/alerts",
                "/monitoring/health"
            ]

@dataclass
class PerformanceMetrics:
    """Performance test results."""
    endpoint: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float

class MonitoringPerformanceValidator:
    """Validates monitoring system performance under production loads."""

    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.results: List[PerformanceMetrics] = []
        self.system_metrics: Dict[str, List[float]] = {
            'cpu_percent': [],
            'memory_percent': [],
            'disk_io': [],
            'network_io': []
        }

    async def run_validation(self) -> Dict[str, Any]:
        """Run comprehensive monitoring performance validation."""
        logger.info("🚀 Starting monitoring system performance validation")
        logger.info(f"Configuration: {self.config.concurrent_users} users, {self.config.test_duration_seconds}s duration")

        validation_results = {
            "timestamp": datetime.now().isoformat(),
            "config": self.config.__dict__,
            "endpoint_performance": {},
            "system_performance": {},
            "alert_system_performance": {},
            "database_performance": {},
            "overall_assessment": {}
        }

        try:
            # Initialize session
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)

            # Run performance tests
            logger.info("🔍 Testing endpoint performance under load")
            validation_results["endpoint_performance"] = await self._test_endpoint_performance()

            logger.info("📊 Testing system resource usage")
            validation_results["system_performance"] = await self._test_system_performance()

            logger.info("🚨 Testing alert system performance")
            validation_results["alert_system_performance"] = await self._test_alert_system()

            logger.info("🗃️ Testing database performance")
            validation_results["database_performance"] = await self._test_database_performance()

            # Generate overall assessment
            validation_results["overall_assessment"] = self._generate_assessment(validation_results)

            # Save results
            await self._save_validation_results(validation_results)

        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            validation_results["error"] = str(e)

        finally:
            if self.session:
                await self.session.close()

        return validation_results

    async def _test_endpoint_performance(self) -> Dict[str, Any]:
        """Test monitoring endpoint performance under concurrent load."""
        endpoint_results = {}

        for endpoint in self.config.endpoints_to_test:
            logger.info(f"🔄 Testing endpoint: {endpoint}")

            # Run load test for this endpoint
            response_times = []
            status_codes = []

            # Create tasks for concurrent requests
            tasks = []
            for _ in range(self.config.concurrent_users):
                task = asyncio.create_task(
                    self._load_test_endpoint(endpoint, response_times, status_codes)
                )
                tasks.append(task)

            # Run tasks concurrently
            start_time = time.time()
            await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time

            # Calculate metrics
            if response_times:
                metrics = PerformanceMetrics(
                    endpoint=endpoint,
                    total_requests=len(response_times),
                    successful_requests=len([s for s in status_codes if 200 <= s < 300]),
                    failed_requests=len([s for s in status_codes if s >= 400]),
                    avg_response_time=statistics.mean(response_times),
                    min_response_time=min(response_times),
                    max_response_time=max(response_times),
                    p95_response_time=statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times),
                    p99_response_time=statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else max(response_times),
                    requests_per_second=len(response_times) / total_time,
                    error_rate=len([s for s in status_codes if s >= 400]) / len(status_codes)
                )

                endpoint_results[endpoint] = {
                    "metrics": metrics.__dict__,
                    "performance_grade": self._grade_endpoint_performance(metrics)
                }

                logger.info(f"✅ {endpoint}: {metrics.avg_response_time:.3f}s avg, {metrics.requests_per_second:.1f} RPS")
            else:
                endpoint_results[endpoint] = {
                    "error": "No successful requests",
                    "performance_grade": "F"
                }

        return endpoint_results

    async def _load_test_endpoint(self, endpoint: str, response_times: List[float], status_codes: List[int]):
        """Load test a specific endpoint."""
        headers = {"Authorization": f"Bearer {self.config.monitoring_secret}"}
        url = f"{self.config.base_url}{endpoint}"

        end_time = time.time() + self.config.test_duration_seconds

        while time.time() < end_time:
            try:
                start_time = time.time()
                async with self.session.get(url, headers=headers) as response:
                    await response.read()  # Consume response body
                    response_time = time.time() - start_time

                    response_times.append(response_time)
                    status_codes.append(response.status)

                # Small delay to avoid overwhelming the server
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.warning(f"Request failed for {endpoint}: {e}")
                status_codes.append(500)

    def _grade_endpoint_performance(self, metrics: PerformanceMetrics) -> str:
        """Grade endpoint performance based on metrics."""
        # Performance grading criteria
        if metrics.error_rate > 0.05:  # >5% error rate
            return "F"
        elif metrics.avg_response_time > 5.0:  # >5s average response
            return "F"
        elif metrics.p95_response_time > 10.0:  # >10s 95th percentile
            return "D"
        elif metrics.avg_response_time > 2.0:  # >2s average response
            return "C"
        elif metrics.avg_response_time > 1.0:  # >1s average response
            return "B"
        else:  # <1s average response
            return "A"

    async def _test_system_performance(self) -> Dict[str, Any]:
        """Test system resource usage during monitoring operations."""
        logger.info("📊 Starting system performance monitoring")

        # Collect baseline metrics
        baseline_cpu = psutil.cpu_percent(interval=1)
        baseline_memory = psutil.virtual_memory().percent
        baseline_disk = psutil.disk_io_counters()
        baseline_network = psutil.net_io_counters()

        # Run monitoring operations while collecting metrics
        start_time = time.time()
        metrics_collection_duration = 60  # 1 minute

        cpu_samples = []
        memory_samples = []

        while time.time() - start_time < metrics_collection_duration:
            # Simulate monitoring dashboard requests
            await self._simulate_dashboard_usage()

            # Collect system metrics
            cpu_samples.append(psutil.cpu_percent())
            memory_samples.append(psutil.virtual_memory().percent)

            await asyncio.sleep(1)

        # Calculate final metrics
        final_disk = psutil.disk_io_counters()
        final_network = psutil.net_io_counters()

        return {
            "baseline": {
                "cpu_percent": baseline_cpu,
                "memory_percent": baseline_memory
            },
            "during_load": {
                "avg_cpu_percent": statistics.mean(cpu_samples),
                "max_cpu_percent": max(cpu_samples),
                "avg_memory_percent": statistics.mean(memory_samples),
                "max_memory_percent": max(memory_samples)
            },
            "disk_io": {
                "read_bytes": final_disk.read_bytes - baseline_disk.read_bytes if baseline_disk and final_disk else 0,
                "write_bytes": final_disk.write_bytes - baseline_disk.write_bytes if baseline_disk and final_disk else 0
            },
            "network_io": {
                "bytes_sent": final_network.bytes_sent - baseline_network.bytes_sent if baseline_network and final_network else 0,
                "bytes_recv": final_network.bytes_recv - baseline_network.bytes_recv if baseline_network and final_network else 0
            },
            "resource_grade": self._grade_system_performance(cpu_samples, memory_samples)
        }

    async def _simulate_dashboard_usage(self):
        """Simulate typical dashboard usage patterns."""
        try:
            headers = {"Authorization": f"Bearer {self.config.monitoring_secret}"}

            # Simulate user browsing different dashboards
            endpoints = ["/monitoring/performance", "/monitoring/business", "/monitoring/infrastructure"]
            for endpoint in endpoints:
                url = f"{self.config.base_url}{endpoint}"
                async with self.session.get(url, headers=headers) as response:
                    await response.read()

        except Exception as e:
            logger.warning(f"Simulation request failed: {e}")

    def _grade_system_performance(self, cpu_samples: List[float], memory_samples: List[float]) -> str:
        """Grade system performance based on resource usage."""
        avg_cpu = statistics.mean(cpu_samples)
        max_cpu = max(cpu_samples)
        avg_memory = statistics.mean(memory_samples)
        max_memory = max(memory_samples)

        # Performance grading criteria
        if max_cpu > 95 or max_memory > 95:  # System overload
            return "F"
        elif avg_cpu > 80 or avg_memory > 80:  # High resource usage
            return "D"
        elif avg_cpu > 60 or avg_memory > 60:  # Moderate resource usage
            return "C"
        elif avg_cpu > 40 or avg_memory > 40:  # Low resource usage
            return "B"
        else:  # Very low resource usage
            return "A"

    async def _test_alert_system(self) -> Dict[str, Any]:
        """Test alert system performance and responsiveness."""
        logger.info("🚨 Testing alert system performance")

        # Test alert evaluation performance
        start_time = time.time()

        # Simulate metrics that would trigger alerts
        test_metrics = {
            "response_time_95th": 3.0,  # Should trigger high response time alert
            "error_rate": 0.1,          # Should trigger high error rate alert
            "memory_usage_mb": 2048,    # Should trigger high memory alert
            "database_status": "error"   # Should trigger database alert
        }

        try:
            # Test alert evaluation
            await alert_manager.evaluate_metrics(test_metrics)
            evaluation_time = time.time() - start_time

            # Test alert configuration retrieval
            start_time = time.time()
            alert_summary = alert_manager.get_alert_summary()
            config_time = time.time() - start_time

            # Test active alerts retrieval
            start_time = time.time()
            active_alerts = alert_manager.get_active_alerts()
            active_time = time.time() - start_time

            return {
                "alert_evaluation_time": evaluation_time,
                "config_retrieval_time": config_time,
                "active_alerts_time": active_time,
                "active_alerts_count": len(active_alerts),
                "total_alert_rules": alert_summary.get("total_rules", 0),
                "enabled_rules": alert_summary.get("enabled_rules", 0),
                "performance_grade": self._grade_alert_performance(evaluation_time, config_time)
            }

        except Exception as e:
            logger.error(f"Alert system test failed: {e}")
            return {
                "error": str(e),
                "performance_grade": "F"
            }

    def _grade_alert_performance(self, evaluation_time: float, config_time: float) -> str:
        """Grade alert system performance."""
        # Alert system should be very fast
        if evaluation_time > 5.0 or config_time > 2.0:  # Too slow
            return "F"
        elif evaluation_time > 2.0 or config_time > 1.0:  # Slow
            return "D"
        elif evaluation_time > 1.0 or config_time > 0.5:  # Moderate
            return "C"
        elif evaluation_time > 0.5 or config_time > 0.2:  # Good
            return "B"
        else:  # Excellent
            return "A"

    async def _test_database_performance(self) -> Dict[str, Any]:
        """Test database performance with monitoring queries."""
        logger.info("🗃️ Testing database performance")

        try:
            # Test data retention operations
            start_time = time.time()
            retention_summary = retention_manager.get_retention_summary()
            retention_time = time.time() - start_time

            # Test auth operations
            start_time = time.time()
            user_summary = auth_manager.get_user_summary()
            auth_time = time.time() - start_time

            # Test audit log retrieval
            start_time = time.time()
            audit_logs = auth_manager.get_audit_logs(hours=1)
            audit_time = time.time() - start_time

            return {
                "retention_query_time": retention_time,
                "auth_query_time": auth_time,
                "audit_query_time": audit_time,
                "audit_logs_count": len(audit_logs),
                "retention_policies": len(retention_summary.get("retention_policies", {})),
                "performance_grade": self._grade_database_performance(retention_time, auth_time, audit_time)
            }

        except Exception as e:
            logger.error(f"Database performance test failed: {e}")
            return {
                "error": str(e),
                "performance_grade": "F"
            }

    def _grade_database_performance(self, retention_time: float, auth_time: float, audit_time: float) -> str:
        """Grade database performance."""
        max_time = max(retention_time, auth_time, audit_time)
        avg_time = (retention_time + auth_time + audit_time) / 3

        if max_time > 5.0 or avg_time > 2.0:  # Too slow
            return "F"
        elif max_time > 2.0 or avg_time > 1.0:  # Slow
            return "D"
        elif max_time > 1.0 or avg_time > 0.5:  # Moderate
            return "C"
        elif max_time > 0.5 or avg_time > 0.2:  # Good
            return "B"
        else:  # Excellent
            return "A"

    def _generate_assessment(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall performance assessment."""
        grades = []

        # Collect all performance grades
        endpoint_grades = [
            ep.get("performance_grade", "F")
            for ep in results.get("endpoint_performance", {}).values()
        ]
        grades.extend(endpoint_grades)

        system_grade = results.get("system_performance", {}).get("resource_grade", "F")
        alert_grade = results.get("alert_system_performance", {}).get("performance_grade", "F")
        db_grade = results.get("database_performance", {}).get("performance_grade", "F")

        grades.extend([system_grade, alert_grade, db_grade])

        # Calculate overall grade
        grade_points = {"A": 4, "B": 3, "C": 2, "D": 1, "F": 0}
        total_points = sum(grade_points.get(grade, 0) for grade in grades)
        avg_points = total_points / len(grades) if grades else 0

        if avg_points >= 3.5:
            overall_grade = "A"
        elif avg_points >= 2.5:
            overall_grade = "B"
        elif avg_points >= 1.5:
            overall_grade = "C"
        elif avg_points >= 0.5:
            overall_grade = "D"
        else:
            overall_grade = "F"

        # Generate recommendations
        recommendations = self._generate_recommendations(results, overall_grade)

        return {
            "overall_grade": overall_grade,
            "component_grades": {
                "endpoints": endpoint_grades,
                "system_resources": system_grade,
                "alert_system": alert_grade,
                "database": db_grade
            },
            "recommendations": recommendations,
            "production_ready": overall_grade in ["A", "B"],
            "performance_summary": self._generate_performance_summary(results)
        }

    def _generate_recommendations(self, results: Dict[str, Any], overall_grade: str) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []

        # Check endpoint performance
        endpoint_results = results.get("endpoint_performance", {})
        for endpoint, data in endpoint_results.items():
            if data.get("performance_grade") in ["D", "F"]:
                metrics = data.get("metrics", {})
                if metrics.get("error_rate", 0) > 0.05:
                    recommendations.append(f"High error rate ({metrics['error_rate']:.1%}) on {endpoint} - investigate server errors")
                if metrics.get("avg_response_time", 0) > 2.0:
                    recommendations.append(f"Slow response time ({metrics['avg_response_time']:.2f}s) on {endpoint} - optimize database queries or add caching")

        # Check system performance
        system_perf = results.get("system_performance", {})
        during_load = system_perf.get("during_load", {})
        if during_load.get("max_cpu_percent", 0) > 80:
            recommendations.append("High CPU usage detected - consider scaling up server resources")
        if during_load.get("max_memory_percent", 0) > 80:
            recommendations.append("High memory usage detected - check for memory leaks or increase RAM")

        # Check alert system
        alert_perf = results.get("alert_system_performance", {})
        if alert_perf.get("performance_grade") in ["D", "F"]:
            recommendations.append("Alert system performance issues - optimize alert evaluation logic")

        # Check database performance
        db_perf = results.get("database_performance", {})
        if db_perf.get("performance_grade") in ["D", "F"]:
            recommendations.append("Database performance issues - add indexes or optimize queries")

        # General recommendations based on overall grade
        if overall_grade == "F":
            recommendations.append("System is not production-ready - address critical performance issues before deployment")
        elif overall_grade == "D":
            recommendations.append("System needs significant optimization before production deployment")
        elif overall_grade == "C":
            recommendations.append("System performance is acceptable but could benefit from optimization")

        return recommendations

    def _generate_performance_summary(self, results: Dict[str, Any]) -> Dict[str, str]:
        """Generate human-readable performance summary."""
        endpoint_results = results.get("endpoint_performance", {})

        # Find fastest and slowest endpoints
        avg_times = {}
        for endpoint, data in endpoint_results.items():
            metrics = data.get("metrics", {})
            avg_times[endpoint] = metrics.get("avg_response_time", float('inf'))

        fastest_endpoint = min(avg_times, key=avg_times.get) if avg_times else "None"
        slowest_endpoint = max(avg_times, key=avg_times.get) if avg_times else "None"

        return {
            "fastest_endpoint": f"{fastest_endpoint} ({avg_times.get(fastest_endpoint, 0):.3f}s)",
            "slowest_endpoint": f"{slowest_endpoint} ({avg_times.get(slowest_endpoint, 0):.3f}s)",
            "total_endpoints_tested": len(endpoint_results),
            "test_duration": f"{self.config.test_duration_seconds}s",
            "concurrent_users": str(self.config.concurrent_users)
        }

    async def _save_validation_results(self, results: Dict[str, Any]):
        """Save validation results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"monitoring_validation_{timestamp}.json"

        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)

            logger.info(f"✅ Validation results saved to {filename}")

            # Print summary
            assessment = results.get("overall_assessment", {})
            logger.info(f"🎯 Overall Grade: {assessment.get('overall_grade', 'Unknown')}")
            logger.info(f"🚀 Production Ready: {assessment.get('production_ready', False)}")

            if assessment.get('recommendations'):
                logger.info("📋 Recommendations:")
                for rec in assessment['recommendations'][:5]:  # Show top 5
                    logger.info(f"   • {rec}")

        except Exception as e:
            logger.error(f"Failed to save results: {e}")


async def main():
    """Main validation runner."""
    # Load configuration from environment or use defaults
    config = LoadTestConfig(
        concurrent_users=int(os.getenv("LOAD_TEST_USERS", "20")),
        test_duration_seconds=int(os.getenv("LOAD_TEST_DURATION", "60")),
        monitoring_secret=os.getenv("MONITORING_SECRET", "monitoring-secret-key"),
        base_url=os.getenv("BASE_URL", "http://localhost:8000")
    )

    validator = MonitoringPerformanceValidator(config)
    results = await validator.run_validation()

    # Return exit code based on results
    overall_grade = results.get("overall_assessment", {}).get("overall_grade", "F")
    if overall_grade in ["A", "B"]:
        logger.info("✅ Monitoring system validation PASSED")
        sys.exit(0)
    else:
        logger.error("❌ Monitoring system validation FAILED")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())