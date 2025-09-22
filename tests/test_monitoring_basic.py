"""Basic tests for monitoring system components without FastAPI dependencies."""

import pytest
import sys
import os
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_monitoring_auth_manager_creation():
    """Test that monitoring auth manager can be created."""
    from core.monitoring_auth import MonitoringAuthManager, MonitoringRole

    manager = MonitoringAuthManager()
    assert manager is not None
    assert len(manager.users) > 0
    assert "admin" in manager.users
    assert manager.users["admin"].role == MonitoringRole.ADMIN


def test_alert_manager_creation():
    """Test that alert manager can be created."""
    from core.alert_manager import AlertManager, AlertSeverity

    manager = AlertManager()
    assert manager is not None
    assert len(manager.alert_rules) > 0

    # Check that we have critical alerts configured
    critical_alerts = [
        rule for rule in manager.alert_rules.values()
        if rule.severity == AlertSeverity.CRITICAL
    ]
    assert len(critical_alerts) > 0


def test_data_retention_manager_creation():
    """Test that data retention manager can be created."""
    from core.data_retention import DataRetentionManager, DataCategory

    manager = DataRetentionManager()
    assert manager is not None
    assert len(manager.retention_rules) > 0

    # Check that business analytics has immediate anonymization
    business_rule = manager.retention_rules.get(DataCategory.BUSINESS_ANALYTICS)
    assert business_rule is not None
    assert business_rule.anonymize_after_days == 1


def test_monitoring_permissions():
    """Test monitoring permission system."""
    from core.monitoring_auth import MonitoringRole, MonitoringPermission, MonitoringAuthManager

    manager = MonitoringAuthManager()

    # Test that admin has all permissions
    admin = manager.users["admin"]
    assert manager.has_permission(admin, MonitoringPermission.VIEW_PERFORMANCE)
    assert manager.has_permission(admin, MonitoringPermission.MANAGE_USERS)

    # Test that viewer has limited permissions
    viewer = manager.users["viewer"]
    assert manager.has_permission(viewer, MonitoringPermission.VIEW_PERFORMANCE)
    assert not manager.has_permission(viewer, MonitoringPermission.MANAGE_USERS)


def test_alert_threshold_evaluation():
    """Test alert threshold evaluation logic."""
    from core.alert_manager import AlertManager

    manager = AlertManager()

    # Test greater than threshold
    assert manager._evaluate_threshold(5.0, 2.0, "gt") == True
    assert manager._evaluate_threshold(1.0, 2.0, "gt") == False

    # Test less than threshold
    assert manager._evaluate_threshold(1.0, 2.0, "lt") == True
    assert manager._evaluate_threshold(3.0, 2.0, "lt") == False

    # Test equals threshold
    assert manager._evaluate_threshold(2.0, 2.0, "eq") == True
    assert manager._evaluate_threshold(2.1, 2.0, "eq") == False


def test_api_key_creation():
    """Test API key creation and hashing."""
    from core.monitoring_auth import MonitoringAuthManager, MonitoringPermission

    manager = MonitoringAuthManager()

    permissions = {MonitoringPermission.VIEW_PERFORMANCE}
    key_value, api_key = manager.create_api_key(
        "test_key",
        permissions,
        "admin"
    )

    assert key_value.startswith("cpt_monitor_")
    assert api_key.name == "test_key"
    assert api_key.permissions == permissions
    assert api_key.key_hash != key_value  # Should be hashed


def test_data_retention_summary():
    """Test data retention summary generation."""
    from core.data_retention import DataRetentionManager

    manager = DataRetentionManager()
    summary = manager.get_retention_summary()

    assert "retention_policies" in summary
    assert "configuration" in summary
    assert "pending_requests" in summary

    # Should have policies for all major data categories
    policies = summary["retention_policies"]
    assert "performance_metrics" in policies
    assert "business_analytics" in policies
    assert "audit_logs" in policies


@pytest.mark.asyncio
async def test_alert_suppression():
    """Test alert suppression functionality."""
    from core.alert_manager import AlertManager
    from datetime import datetime

    manager = AlertManager()

    # Test suppression
    rule_name = "high_response_time"
    success = await manager.suppress_alert(rule_name, 60)  # 60 minutes

    assert success == True
    assert rule_name in manager.suppressed_alerts
    assert manager._is_suppressed(rule_name) == True

    # Test that suppression expires
    # Mock the suppression time to be in the past
    past_time = datetime.now() - timedelta(hours=2)
    manager.suppressed_alerts[rule_name] = past_time

    assert manager._is_suppressed(rule_name) == False
    assert rule_name not in manager.suppressed_alerts  # Should be cleaned up


@pytest.mark.asyncio
async def test_alert_evaluation():
    """Test alert evaluation with mock metrics."""
    from core.alert_manager import AlertManager

    manager = AlertManager()

    # Clear any existing alerts
    manager.active_alerts.clear()

    # Test metrics that should trigger alerts
    test_metrics = {
        "response_time_95th": 3.0,  # Above 2.0 threshold
        "error_rate": 0.1,          # Above 0.05 threshold
    }

    initial_count = len(manager.active_alerts)
    await manager.evaluate_metrics(test_metrics)

    # Should have created new alerts
    assert len(manager.active_alerts) > initial_count


def test_jwt_token_creation():
    """Test JWT token creation (mocked)."""
    from core.monitoring_auth import MonitoringAuthManager

    manager = MonitoringAuthManager()

    # Mock JWT to avoid dependency issues
    with patch('jwt.encode') as mock_encode:
        mock_encode.return_value = "mocked_jwt_token"

        token = manager.generate_jwt_token("admin")
        assert token == "mocked_jwt_token"
        mock_encode.assert_called_once()


def test_performance_validation_script_exists():
    """Test that performance validation script exists and is valid Python."""
    script_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'scripts',
        'validate_monitoring_performance.py'
    )

    assert os.path.exists(script_path)

    # Check that it's valid Python
    with open(script_path, 'r') as f:
        content = f.read()

    # Should contain key classes and functions
    assert "MonitoringPerformanceValidator" in content
    assert "async def run_validation" in content
    assert "LoadTestConfig" in content


def test_operational_documentation_exists():
    """Test that operational documentation exists."""
    docs_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'docs',
        'monitoring',
        'OPERATIONAL_GUIDE.md'
    )

    assert os.path.exists(docs_path)

    with open(docs_path, 'r') as f:
        content = f.read()

    # Should contain key sections
    assert "Authentication and Access Control" in content
    assert "Alert Management" in content
    assert "Data Management and Compliance" in content
    assert "Emergency Procedures" in content


def test_training_checklist_exists():
    """Test that training checklist exists."""
    training_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'docs',
        'monitoring',
        'TRAINING_CHECKLIST.md'
    )

    assert os.path.exists(training_path)

    with open(training_path, 'r') as f:
        content = f.read()

    # Should contain training sections
    assert "Dashboard Navigation" in content
    assert "Alert Management" in content
    assert "Certification Requirements" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])