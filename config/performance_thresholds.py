"""Performance thresholds and benchmarks for production readiness validation."""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
from dotenv import load_dotenv

load_dotenv()


class PerformanceMetric(Enum):
    """Types of performance metrics."""
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    CONCURRENT_USERS = "concurrent_users"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DATABASE_QUERY_TIME = "database_query_time"
    API_LATENCY = "api_latency"
    ERROR_RATE = "error_rate"
    AVAILABILITY = "availability"


class LoadTestScenario(Enum):
    """Load testing scenarios."""
    BASELINE = "baseline"
    NORMAL_LOAD = "normal_load"
    PEAK_LOAD = "peak_load"
    STRESS_TEST = "stress_test"
    TAX_DEADLINE_SURGE = "tax_deadline_surge"
    SUSTAINED_LOAD = "sustained_load"


@dataclass
class PerformanceThreshold:
    """Performance threshold definition."""
    metric: PerformanceMetric
    scenario: LoadTestScenario
    target_value: float
    acceptable_value: float
    critical_value: float
    unit: str
    description: str


@dataclass
class LoadTestConfiguration:
    """Load test configuration parameters."""
    scenario: LoadTestScenario
    concurrent_users: int
    ramp_up_duration_seconds: int
    test_duration_seconds: int
    think_time_seconds: float
    user_scenarios: List[str]
    data_volume: str
    network_conditions: str


