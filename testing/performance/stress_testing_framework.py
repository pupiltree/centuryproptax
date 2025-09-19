"""Stress testing framework for system resilience validation."""

import asyncio
import aiohttp
import time
import logging
import psutil
import random
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

from config.performance_thresholds import (
    LoadTestScenario,
    PerformanceMetric,
    performance_thresholds
)


class StressTestType(Enum):
    """Types of stress tests."""
    LOAD_SPIKE = "load_spike"
    SUSTAINED_OVERLOAD = "sustained_overload"
    MEMORY_PRESSURE = "memory_pressure"
    CPU_SATURATION = "cpu_saturation"
    NETWORK_CONGESTION = "network_congestion"
    DATABASE_OVERLOAD = "database_overload"
    CASCADING_FAILURE = "cascading_failure"
    RECOVERY_VALIDATION = "recovery_validation"


class FailureMode(Enum):
    """System failure modes to test."""
    GRACEFUL_DEGRADATION = "graceful_degradation"
    CIRCUIT_BREAKER = "circuit_breaker"
    RATE_LIMITING = "rate_limiting"
    QUEUE_OVERFLOW = "queue_overflow"
    MEMORY_EXHAUSTION = "memory_exhaustion"
    CONNECTION_POOL_EXHAUSTION = "connection_pool_exhaustion"
    TIMEOUT_CASCADE = "timeout_cascade"


@dataclass
class StressTestConfiguration:
    """Stress test configuration parameters."""
    test_type: StressTestType
    duration_seconds: int
    max_concurrent_users: int
    load_pattern: str  # linear, exponential, spike, sawtooth
    failure_injection: Optional[FailureMode]
    recovery_time_seconds: int
    target_metrics: Dict[str, float]
    chaos_engineering: bool


@dataclass
class StressTestResult:
    """Stress test execution result."""
    test_id: str
    test_type: StressTestType
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    peak_concurrent_users: int
    breaking_point_users: Optional[int]
    system_recovery_time: Optional[float]
    performance_degradation: Dict[str, Dict[str, float]]
    failure_modes_triggered: List[FailureMode]
    resource_exhaustion: Dict[str, float]
    error_patterns: Dict[str, List[Dict[str, Any]]]
    resilience_score: float
    recommendations: List[str]


