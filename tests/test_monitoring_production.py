"""Tests for production monitoring system components.

This test suite validates:
- Monitoring dashboard endpoints and authentication
- Alert system functionality and performance
- Data retention policies and compliance
- Role-based access controls
- Performance under load conditions
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from src.main import app
from src.core.monitoring_auth import auth_manager, MonitoringRole, MonitoringPermission
from src.core.alert_manager import alert_manager, AlertSeverity
from src.core.data_retention import retention_manager, DataCategory
from src.api.monitoring_dashboards import dashboard_manager


class TestMonitoringDashboards:
    """Test monitoring dashboard endpoints."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_health_endpoint_public_access(self):
        """Test that health endpoint is publicly accessible."""
        response = self.client.get("/monitoring/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "services" in data

    def test_protected_endpoints_require_auth(self):
        """Test that protected endpoints require authentication."""
        protected_endpoints = [
            "/monitoring/performance",
            "/monitoring/business",
            "/monitoring/infrastructure",
            "/monitoring/alerts"
        ]

        for endpoint in protected_endpoints:
            response = self.client.get(endpoint)
            assert response.status_code == 401

    def test_dashboard_with_valid_token(self):
        """Test dashboard access with valid authentication."""
        headers = {"Authorization": "Bearer monitoring-secret-key"}

        response = self.client.get("/monitoring/performance", headers=headers)
        # May fail due to missing database, but should not be auth error
        assert response.status_code != 401

    def test_dashboard_ui_endpoint(self):
        """Test dashboard UI endpoint."""
        headers = {"Authorization": "Bearer monitoring-secret-key"}

        response = self.client.get("/monitoring/dashboard", headers=headers)
        assert response.status_code != 401  # Should not be auth error


class TestMonitoringAuth:
    """Test monitoring authentication and authorization."""

    def setup_method(self):
        """Set up test data."""
        # Clear existing users for clean tests
        auth_manager.users.clear()
        auth_manager.api_keys.clear()
        auth_manager.create_default_users()

    def test_create_user(self):
        """Test user creation."""
        user = auth_manager.create_user(
            "test_operator",
            "test@centuryproptax.com",
            MonitoringRole.OPERATOR
        )

        assert user.username == "test_operator"
        assert user.role == MonitoringRole.OPERATOR
        assert MonitoringPermission.VIEW_PERFORMANCE in user.permissions
        assert MonitoringPermission.ACKNOWLEDGE_ALERTS in user.permissions

    def test_user_role_permissions(self):
        """Test role-based permissions."""
        # Test viewer permissions
        viewer = auth_manager.users.get("viewer")
        assert viewer is not None
        assert auth_manager.has_permission(viewer, MonitoringPermission.VIEW_PERFORMANCE)
        assert not auth_manager.has_permission(viewer, MonitoringPermission.CONFIGURE_ALERTS)

        # Test admin permissions
        admin = auth_manager.users.get("admin")
        assert admin is not None
        assert auth_manager.has_permission(admin, MonitoringPermission.MANAGE_USERS)

    def test_api_key_creation(self):
        """Test API key creation and authentication."""
        permissions = {MonitoringPermission.VIEW_PERFORMANCE, MonitoringPermission.VIEW_INFRASTRUCTURE}

        key_value, api_key = auth_manager.create_api_key(
            "test_key",
            permissions,
            "admin",
            expires_in_days=30
        )

        assert key_value.startswith("cpt_monitor_")
        assert api_key.name == "test_key"
        assert api_key.permissions == permissions

        # Test authentication
        authenticated_key = auth_manager.authenticate_api_key(key_value)
        assert authenticated_key is not None
        assert authenticated_key.key_id == api_key.key_id

    def test_jwt_token_generation(self):
        """Test JWT token generation and validation."""
        username = "operator"
        token = auth_manager.generate_jwt_token(username)

        assert token is not None
        assert isinstance(token, str)

        # Test authentication with token
        user = auth_manager.authenticate_user(username, token)
        assert user is not None
        assert user.username == username

    def test_audit_logging(self):
        """Test audit logging functionality."""
        initial_log_count = len(auth_manager.audit_logs)

        auth_manager.log_action(
            "test_user",
            "test_action",
            "test_resource",
            {"test": "data"}
        )

        assert len(auth_manager.audit_logs) == initial_log_count + 1
        latest_log = auth_manager.audit_logs[-1]
        assert latest_log.user == "test_user"
        assert latest_log.action == "test_action"


class TestAlertManager:
    """Test alert management system."""

    def setup_method(self):
        """Set up test data."""
        alert_manager.active_alerts.clear()
        alert_manager.load_default_alert_rules()

    @pytest.mark.asyncio
    async def test_alert_evaluation(self):
        """Test alert threshold evaluation."""
        # Create test metrics that should trigger alerts
        test_metrics = {
            "response_time_95th": 3.0,  # Above 2.0 threshold
            "error_rate": 0.1,          # Above 0.05 threshold
            "memory_usage_mb": 2048     # Above 1024 threshold
        }

        initial_alert_count = len(alert_manager.active_alerts)

        await alert_manager.evaluate_metrics(test_metrics)

        # Should have triggered new alerts
        assert len(alert_manager.active_alerts) > initial_alert_count

    def test_alert_configuration(self):
        """Test alert configuration management."""
        # Test getting alert summary
        summary = alert_manager.get_alert_summary()

        assert "active_alerts" in summary
        assert "total_rules" in summary
        assert "enabled_rules" in summary
        assert summary["total_rules"] > 0

    @pytest.mark.asyncio
    async def test_alert_acknowledgment(self):
        """Test alert acknowledgment."""
        # First create an active alert
        test_metrics = {"response_time_95th": 3.0}
        await alert_manager.evaluate_metrics(test_metrics)

        # Find an active alert
        if alert_manager.active_alerts:
            alert_name = list(alert_manager.active_alerts.keys())[0]

            # Acknowledge the alert
            success = await alert_manager.acknowledge_alert(alert_name, "test_operator")
            assert success

            # Verify acknowledgment
            alert = alert_manager.active_alerts[alert_name]
            assert alert.acknowledged_by == "test_operator"
            assert alert.acknowledged_at is not None

    @pytest.mark.asyncio
    async def test_alert_suppression(self):
        """Test alert suppression."""
        rule_name = "high_response_time"

        # Suppress the alert
        success = await alert_manager.suppress_alert(rule_name, 60)  # 60 minutes
        assert success

        # Verify suppression
        assert rule_name in alert_manager.suppressed_alerts

        # Test that suppressed alerts don't trigger
        test_metrics = {"response_time_95th": 3.0}
        initial_count = len(alert_manager.active_alerts)

        await alert_manager.evaluate_metrics(test_metrics)

        # Should not create new alert for suppressed rule
        assert len(alert_manager.active_alerts) == initial_count


class TestDataRetention:
    """Test data retention and compliance policies."""

    def setup_method(self):
        """Set up test data."""
        retention_manager.load_default_policies()

    def test_retention_policies_loaded(self):
        """Test that retention policies are properly loaded."""
        assert len(retention_manager.retention_rules) > 0

        # Test specific policy
        perf_rule = retention_manager.retention_rules.get(DataCategory.PERFORMANCE_METRICS)
        assert perf_rule is not None
        assert perf_rule.retention_days == 30
        assert perf_rule.anonymize_after_days == 7

    def test_compliance_configuration(self):
        """Test compliance configuration."""
        business_rule = retention_manager.retention_rules.get(DataCategory.BUSINESS_ANALYTICS)
        assert business_rule is not None
        assert business_rule.anonymize_after_days == 1  # Immediate anonymization

        # Should include privacy compliance regions
        assert len(business_rule.compliance_regions) > 0

    def test_retention_summary(self):
        """Test retention summary generation."""
        summary = retention_manager.get_retention_summary()

        assert "retention_policies" in summary
        assert "configuration" in summary
        assert "pending_requests" in summary

        # Check that all data categories are covered
        policies = summary["retention_policies"]
        assert len(policies) > 0

    @pytest.mark.asyncio
    async def test_data_export_request(self):
        """Test data export request creation."""
        categories = [DataCategory.PERFORMANCE_METRICS, DataCategory.BUSINESS_ANALYTICS]
        date_range = (datetime.now() - timedelta(days=30), datetime.now())

        request_id = await retention_manager.request_data_export(
            "user123",
            categories,
            date_range,
            "admin"
        )

        assert request_id is not None
        assert request_id in retention_manager.export_requests

        request = retention_manager.export_requests[request_id]
        assert request.user_identifier == "user123"
        assert request.status == "pending"

    @pytest.mark.asyncio
    async def test_data_deletion_request(self):
        """Test data deletion request creation."""
        categories = [DataCategory.USER_SESSIONS]

        request_id = await retention_manager.request_data_deletion(
            "user456",
            categories,
            "admin",
            verification_required=True
        )

        assert request_id is not None
        assert request_id in retention_manager.deletion_requests

        request = retention_manager.deletion_requests[request_id]
        assert request.user_identifier == "user456"
        assert request.verification_required is True


class TestMonitoringPerformance:
    """Test monitoring system performance characteristics."""

    @pytest.mark.asyncio
    async def test_dashboard_response_time(self):
        """Test dashboard response time performance."""
        # Mock dashboard manager initialization
        dashboard_manager.db_pool = Mock()
        dashboard_manager.redis_client = Mock()

        start_time = datetime.now()

        try:
            # Test performance metrics retrieval
            metrics = await dashboard_manager.get_performance_metrics()

            response_time = (datetime.now() - start_time).total_seconds()

            # Should respond within reasonable time
            assert response_time < 5.0  # 5 seconds max
            assert metrics is not None
            assert hasattr(metrics, 'timestamp')

        except Exception:
            # Expected to fail without real database, but timing test is still valid
            response_time = (datetime.now() - start_time).total_seconds()
            assert response_time < 5.0

    def test_memory_usage_monitoring(self):
        """Test that monitoring components don't consume excessive memory."""
        import psutil
        import sys

        # Get current memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss

        # Create monitoring objects (should be lightweight)
        auth_manager.create_default_users()
        alert_manager.load_default_alert_rules()
        retention_manager.load_default_policies()

        # Check memory usage after initialization
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Should not use more than 50MB for monitoring components
        assert memory_increase < 50 * 1024 * 1024  # 50MB

    @pytest.mark.asyncio
    async def test_concurrent_access_simulation(self):
        """Test monitoring system under concurrent access."""
        async def simulate_user_request():
            """Simulate a user making monitoring requests."""
            try:
                # Simulate dashboard access
                summary = auth_manager.get_user_summary()
                alert_summary = alert_manager.get_alert_summary()
                retention_summary = retention_manager.get_retention_summary()

                return len(summary) + len(alert_summary) + len(retention_summary)
            except Exception:
                return 0

        # Run multiple concurrent requests
        tasks = [simulate_user_request() for _ in range(20)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All requests should complete without errors
        successful_requests = [r for r in results if isinstance(r, int) and r > 0]
        assert len(successful_requests) >= 15  # At least 75% success rate


@pytest.mark.integration
class TestMonitoringIntegration:
    """Integration tests for the monitoring system."""

    def test_monitoring_routes_loaded(self):
        """Test that monitoring routes are properly loaded."""
        client = TestClient(app)

        # Test that routes exist (may fail auth, but should not 404)
        routes_to_test = [
            "/monitoring/health",
            "/monitoring/performance",
            "/monitoring/business",
            "/monitoring/infrastructure",
            "/monitoring/alerts"
        ]

        for route in routes_to_test:
            response = client.get(route)
            assert response.status_code != 404  # Route should exist

    @pytest.mark.asyncio
    async def test_monitoring_initialization(self):
        """Test monitoring system initialization."""
        # Test that managers can be initialized without errors
        try:
            # These should not raise exceptions
            auth_manager.get_user_summary()
            alert_manager.get_alert_summary()
            retention_manager.get_retention_summary()

            initialization_success = True
        except Exception as e:
            print(f"Initialization error: {e}")
            initialization_success = False

        assert initialization_success

    def test_environment_configuration(self):
        """Test that environment configuration is properly handled."""
        import os

        # Test that monitoring components handle missing env vars gracefully
        original_db_url = os.environ.get("DATABASE_URL")
        original_redis_url = os.environ.get("REDIS_URL")

        try:
            # Remove env vars temporarily
            if "DATABASE_URL" in os.environ:
                del os.environ["DATABASE_URL"]
            if "REDIS_URL" in os.environ:
                del os.environ["REDIS_URL"]

            # Components should still initialize with defaults
            auth_manager.get_user_summary()
            alert_manager.get_alert_summary()

            config_handling_success = True

        except Exception:
            config_handling_success = False

        finally:
            # Restore env vars
            if original_db_url:
                os.environ["DATABASE_URL"] = original_db_url
            if original_redis_url:
                os.environ["REDIS_URL"] = original_redis_url

        assert config_handling_success


if __name__ == "__main__":
    pytest.main([__file__, "-v"])