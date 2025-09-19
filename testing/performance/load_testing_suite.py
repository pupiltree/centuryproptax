"""Comprehensive load testing suite for property tax chatbot."""

import asyncio
import aiohttp
import time
import logging
import statistics
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import json

from config.performance_thresholds import (
    PerformanceThresholds,
    LoadTestScenario,
    PerformanceMetric,
    performance_thresholds
)


@dataclass
class LoadTestResult:
    """Individual load test result."""
    test_id: str
    scenario: LoadTestScenario
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    concurrent_users: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float
    min_response_time: float
    max_response_time: float
    requests_per_second: float
    error_rate: float
    errors_by_type: Dict[str, int]
    endpoint_performance: Dict[str, Dict[str, float]]
    resource_usage: Dict[str, float]


@dataclass
class UserSession:
    """Virtual user session data."""
    user_id: str
    session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    scenario_type: str
    requests_made: int
    total_response_time: float
    errors_encountered: int
    current_step: int


@dataclass
class RequestResult:
    """Individual request result."""
    timestamp: datetime
    endpoint: str
    method: str
    response_time: float
    status_code: int
    success: bool
    error_message: Optional[str]
    response_size: int


class VirtualUser:
    """Virtual user for load testing."""

    def __init__(self, user_id: str, scenario_type: str, endpoints: List[str],
                 think_time: float, session_duration: int):
        self.user_id = user_id
        self.scenario_type = scenario_type
        self.endpoints = endpoints
        self.think_time = think_time
        self.session_duration = session_duration
        self.session = UserSession(
            user_id=user_id,
            session_id=f"session_{user_id}_{int(time.time())}",
            start_time=datetime.now(),
            end_time=None,
            scenario_type=scenario_type,
            requests_made=0,
            total_response_time=0.0,
            errors_encountered=0,
            current_step=0
        )
        self.request_results: List[RequestResult] = []

    async def run_session(self, base_url: str, session_timeout: aiohttp.ClientTimeout) -> UserSession:
        """Run a complete user session."""
        session_start = time.time()

        async with aiohttp.ClientSession(timeout=session_timeout) as http_session:
            while (time.time() - session_start) < self.session_duration:
                # Select endpoint for this request
                endpoint = random.choice(self.endpoints)

                # Make request
                request_result = await self._make_request(http_session, base_url, endpoint)
                self.request_results.append(request_result)

                # Update session stats
                self.session.requests_made += 1
                self.session.total_response_time += request_result.response_time
                if not request_result.success:
                    self.session.errors_encountered += 1

                # Think time before next request
                await asyncio.sleep(self.think_time + random.uniform(-0.5, 0.5))

                self.session.current_step += 1

        self.session.end_time = datetime.now()
        return self.session

    async def _make_request(self, session: aiohttp.ClientSession, base_url: str, endpoint: str) -> RequestResult:
        """Make a single HTTP request."""
        start_time = time.time()
        request_timestamp = datetime.now()

        try:
            # Prepare request data based on endpoint
            method, url, data = self._prepare_request(base_url, endpoint)

            if method.upper() == "GET":
                async with session.get(url) as response:
                    content = await response.read()
                    response_time = time.time() - start_time

                    return RequestResult(
                        timestamp=request_timestamp,
                        endpoint=endpoint,
                        method=method,
                        response_time=response_time,
                        status_code=response.status,
                        success=200 <= response.status < 400,
                        error_message=None if 200 <= response.status < 400 else f"HTTP {response.status}",
                        response_size=len(content)
                    )
            else:
                async with session.post(url, json=data) as response:
                    content = await response.read()
                    response_time = time.time() - start_time

                    return RequestResult(
                        timestamp=request_timestamp,
                        endpoint=endpoint,
                        method=method,
                        response_time=response_time,
                        status_code=response.status,
                        success=200 <= response.status < 400,
                        error_message=None if 200 <= response.status < 400 else f"HTTP {response.status}",
                        response_size=len(content)
                    )

        except Exception as e:
            response_time = time.time() - start_time
            return RequestResult(
                timestamp=request_timestamp,
                endpoint=endpoint,
                method="GET",
                response_time=response_time,
                status_code=0,
                success=False,
                error_message=str(e),
                response_size=0
            )

    def _prepare_request(self, base_url: str, endpoint: str) -> Tuple[str, str, Optional[Dict]]:
        """Prepare request method, URL, and data based on endpoint."""
        url = f"{base_url}{endpoint}"

        # Property tax specific request data
        if endpoint == "/api/property/search":
            return "GET", f"{url}?address=123 Main St&city=Austin", None
        elif endpoint == "/api/property/details":
            return "GET", f"{url}?property_id=PROP{random.randint(1000, 9999)}", None
        elif endpoint == "/api/tax/calculate":
            return "POST", url, {
                "property_id": f"PROP{random.randint(1000, 9999)}",
                "year": 2024,
                "exemptions": ["homestead"]
            }
        elif endpoint == "/api/payment/process":
            return "POST", url, {
                "property_id": f"PROP{random.randint(1000, 9999)}",
                "amount": round(random.uniform(1000, 5000), 2),
                "payment_method": "credit_card"
            }
        elif endpoint == "/api/exemption/apply":
            return "POST", url, {
                "property_id": f"PROP{random.randint(1000, 9999)}",
                "exemption_type": "homestead",
                "applicant_info": {"name": "Test User", "email": "test@example.com"}
            }
        elif endpoint == "/api/chat/message":
            return "POST", url, {
                "message": "What is my property tax for 123 Main Street?",
                "session_id": self.session.session_id
            }
        else:
            return "GET", url, None