class PerformanceThresholds:
    """Performance thresholds and benchmarks configuration."""

    # Response Time Thresholds (seconds)
    API_RESPONSE_TIME_TARGET = float(os.getenv("API_RESPONSE_TIME_TARGET", "1.0"))
    API_RESPONSE_TIME_ACCEPTABLE = float(os.getenv("API_RESPONSE_TIME_ACCEPTABLE", "2.0"))
    API_RESPONSE_TIME_CRITICAL = float(os.getenv("API_RESPONSE_TIME_CRITICAL", "5.0"))

    # Database Query Thresholds (seconds)
    DB_QUERY_TIME_TARGET = float(os.getenv("DB_QUERY_TIME_TARGET", "0.5"))
    DB_QUERY_TIME_ACCEPTABLE = float(os.getenv("DB_QUERY_TIME_ACCEPTABLE", "1.0"))
    DB_QUERY_TIME_CRITICAL = float(os.getenv("DB_QUERY_TIME_CRITICAL", "3.0"))

    # Throughput Thresholds (requests per second)
    THROUGHPUT_TARGET = int(os.getenv("THROUGHPUT_TARGET", "100"))
    THROUGHPUT_ACCEPTABLE = int(os.getenv("THROUGHPUT_ACCEPTABLE", "50"))
    THROUGHPUT_CRITICAL = int(os.getenv("THROUGHPUT_CRITICAL", "20"))

    # Concurrent Users Thresholds
    CONCURRENT_USERS_TARGET = int(os.getenv("CONCURRENT_USERS_TARGET", "200"))
    CONCURRENT_USERS_ACCEPTABLE = int(os.getenv("CONCURRENT_USERS_ACCEPTABLE", "100"))
    CONCURRENT_USERS_CRITICAL = int(os.getenv("CONCURRENT_USERS_CRITICAL", "50"))

    # Resource Usage Thresholds (percentage)
    CPU_USAGE_TARGET = float(os.getenv("CPU_USAGE_TARGET", "70.0"))
    CPU_USAGE_ACCEPTABLE = float(os.getenv("CPU_USAGE_ACCEPTABLE", "85.0"))
    CPU_USAGE_CRITICAL = float(os.getenv("CPU_USAGE_CRITICAL", "95.0"))

    MEMORY_USAGE_TARGET = float(os.getenv("MEMORY_USAGE_TARGET", "75.0"))
    MEMORY_USAGE_ACCEPTABLE = float(os.getenv("MEMORY_USAGE_ACCEPTABLE", "90.0"))
    MEMORY_USAGE_CRITICAL = float(os.getenv("MEMORY_USAGE_CRITICAL", "98.0"))

    # Error Rate Thresholds (percentage)
    ERROR_RATE_TARGET = float(os.getenv("ERROR_RATE_TARGET", "0.1"))
    ERROR_RATE_ACCEPTABLE = float(os.getenv("ERROR_RATE_ACCEPTABLE", "1.0"))
    ERROR_RATE_CRITICAL = float(os.getenv("ERROR_RATE_CRITICAL", "5.0"))

    # Availability Thresholds (percentage)
    AVAILABILITY_TARGET = float(os.getenv("AVAILABILITY_TARGET", "99.9"))
    AVAILABILITY_ACCEPTABLE = float(os.getenv("AVAILABILITY_ACCEPTABLE", "99.5"))
    AVAILABILITY_CRITICAL = float(os.getenv("AVAILABILITY_CRITICAL", "95.0"))

    # Performance test scenarios configuration
    LOAD_TEST_SCENARIOS: Dict[LoadTestScenario, LoadTestConfiguration] = {
        LoadTestScenario.BASELINE: LoadTestConfiguration(
            scenario=LoadTestScenario.BASELINE,
            concurrent_users=10,
            ramp_up_duration_seconds=60,
            test_duration_seconds=300,  # 5 minutes
            think_time_seconds=2.0,
            user_scenarios=["property_inquiry", "general_information"],
            data_volume="small",
            network_conditions="ideal"
        ),
        LoadTestScenario.NORMAL_LOAD: LoadTestConfiguration(
            scenario=LoadTestScenario.NORMAL_LOAD,
            concurrent_users=50,
            ramp_up_duration_seconds=120,
            test_duration_seconds=600,  # 10 minutes
            think_time_seconds=3.0,
            user_scenarios=["property_inquiry", "payment_processing", "exemption_application"],
            data_volume="medium",
            network_conditions="realistic"
        ),
        LoadTestScenario.PEAK_LOAD: LoadTestConfiguration(
            scenario=LoadTestScenario.PEAK_LOAD,
            concurrent_users=100,
            ramp_up_duration_seconds=180,
            test_duration_seconds=900,  # 15 minutes
            think_time_seconds=1.5,
            user_scenarios=["property_inquiry", "payment_processing", "exemption_application", "assessment_appeal"],
            data_volume="large",
            network_conditions="realistic"
        ),
        LoadTestScenario.STRESS_TEST: LoadTestConfiguration(
            scenario=LoadTestScenario.STRESS_TEST,
            concurrent_users=200,
            ramp_up_duration_seconds=300,
            test_duration_seconds=1800,  # 30 minutes
            think_time_seconds=1.0,
            user_scenarios=["all_scenarios"],
            data_volume="large",
            network_conditions="challenging"
        ),
        LoadTestScenario.TAX_DEADLINE_SURGE: LoadTestConfiguration(
            scenario=LoadTestScenario.TAX_DEADLINE_SURGE,
            concurrent_users=300,
            ramp_up_duration_seconds=600,
            test_duration_seconds=3600,  # 1 hour
            think_time_seconds=0.5,
            user_scenarios=["payment_processing", "property_inquiry", "exemption_application"],
            data_volume="xlarge",
            network_conditions="challenging"
        ),
        LoadTestScenario.SUSTAINED_LOAD: LoadTestConfiguration(
            scenario=LoadTestScenario.SUSTAINED_LOAD,
            concurrent_users=75,
            ramp_up_duration_seconds=300,
            test_duration_seconds=7200,  # 2 hours
            think_time_seconds=2.5,
            user_scenarios=["property_inquiry", "payment_processing", "general_information"],
            data_volume="large",
            network_conditions="realistic"
        )
    }

    # Performance thresholds by scenario
    PERFORMANCE_THRESHOLDS: List[PerformanceThreshold] = [
        # Response Time Thresholds
        PerformanceThreshold(
            metric=PerformanceMetric.RESPONSE_TIME,
            scenario=LoadTestScenario.BASELINE,
            target_value=0.5,
            acceptable_value=1.0,
            critical_value=2.0,
            unit="seconds",
            description="API response time under baseline load"
        ),
        PerformanceThreshold(
            metric=PerformanceMetric.RESPONSE_TIME,
            scenario=LoadTestScenario.NORMAL_LOAD,
            target_value=1.0,
            acceptable_value=2.0,
            critical_value=3.0,
            unit="seconds",
            description="API response time under normal load"
        ),
        PerformanceThreshold(
            metric=PerformanceMetric.RESPONSE_TIME,
            scenario=LoadTestScenario.PEAK_LOAD,
            target_value=1.5,
            acceptable_value=2.5,
            critical_value=4.0,
            unit="seconds",
            description="API response time under peak load"
        ),
        PerformanceThreshold(
            metric=PerformanceMetric.RESPONSE_TIME,
            scenario=LoadTestScenario.TAX_DEADLINE_SURGE,
            target_value=2.0,
            acceptable_value=3.0,
            critical_value=5.0,
            unit="seconds",
            description="API response time during tax deadline surge"
        ),

        # Throughput Thresholds
        PerformanceThreshold(
            metric=PerformanceMetric.THROUGHPUT,
            scenario=LoadTestScenario.NORMAL_LOAD,
            target_value=100.0,
            acceptable_value=75.0,
            critical_value=50.0,
            unit="requests/second",
            description="System throughput under normal load"
        ),
        PerformanceThreshold(
            metric=PerformanceMetric.THROUGHPUT,
            scenario=LoadTestScenario.PEAK_LOAD,
            target_value=150.0,
            acceptable_value=100.0,
            critical_value=75.0,
            unit="requests/second",
            description="System throughput under peak load"
        ),

        # Error Rate Thresholds
        PerformanceThreshold(
            metric=PerformanceMetric.ERROR_RATE,
            scenario=LoadTestScenario.NORMAL_LOAD,
            target_value=0.1,
            acceptable_value=0.5,
            critical_value=2.0,
            unit="percentage",
            description="Error rate under normal load"
        ),
        PerformanceThreshold(
            metric=PerformanceMetric.ERROR_RATE,
            scenario=LoadTestScenario.STRESS_TEST,
            target_value=0.5,
            acceptable_value=2.0,
            critical_value=5.0,
            unit="percentage",
            description="Error rate under stress conditions"
        ),

        # Resource Usage Thresholds
        PerformanceThreshold(
            metric=PerformanceMetric.CPU_USAGE,
            scenario=LoadTestScenario.PEAK_LOAD,
            target_value=70.0,
            acceptable_value=85.0,
            critical_value=95.0,
            unit="percentage",
            description="CPU usage under peak load"
        ),
        PerformanceThreshold(
            metric=PerformanceMetric.MEMORY_USAGE,
            scenario=LoadTestScenario.PEAK_LOAD,
            target_value=75.0,
            acceptable_value=90.0,
            critical_value=98.0,
            unit="percentage",
            description="Memory usage under peak load"
        ),

        # Database Performance Thresholds
        PerformanceThreshold(
            metric=PerformanceMetric.DATABASE_QUERY_TIME,
            scenario=LoadTestScenario.NORMAL_LOAD,
            target_value=0.3,
            acceptable_value=0.8,
            critical_value=2.0,
            unit="seconds",
            description="Database query time under normal load"
        ),
        PerformanceThreshold(
            metric=PerformanceMetric.DATABASE_QUERY_TIME,
            scenario=LoadTestScenario.PEAK_LOAD,
            target_value=0.5,
            acceptable_value=1.0,
            critical_value=3.0,
            unit="seconds",
            description="Database query time under peak load"
        )
    ]

    # Property Tax Specific Scenarios
    PROPERTY_TAX_SCENARIOS = {
        "property_inquiry": {
            "weight": 40,  # 40% of traffic
            "endpoints": ["/api/property/search", "/api/property/details", "/api/tax/calculate"],
            "think_time": 3.0,
            "session_duration": 300  # 5 minutes
        },
        "payment_processing": {
            "weight": 25,  # 25% of traffic
            "endpoints": ["/api/property/details", "/api/payment/calculate", "/api/payment/process"],
            "think_time": 5.0,
            "session_duration": 600  # 10 minutes
        },
        "exemption_application": {
            "weight": 15,  # 15% of traffic
            "endpoints": ["/api/exemption/eligibility", "/api/exemption/apply", "/api/exemption/status"],
            "think_time": 10.0,
            "session_duration": 900  # 15 minutes
        },
        "assessment_appeal": {
            "weight": 10,  # 10% of traffic
            "endpoints": ["/api/assessment/details", "/api/appeal/submit", "/api/appeal/status"],
            "think_time": 15.0,
            "session_duration": 1200  # 20 minutes
        },
        "general_information": {
            "weight": 10,  # 10% of traffic
            "endpoints": ["/api/info/rates", "/api/info/deadlines", "/api/info/contact"],
            "think_time": 2.0,
            "session_duration": 180  # 3 minutes
        }
    }

    # API Endpoint Performance Requirements
    ENDPOINT_PERFORMANCE_REQUIREMENTS = {
        "/api/property/search": {"max_response_time": 1.0, "target_response_time": 0.5},
        "/api/property/details": {"max_response_time": 1.5, "target_response_time": 0.8},
        "/api/tax/calculate": {"max_response_time": 2.0, "target_response_time": 1.0},
        "/api/payment/process": {"max_response_time": 3.0, "target_response_time": 2.0},
        "/api/exemption/apply": {"max_response_time": 2.5, "target_response_time": 1.5},
        "/api/appeal/submit": {"max_response_time": 3.0, "target_response_time": 2.0},
        "/api/chat/message": {"max_response_time": 2.0, "target_response_time": 1.0},
        "/api/chat/history": {"max_response_time": 1.0, "target_response_time": 0.5}
    }

    @classmethod
    def get_threshold(cls, metric: PerformanceMetric, scenario: LoadTestScenario) -> Optional[PerformanceThreshold]:
        """Get performance threshold for specific metric and scenario."""
        for threshold in cls.PERFORMANCE_THRESHOLDS:
            if threshold.metric == metric and threshold.scenario == scenario:
                return threshold
        return None

    @classmethod
    def get_load_test_config(cls, scenario: LoadTestScenario) -> Optional[LoadTestConfiguration]:
        """Get load test configuration for scenario."""
        return cls.LOAD_TEST_SCENARIOS.get(scenario)

    @classmethod
    def validate_performance_result(cls, metric: PerformanceMetric, scenario: LoadTestScenario,
                                  measured_value: float) -> Dict[str, any]:
        """Validate performance result against thresholds."""
        threshold = cls.get_threshold(metric, scenario)
        if not threshold:
            return {"status": "unknown", "message": f"No threshold defined for {metric.value} in {scenario.value}"}

        if measured_value <= threshold.target_value:
            return {"status": "excellent", "message": "Meets target performance", "threshold": "target"}
        elif measured_value <= threshold.acceptable_value:
            return {"status": "acceptable", "message": "Meets acceptable performance", "threshold": "acceptable"}
        elif measured_value <= threshold.critical_value:
            return {"status": "warning", "message": "Performance degraded but within critical limits", "threshold": "critical"}
        else:
            return {"status": "critical", "message": "Performance exceeds critical thresholds", "threshold": "exceeded"}

    @classmethod
    def get_scenario_configuration_summary(cls) -> Dict[str, any]:
        """Get summary of all load test scenario configurations."""
        return {
            "total_scenarios": len(cls.LOAD_TEST_SCENARIOS),
            "scenarios": {
                scenario.value: {
                    "concurrent_users": config.concurrent_users,
                    "test_duration_minutes": config.test_duration_seconds / 60,
                    "user_scenarios": config.user_scenarios,
                    "data_volume": config.data_volume
                }
                for scenario, config in cls.LOAD_TEST_SCENARIOS.items()
            },
            "total_thresholds": len(cls.PERFORMANCE_THRESHOLDS),
            "metrics_covered": list(set(threshold.metric.value for threshold in cls.PERFORMANCE_THRESHOLDS)),
            "property_tax_scenarios": len(cls.PROPERTY_TAX_SCENARIOS),
            "monitored_endpoints": len(cls.ENDPOINT_PERFORMANCE_REQUIREMENTS)
        }