class SystemMonitor:
    """Real-time system monitoring during stress tests."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.monitoring_data: List[Dict[str, Any]] = []
        self.monitoring_active = False

    async def start_monitoring(self, interval_seconds: float = 1.0):
        """Start continuous system monitoring."""
        self.monitoring_active = True
        self.monitoring_data.clear()

        while self.monitoring_active:
            try:
                # Collect system metrics
                metrics = {
                    "timestamp": datetime.now().isoformat(),
                    "cpu_percent": psutil.cpu_percent(interval=None),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_io": psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {},
                    "network_io": psutil.net_io_counters()._asdict(),
                    "processes": len(psutil.pids()),
                    "connections": len(psutil.net_connections()),
                    "load_average": psutil.getloadavg() if hasattr(psutil, "getloadavg") else [0, 0, 0]
                }

                self.monitoring_data.append(metrics)

                # Keep only last 1000 data points to prevent memory issues
                if len(self.monitoring_data) > 1000:
                    self.monitoring_data.pop(0)

                await asyncio.sleep(interval_seconds)

            except Exception as e:
                self.logger.error(f"Monitoring error: {str(e)}")
                await asyncio.sleep(interval_seconds)

    def stop_monitoring(self):
        """Stop system monitoring."""
        self.monitoring_active = False

    def get_peak_usage(self) -> Dict[str, float]:
        """Get peak resource usage during monitoring period."""
        if not self.monitoring_data:
            return {}

        return {
            "peak_cpu_percent": max(m["cpu_percent"] for m in self.monitoring_data),
            "peak_memory_percent": max(m["memory_percent"] for m in self.monitoring_data),
            "peak_processes": max(m["processes"] for m in self.monitoring_data),
            "peak_connections": max(m["connections"] for m in self.monitoring_data),
            "average_cpu": sum(m["cpu_percent"] for m in self.monitoring_data) / len(self.monitoring_data),
            "average_memory": sum(m["memory_percent"] for m in self.monitoring_data) / len(self.monitoring_data)
        }


class StressPatternGenerator:
    """Generate different load patterns for stress testing."""

    @staticmethod
    def linear_ramp(start_users: int, end_users: int, duration_seconds: int) -> List[Tuple[float, int]]:
        """Generate linear load ramp pattern."""
        steps = min(100, duration_seconds)
        step_duration = duration_seconds / steps
        user_increment = (end_users - start_users) / steps

        pattern = []
        for i in range(steps):
            timestamp = i * step_duration
            users = int(start_users + (i * user_increment))
            pattern.append((timestamp, users))

        return pattern

    @staticmethod
    def exponential_growth(start_users: int, end_users: int, duration_seconds: int) -> List[Tuple[float, int]]:
        """Generate exponential load growth pattern."""
        steps = min(100, duration_seconds)
        step_duration = duration_seconds / steps

        pattern = []
        for i in range(steps):
            timestamp = i * step_duration
            # Exponential formula: start_users * (end_users/start_users)^(i/steps)
            growth_factor = (end_users / start_users) ** (i / steps)
            users = int(start_users * growth_factor)
            pattern.append((timestamp, users))

        return pattern

    @staticmethod
    def spike_pattern(baseline_users: int, spike_users: int, duration_seconds: int,
                     spike_start_percent: float = 0.3, spike_duration_percent: float = 0.4) -> List[Tuple[float, int]]:
        """Generate load spike pattern."""
        steps = min(100, duration_seconds)
        step_duration = duration_seconds / steps

        spike_start_time = duration_seconds * spike_start_percent
        spike_end_time = spike_start_time + (duration_seconds * spike_duration_percent)

        pattern = []
        for i in range(steps):
            timestamp = i * step_duration
            if spike_start_time <= timestamp <= spike_end_time:
                users = spike_users
            else:
                users = baseline_users
            pattern.append((timestamp, users))

        return pattern

    @staticmethod
    def sawtooth_pattern(min_users: int, max_users: int, duration_seconds: int,
                        cycle_count: int = 3) -> List[Tuple[float, int]]:
        """Generate sawtooth load pattern."""
        steps = min(100, duration_seconds)
        step_duration = duration_seconds / steps
        cycle_duration = duration_seconds / cycle_count

        pattern = []
        for i in range(steps):
            timestamp = i * step_duration
            cycle_position = (timestamp % cycle_duration) / cycle_duration
            users = int(min_users + (max_users - min_users) * cycle_position)
            pattern.append((timestamp, users))

        return pattern


class StressTestingFramework:
    """Comprehensive stress testing framework."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
        self.system_monitor = SystemMonitor()
        self.pattern_generator = StressPatternGenerator()
        self.active_sessions: Dict[str, aiohttp.ClientSession] = {}
        self.test_results: List[StressTestResult] = []

    async def run_stress_test(self, config: StressTestConfiguration) -> StressTestResult:
        """Run comprehensive stress test based on configuration."""
        test_id = f"stress_test_{config.test_type.value}_{int(time.time())}"
        start_time = datetime.now()

        self.logger.info(f"Starting stress test {test_id}: {config.test_type.value}")

        # Start system monitoring
        monitor_task = asyncio.create_task(self.system_monitor.start_monitoring())

        try:
            # Generate load pattern
            load_pattern = self._generate_load_pattern(config)

            # Execute stress test
            test_result = await self._execute_stress_pattern(
                test_id, config, load_pattern, start_time
            )

            return test_result

        finally:
            # Stop monitoring
            self.system_monitor.stop_monitoring()
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass

    def _generate_load_pattern(self, config: StressTestConfiguration) -> List[Tuple[float, int]]:
        """Generate load pattern based on configuration."""
        if config.load_pattern == "linear":
            return self.pattern_generator.linear_ramp(
                10, config.max_concurrent_users, config.duration_seconds
            )
        elif config.load_pattern == "exponential":
            return self.pattern_generator.exponential_growth(
                10, config.max_concurrent_users, config.duration_seconds
            )
        elif config.load_pattern == "spike":
            return self.pattern_generator.spike_pattern(
                50, config.max_concurrent_users, config.duration_seconds
            )
        elif config.load_pattern == "sawtooth":
            return self.pattern_generator.sawtooth_pattern(
                20, config.max_concurrent_users, config.duration_seconds
            )
        else:
            # Default to linear
            return self.pattern_generator.linear_ramp(
                10, config.max_concurrent_users, config.duration_seconds
            )

    async def _execute_stress_pattern(self, test_id: str, config: StressTestConfiguration,
                                    load_pattern: List[Tuple[float, int]], start_time: datetime) -> StressTestResult:
        """Execute stress test following the specified load pattern."""
        peak_users = 0
        breaking_point_users = None
        failure_modes_triggered = []
        performance_metrics = {}
        error_patterns = {}

        current_user_tasks = []
        pattern_start = time.time()

        for i, (timestamp, target_users) in enumerate(load_pattern):
            # Wait until the right time for this pattern step
            elapsed = time.time() - pattern_start
            if elapsed < timestamp:
                await asyncio.sleep(timestamp - elapsed)

            # Adjust concurrent users to target level
            while len(current_user_tasks) < target_users:
                user_id = f"stress_user_{len(current_user_tasks)}"
                task = asyncio.create_task(self._run_stress_user_session(user_id, config))
                current_user_tasks.append(task)

            # Remove completed tasks
            current_user_tasks = [task for task in current_user_tasks if not task.done()]

            peak_users = max(peak_users, len(current_user_tasks))

            # Check for system breaking point
            if await self._check_system_breaking_point():
                if breaking_point_users is None:
                    breaking_point_users = len(current_user_tasks)
                    self.logger.warning(f"System breaking point detected at {breaking_point_users} users")

            # Collect real-time metrics
            current_metrics = await self._collect_real_time_metrics()
            performance_metrics[timestamp] = current_metrics

            # Check for failure modes
            detected_failures = await self._detect_failure_modes(current_metrics)
            failure_modes_triggered.extend(detected_failures)

            # Log progress
            if i % 10 == 0:
                self.logger.info(f"Stress test progress: {len(current_user_tasks)} active users, "
                               f"target: {target_users}")

        # Wait for remaining tasks to complete or timeout
        if current_user_tasks:
            try:
                await asyncio.wait_for(asyncio.gather(*current_user_tasks, return_exceptions=True), timeout=60)
            except asyncio.TimeoutError:
                self.logger.warning("Some user sessions did not complete within timeout")

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Calculate resilience score
        resilience_score = self._calculate_resilience_score(
            peak_users, breaking_point_users, failure_modes_triggered, performance_metrics
        )

        # Generate recommendations
        recommendations = self._generate_stress_test_recommendations(
            config, peak_users, breaking_point_users, failure_modes_triggered
        )

        return StressTestResult(
            test_id=test_id,
            test_type=config.test_type,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            peak_concurrent_users=peak_users,
            breaking_point_users=breaking_point_users,
            system_recovery_time=None,  # Would measure recovery after load removal
            performance_degradation=self._analyze_performance_degradation(performance_metrics),
            failure_modes_triggered=list(set(failure_modes_triggered)),
            resource_exhaustion=self.system_monitor.get_peak_usage(),
            error_patterns=error_patterns,
            resilience_score=resilience_score,
            recommendations=recommendations
        )

    async def _run_stress_user_session(self, user_id: str, config: StressTestConfiguration):
        """Run individual user session for stress testing."""
        session_timeout = aiohttp.ClientTimeout(total=10, connect=5)

        try:
            async with aiohttp.ClientSession(timeout=session_timeout) as session:
                # Aggressive request pattern for stress testing
                request_count = 0
                session_start = time.time()

                while (time.time() - session_start) < 30:  # 30 second sessions
                    try:
                        # Make rapid requests to stress the system
                        endpoints = [
                            "/api/property/search?address=test",
                            "/api/tax/calculate",
                            "/api/chat/message"
                        ]

                        endpoint = random.choice(endpoints)
                        start_time = time.time()

                        if endpoint == "/api/tax/calculate":
                            async with session.post(f"{self.base_url}{endpoint}", json={
                                "property_id": f"STRESS_{random.randint(1000, 9999)}",
                                "year": 2024
                            }) as response:
                                await response.read()
                        elif endpoint == "/api/chat/message":
                            async with session.post(f"{self.base_url}{endpoint}", json={
                                "message": f"Stress test message {request_count}",
                                "session_id": user_id
                            }) as response:
                                await response.read()
                        else:
                            async with session.get(f"{self.base_url}{endpoint}") as response:
                                await response.read()

                        request_count += 1

                        # Minimal think time for stress testing
                        await asyncio.sleep(0.1)

                    except Exception as e:
                        # Log errors but continue stress testing
                        self.logger.debug(f"Stress test request error: {str(e)}")
                        await asyncio.sleep(0.5)

        except Exception as e:
            self.logger.debug(f"Stress test session error: {str(e)}")

    async def _check_system_breaking_point(self) -> bool:
        """Check if system has reached breaking point."""
        try:
            # Check CPU usage
            cpu_usage = psutil.cpu_percent(interval=0.1)
            if cpu_usage > 95:
                return True

            # Check memory usage
            memory_usage = psutil.virtual_memory().percent
            if memory_usage > 95:
                return True

            # Check if system is responsive
            start_time = time.time()
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                    async with session.get(f"{self.base_url}/health") as response:
                        response_time = time.time() - start_time
                        if response_time > 10 or response.status >= 500:
                            return True
            except:
                return True

            return False

        except Exception:
            return True

    async def _collect_real_time_metrics(self) -> Dict[str, float]:
        """Collect real-time performance metrics."""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=None),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_io_read": psutil.disk_io_counters().read_bytes if psutil.disk_io_counters() else 0,
                "disk_io_write": psutil.disk_io_counters().write_bytes if psutil.disk_io_counters() else 0,
                "network_sent": psutil.net_io_counters().bytes_sent,
                "network_recv": psutil.net_io_counters().bytes_recv,
                "active_connections": len(psutil.net_connections()),
                "timestamp": time.time()
            }
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {str(e)}")
            return {"timestamp": time.time()}

    async def _detect_failure_modes(self, metrics: Dict[str, float]) -> List[FailureMode]:
        """Detect system failure modes based on metrics."""
        detected_failures = []

        # Memory exhaustion detection
        if metrics.get("memory_percent", 0) > 90:
            detected_failures.append(FailureMode.MEMORY_EXHAUSTION)

        # Connection pool exhaustion detection
        if metrics.get("active_connections", 0) > 1000:
            detected_failures.append(FailureMode.CONNECTION_POOL_EXHAUSTION)

        # CPU saturation detection
        if metrics.get("cpu_percent", 0) > 95:
            detected_failures.append(FailureMode.TIMEOUT_CASCADE)

        return detected_failures

    def _calculate_resilience_score(self, peak_users: int, breaking_point_users: Optional[int],
                                  failure_modes: List[FailureMode], metrics: Dict[float, Dict[str, float]]) -> float:
        """Calculate system resilience score (0-100)."""
        base_score = 100.0

        # Deduct points for early breaking point
        if breaking_point_users is not None:
            if breaking_point_users < 50:
                base_score -= 30
            elif breaking_point_users < 100:
                base_score -= 20
            elif breaking_point_users < 200:
                base_score -= 10

        # Deduct points for failure modes
        base_score -= len(failure_modes) * 10

        # Bonus points for handling high load
        if peak_users > 200:
            base_score += 10
        elif peak_users > 100:
            base_score += 5

        return max(0, min(100, base_score))

    def _analyze_performance_degradation(self, metrics: Dict[float, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
        """Analyze performance degradation over time."""
        if not metrics:
            return {}

        timestamps = sorted(metrics.keys())
        if len(timestamps) < 2:
            return {}

        baseline = metrics[timestamps[0]]
        peak = metrics[timestamps[-1]]

        degradation = {}
        for metric_name in baseline.keys():
            if metric_name == "timestamp":
                continue

            baseline_value = baseline.get(metric_name, 0)
            peak_value = peak.get(metric_name, 0)

            if baseline_value > 0:
                degradation_percent = ((peak_value - baseline_value) / baseline_value) * 100
                degradation[metric_name] = {
                    "baseline": baseline_value,
                    "peak": peak_value,
                    "degradation_percent": degradation_percent
                }

        return degradation

    def _generate_stress_test_recommendations(self, config: StressTestConfiguration,
                                            peak_users: int, breaking_point_users: Optional[int],
                                            failure_modes: List[FailureMode]) -> List[str]:
        """Generate recommendations based on stress test results."""
        recommendations = []

        if breaking_point_users is not None:
            if breaking_point_users < 100:
                recommendations.append("System breaking point too low - consider scaling infrastructure")
            recommendations.append(f"Breaking point at {breaking_point_users} users - plan capacity accordingly")

        if FailureMode.MEMORY_EXHAUSTION in failure_modes:
            recommendations.append("Memory optimization needed - implement caching and connection pooling")

        if FailureMode.CONNECTION_POOL_EXHAUSTION in failure_modes:
            recommendations.append("Connection pool tuning needed - increase pool size or implement connection reuse")

        if FailureMode.TIMEOUT_CASCADE in failure_modes:
            recommendations.append("Timeout configuration needed - implement circuit breakers and rate limiting")

        if peak_users > 200 and not failure_modes:
            recommendations.append("Excellent stress test performance - system handles high load well")

        if not recommendations:
            recommendations.append("System performed well under stress conditions")

        return recommendations

    async def run_chaos_engineering_test(self) -> Dict[str, Any]:
        """Run chaos engineering test with failure injection."""
        self.logger.info("Starting chaos engineering test")

        chaos_results = {
            "test_start": datetime.now().isoformat(),
            "failure_scenarios": [],
            "recovery_metrics": {},
            "overall_resilience": "unknown"
        }

        # Define chaos scenarios
        chaos_scenarios = [
            {"name": "high_latency_injection", "duration": 60},
            {"name": "random_error_injection", "duration": 60},
            {"name": "resource_exhaustion", "duration": 90}
        ]

        for scenario in chaos_scenarios:
            scenario_result = await self._run_chaos_scenario(scenario)
            chaos_results["failure_scenarios"].append(scenario_result)

        chaos_results["test_end"] = datetime.now().isoformat()
        return chaos_results

    async def _run_chaos_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run individual chaos engineering scenario."""
        self.logger.info(f"Running chaos scenario: {scenario['name']}")

        # This would implement specific chaos engineering scenarios
        # For demo purposes, we'll simulate the scenarios
        await asyncio.sleep(scenario['duration'])

        return {
            "scenario_name": scenario['name'],
            "duration": scenario['duration'],
            "impact_detected": True,
            "recovery_time": random.uniform(5, 30),
            "system_degradation": random.uniform(10, 50)
        }


# Example usage and testing
if __name__ == "__main__":
    async def run_stress_test_example():
        framework = StressTestingFramework("http://localhost:8000")

        # Configure stress test
        config = StressTestConfiguration(
            test_type=StressTestType.LOAD_SPIKE,
            duration_seconds=180,  # 3 minutes
            max_concurrent_users=150,
            load_pattern="spike",
            failure_injection=None,
            recovery_time_seconds=60,
            target_metrics={"response_time": 3.0, "error_rate": 5.0},
            chaos_engineering=False
        )

        print(f"Running stress test: {config.test_type.value}")
        result = await framework.run_stress_test(config)

        print(f"Stress test results:")
        print(f"  Peak users: {result.peak_concurrent_users}")
        print(f"  Breaking point: {result.breaking_point_users}")
        print(f"  Resilience score: {result.resilience_score:.1f}/100")
        print(f"  Failure modes: {[f.value for f in result.failure_modes_triggered]}")
        print(f"  Recommendations: {len(result.recommendations)}")
        for rec in result.recommendations[:3]:
            print(f"    - {rec}")

    # Run example
    asyncio.run(run_stress_test_example())