class LoadTestingSuite:
    """Comprehensive load testing suite for property tax chatbot."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
        self.performance_thresholds = performance_thresholds
        self.test_results: List[LoadTestResult] = []

    async def run_load_test(self, scenario: LoadTestScenario,
                           duration_override: Optional[int] = None) -> LoadTestResult:
        """Run a complete load test for specified scenario."""
        config = self.performance_thresholds.get_load_test_config(scenario)
        if not config:
            raise ValueError(f"No configuration found for scenario: {scenario.value}")

        test_id = f"load_test_{scenario.value}_{int(time.time())}"
        start_time = datetime.now()

        self.logger.info(f"Starting load test {test_id} for scenario {scenario.value}")
        self.logger.info(f"Configuration: {config.concurrent_users} users, {config.test_duration_seconds}s duration")

        # Override duration if specified
        test_duration = duration_override or config.test_duration_seconds

        # Create virtual users
        virtual_users = []
        for i in range(config.concurrent_users):
            user_id = f"user_{scenario.value}_{i}"
            scenario_type = self._select_user_scenario(config.user_scenarios)
            scenario_config = self.performance_thresholds.PROPERTY_TAX_SCENARIOS[scenario_type]

            virtual_user = VirtualUser(
                user_id=user_id,
                scenario_type=scenario_type,
                endpoints=scenario_config["endpoints"],
                think_time=config.think_time,
                session_duration=min(test_duration, scenario_config["session_duration"])
            )
            virtual_users.append(virtual_user)

        # Configure session timeout
        session_timeout = aiohttp.ClientTimeout(total=30, connect=10)

        # Run ramp-up
        self.logger.info(f"Ramping up {config.concurrent_users} users over {config.ramp_up_duration_seconds} seconds")
        user_tasks = []
        ramp_up_delay = config.ramp_up_duration_seconds / config.concurrent_users

        for i, user in enumerate(virtual_users):
            await asyncio.sleep(ramp_up_delay)
            task = asyncio.create_task(user.run_session(self.base_url, session_timeout))
            user_tasks.append(task)

        # Wait for all user sessions to complete
        completed_sessions = []
        for task in asyncio.as_completed(user_tasks):
            try:
                session = await task
                completed_sessions.append(session)
            except Exception as e:
                self.logger.error(f"User session failed: {str(e)}")

        end_time = datetime.now()
        actual_duration = (end_time - start_time).total_seconds()

        # Aggregate results
        all_request_results = []
        for user in virtual_users:
            all_request_results.extend(user.request_results)

        # Calculate performance metrics
        result = self._calculate_performance_metrics(
            test_id=test_id,
            scenario=scenario,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=actual_duration,
            concurrent_users=config.concurrent_users,
            request_results=all_request_results,
            user_sessions=completed_sessions
        )

        self.test_results.append(result)
        self.logger.info(f"Load test {test_id} completed: {result.requests_per_second:.1f} RPS, "
                        f"{result.average_response_time:.3f}s avg response time, "
                        f"{result.error_rate:.2f}% error rate")

        return result

    def _select_user_scenario(self, available_scenarios: List[str]) -> str:
        """Select user scenario based on weights."""
        if available_scenarios == ["all_scenarios"]:
            scenarios = list(self.performance_thresholds.PROPERTY_TAX_SCENARIOS.keys())
        else:
            scenarios = available_scenarios

        # Weight-based selection
        weights = []
        for scenario in scenarios:
            if scenario in self.performance_thresholds.PROPERTY_TAX_SCENARIOS:
                weights.append(self.performance_thresholds.PROPERTY_TAX_SCENARIOS[scenario]["weight"])
            else:
                weights.append(10)  # Default weight

        return random.choices(scenarios, weights=weights)[0]

    def _calculate_performance_metrics(self, test_id: str, scenario: LoadTestScenario,
                                     start_time: datetime, end_time: datetime,
                                     duration_seconds: float, concurrent_users: int,
                                     request_results: List[RequestResult],
                                     user_sessions: List[UserSession]) -> LoadTestResult:
        """Calculate comprehensive performance metrics from test results."""
        total_requests = len(request_results)
        successful_requests = len([r for r in request_results if r.success])
        failed_requests = total_requests - successful_requests

        # Response time statistics
        response_times = [r.response_time for r in request_results]
        if response_times:
            average_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            p95_response_time = self._percentile(response_times, 95)
            p99_response_time = self._percentile(response_times, 99)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
        else:
            average_response_time = median_response_time = p95_response_time = p99_response_time = 0
            min_response_time = max_response_time = 0

        # Calculate RPS
        requests_per_second = total_requests / duration_seconds if duration_seconds > 0 else 0

        # Error rate
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0

        # Error types
        errors_by_type = {}
        for result in request_results:
            if not result.success and result.error_message:
                error_type = result.error_message.split()[0] if result.error_message else "Unknown"
                errors_by_type[error_type] = errors_by_type.get(error_type, 0) + 1

        # Endpoint performance breakdown
        endpoint_performance = {}
        endpoints = set(r.endpoint for r in request_results)
        for endpoint in endpoints:
            endpoint_results = [r for r in request_results if r.endpoint == endpoint]
            endpoint_response_times = [r.response_time for r in endpoint_results]

            if endpoint_response_times:
                endpoint_performance[endpoint] = {
                    "count": len(endpoint_results),
                    "average_response_time": statistics.mean(endpoint_response_times),
                    "p95_response_time": self._percentile(endpoint_response_times, 95),
                    "error_rate": len([r for r in endpoint_results if not r.success]) / len(endpoint_results) * 100
                }

        # Simulated resource usage (in production, this would come from monitoring)
        resource_usage = {
            "cpu_usage_percent": min(95, 30 + (concurrent_users / 10) * 2),
            "memory_usage_percent": min(98, 40 + (concurrent_users / 10) * 1.5),
            "disk_io_percent": min(90, 20 + (total_requests / 1000) * 5),
            "network_io_mbps": min(100, (total_requests / duration_seconds) * 0.1)
        }

        return LoadTestResult(
            test_id=test_id,
            scenario=scenario,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration_seconds,
            concurrent_users=concurrent_users,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=average_response_time,
            median_response_time=median_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            errors_by_type=errors_by_type,
            endpoint_performance=endpoint_performance,
            resource_usage=resource_usage
        )

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile value."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * (percentile / 100))
        return sorted_data[min(index, len(sorted_data) - 1)]

    async def run_comprehensive_load_test_suite(self) -> Dict[str, Any]:
        """Run comprehensive load test suite across all scenarios."""
        self.logger.info("Starting comprehensive load test suite")

        suite_start_time = datetime.now()
        suite_results = {}

        # Test scenarios in order of increasing load
        test_scenarios = [
            LoadTestScenario.BASELINE,
            LoadTestScenario.NORMAL_LOAD,
            LoadTestScenario.PEAK_LOAD,
            LoadTestScenario.STRESS_TEST
        ]

        for scenario in test_scenarios:
            try:
                self.logger.info(f"Running {scenario.value} load test...")
                result = await self.run_load_test(scenario)
                suite_results[scenario.value] = result

                # Brief pause between tests
                await asyncio.sleep(30)

            except Exception as e:
                self.logger.error(f"Failed to run {scenario.value} test: {str(e)}")
                suite_results[scenario.value] = {"error": str(e)}

        suite_end_time = datetime.now()
        suite_duration = (suite_end_time - suite_start_time).total_seconds()

        # Generate comprehensive report
        comprehensive_report = self._generate_comprehensive_report(suite_results, suite_duration)

        self.logger.info(f"Comprehensive load test suite completed in {suite_duration:.1f} seconds")
        return comprehensive_report

    def _generate_comprehensive_report(self, suite_results: Dict[str, Any],
                                     suite_duration: float) -> Dict[str, Any]:
        """Generate comprehensive performance test report."""
        report = {
            "test_suite_summary": {
                "total_duration_seconds": suite_duration,
                "scenarios_tested": len(suite_results),
                "overall_status": "passed",
                "timestamp": datetime.now().isoformat()
            },
            "scenario_results": {},
            "performance_analysis": {},
            "threshold_compliance": {},
            "recommendations": []
        }

        passed_tests = 0
        total_tests = 0

        for scenario_name, result in suite_results.items():
            if isinstance(result, dict) and "error" in result:
                report["scenario_results"][scenario_name] = {
                    "status": "failed",
                    "error": result["error"]
                }
                continue

            if not isinstance(result, LoadTestResult):
                continue

            total_tests += 1

            # Analyze against thresholds
            scenario_enum = LoadTestScenario(scenario_name)
            threshold_compliance = self._analyze_threshold_compliance(result, scenario_enum)

            scenario_passed = all(
                compliance["status"] in ["excellent", "acceptable"]
                for compliance in threshold_compliance.values()
            )

            if scenario_passed:
                passed_tests += 1

            report["scenario_results"][scenario_name] = {
                "status": "passed" if scenario_passed else "failed",
                "concurrent_users": result.concurrent_users,
                "duration_seconds": result.duration_seconds,
                "total_requests": result.total_requests,
                "requests_per_second": result.requests_per_second,
                "average_response_time": result.average_response_time,
                "p95_response_time": result.p95_response_time,
                "error_rate": result.error_rate,
                "resource_usage": result.resource_usage
            }

            report["threshold_compliance"][scenario_name] = threshold_compliance

        # Overall pass/fail
        report["test_suite_summary"]["overall_status"] = "passed" if passed_tests == total_tests else "failed"
        report["test_suite_summary"]["passed_scenarios"] = passed_tests
        report["test_suite_summary"]["total_scenarios"] = total_tests

        # Generate recommendations
        report["recommendations"] = self._generate_performance_recommendations(suite_results)

        return report

    def _analyze_threshold_compliance(self, result: LoadTestResult,
                                    scenario: LoadTestScenario) -> Dict[str, Dict[str, Any]]:
        """Analyze test result against performance thresholds."""
        compliance = {}

        # Response time compliance
        response_time_validation = self.performance_thresholds.validate_performance_result(
            PerformanceMetric.RESPONSE_TIME, scenario, result.average_response_time
        )
        compliance["response_time"] = response_time_validation

        # Error rate compliance
        error_rate_validation = self.performance_thresholds.validate_performance_result(
            PerformanceMetric.ERROR_RATE, scenario, result.error_rate
        )
        compliance["error_rate"] = error_rate_validation

        # Throughput compliance (if threshold exists)
        throughput_threshold = self.performance_thresholds.get_threshold(
            PerformanceMetric.THROUGHPUT, scenario
        )
        if throughput_threshold:
            throughput_validation = self.performance_thresholds.validate_performance_result(
                PerformanceMetric.THROUGHPUT, scenario, result.requests_per_second
            )
            compliance["throughput"] = throughput_validation

        return compliance

    def _generate_performance_recommendations(self, suite_results: Dict[str, Any]) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []

        for scenario_name, result in suite_results.items():
            if not isinstance(result, LoadTestResult):
                continue

            # High response time recommendations
            if result.average_response_time > 2.0:
                recommendations.append(
                    f"Response time optimization needed for {scenario_name}: "
                    f"Average {result.average_response_time:.2f}s exceeds target"
                )

            # High error rate recommendations
            if result.error_rate > 1.0:
                recommendations.append(
                    f"Error rate reduction needed for {scenario_name}: "
                    f"{result.error_rate:.2f}% error rate is too high"
                )

            # Resource usage recommendations
            if result.resource_usage.get("cpu_usage_percent", 0) > 85:
                recommendations.append(
                    f"CPU optimization needed: {result.resource_usage['cpu_usage_percent']:.1f}% usage under {scenario_name}"
                )

            if result.resource_usage.get("memory_usage_percent", 0) > 90:
                recommendations.append(
                    f"Memory optimization needed: {result.resource_usage['memory_usage_percent']:.1f}% usage under {scenario_name}"
                )

        if not recommendations:
            recommendations.append("All performance metrics are within acceptable thresholds")

        return recommendations

    def export_results(self, format_type: str = "json") -> str:
        """Export load test results in specified format."""
        if format_type.lower() == "json":
            return json.dumps([asdict(result) for result in self.test_results],
                            default=str, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")


# Example usage and testing
if __name__ == "__main__":
    async def run_load_test_example():
        # Initialize load testing suite
        load_tester = LoadTestingSuite("http://localhost:8000")

        print("Starting load testing suite...")

        # Run a single scenario test
        print("Running baseline load test...")
        baseline_result = await load_tester.run_load_test(LoadTestScenario.BASELINE, duration_override=60)

        print(f"Baseline test results:")
        print(f"  Concurrent users: {baseline_result.concurrent_users}")
        print(f"  Total requests: {baseline_result.total_requests}")
        print(f"  Requests per second: {baseline_result.requests_per_second:.1f}")
        print(f"  Average response time: {baseline_result.average_response_time:.3f}s")
        print(f"  P95 response time: {baseline_result.p95_response_time:.3f}s")
        print(f"  Error rate: {baseline_result.error_rate:.2f}%")

        # Uncomment to run full suite (takes longer)
        # print("\nRunning comprehensive load test suite...")
        # comprehensive_results = await load_tester.run_comprehensive_load_test_suite()
        # print(f"Suite status: {comprehensive_results['test_suite_summary']['overall_status']}")

    # Run example
    asyncio.run(run_load_test_example())