# Global performance thresholds instance
performance_thresholds = PerformanceThresholds()

if __name__ == "__main__":
    print("Performance Thresholds Configuration Summary:")
    summary = performance_thresholds.get_scenario_configuration_summary()

    print(f"\nLoad Test Scenarios: {summary['total_scenarios']}")
    for scenario_name, config in summary['scenarios'].items():
        print(f"  {scenario_name}: {config['concurrent_users']} users, {config['test_duration_minutes']} min")

    print(f"\nPerformance Thresholds: {summary['total_thresholds']}")
    print(f"Metrics Covered: {', '.join(summary['metrics_covered'])}")

    print(f"\nProperty Tax Scenarios: {summary['property_tax_scenarios']}")
    for scenario, details in performance_thresholds.PROPERTY_TAX_SCENARIOS.items():
        print(f"  {scenario}: {details['weight']}% of traffic")

    print(f"\nMonitored Endpoints: {summary['monitored_endpoints']}")

    # Test threshold validation
    print("\nExample Threshold Validation:")
    result = performance_thresholds.validate_performance_result(
        PerformanceMetric.RESPONSE_TIME,
        LoadTestScenario.NORMAL_LOAD,
        1.5
    )
    print(f"Response time 1.5s under normal load: {result['status']} - {result['message']}")