"""Production alert management system with multi-channel notifications.

This module provides:
- Alert configuration and threshold management
- Multi-channel notification delivery (email, Slack, webhook)
- Alert escalation procedures and on-call integration
- Alert suppression and acknowledgment workflow
- Alert history and analytics
"""

import asyncio
import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import os
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class AlertStatus(Enum):
    """Alert status states."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

class NotificationChannel(Enum):
    """Available notification channels."""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"

@dataclass
class AlertRule:
    """Alert rule configuration."""
    name: str
    metric: str
    threshold: float
    operator: str  # "gt", "lt", "eq", "ne"
    severity: AlertSeverity
    enabled: bool
    notification_channels: List[NotificationChannel]
    escalation_minutes: int = 15
    max_escalations: int = 3
    suppression_duration: int = 60  # minutes
    description: str = ""
    runbook_url: str = ""

@dataclass
class AlertInstance:
    """Active alert instance."""
    rule_name: str
    metric: str
    current_value: float
    threshold: float
    severity: AlertSeverity
    status: AlertStatus
    created_at: datetime
    updated_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    escalation_level: int = 0
    notification_count: int = 0

class NotificationConfig:
    """Notification channel configuration."""

    def __init__(self):
        # Email configuration
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.email_from = os.getenv("ALERT_EMAIL_FROM", "alerts@centuryproptax.com")
        self.email_to = os.getenv("ALERT_EMAIL_TO", "ops@centuryproptax.com").split(",")

        # Slack configuration
        self.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
        self.slack_channel = os.getenv("SLACK_CHANNEL", "#alerts")

        # Webhook configuration
        self.webhook_url = os.getenv("ALERT_WEBHOOK_URL", "")
        self.webhook_secret = os.getenv("ALERT_WEBHOOK_SECRET", "")

        # SMS configuration (optional)
        self.sms_api_key = os.getenv("SMS_API_KEY", "")
        self.sms_phone_numbers = os.getenv("ALERT_SMS_NUMBERS", "").split(",")

class AlertManager:
    """Production alert management system."""

    def __init__(self, config_file: Optional[str] = None):
        self.config = NotificationConfig()
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, AlertInstance] = {}
        self.alert_history: List[AlertInstance] = []
        self.suppressed_alerts: Dict[str, datetime] = {}

        # Load alert rules from configuration
        if config_file:
            self.load_alert_rules(config_file)
        else:
            self.load_default_alert_rules()

    def load_default_alert_rules(self):
        """Load default production alert rules."""
        default_rules = [
            AlertRule(
                name="high_response_time",
                metric="response_time_95th",
                threshold=2.0,
                operator="gt",
                severity=AlertSeverity.WARNING,
                enabled=True,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
                escalation_minutes=10,
                description="95th percentile response time exceeds 2 seconds",
                runbook_url="https://docs.centuryproptax.com/runbooks/high-response-time"
            ),
            AlertRule(
                name="critical_error_rate",
                metric="error_rate",
                threshold=0.05,
                operator="gt",
                severity=AlertSeverity.CRITICAL,
                enabled=True,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK, NotificationChannel.WEBHOOK],
                escalation_minutes=5,
                max_escalations=5,
                description="Error rate exceeds 5%",
                runbook_url="https://docs.centuryproptax.com/runbooks/high-error-rate"
            ),
            AlertRule(
                name="high_memory_usage",
                metric="memory_usage_mb",
                threshold=1024,
                operator="gt",
                severity=AlertSeverity.WARNING,
                enabled=True,
                notification_channels=[NotificationChannel.EMAIL],
                escalation_minutes=15,
                description="Memory usage exceeds 1GB",
                runbook_url="https://docs.centuryproptax.com/runbooks/high-memory"
            ),
            AlertRule(
                name="database_connection_failure",
                metric="database_status",
                threshold=0,
                operator="eq",
                severity=AlertSeverity.CRITICAL,
                enabled=True,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK, NotificationChannel.WEBHOOK],
                escalation_minutes=2,
                max_escalations=10,
                description="Database connection failed",
                runbook_url="https://docs.centuryproptax.com/runbooks/database-failure"
            ),
            AlertRule(
                name="redis_connection_failure",
                metric="redis_status",
                threshold=0,
                operator="eq",
                severity=AlertSeverity.WARNING,
                enabled=True,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
                escalation_minutes=5,
                description="Redis connection failed",
                runbook_url="https://docs.centuryproptax.com/runbooks/redis-failure"
            ),
            AlertRule(
                name="disk_space_low",
                metric="disk_usage_percent",
                threshold=85.0,
                operator="gt",
                severity=AlertSeverity.WARNING,
                enabled=True,
                notification_channels=[NotificationChannel.EMAIL],
                escalation_minutes=30,
                description="Disk usage exceeds 85%",
                runbook_url="https://docs.centuryproptax.com/runbooks/disk-space"
            ),
            AlertRule(
                name="high_cpu_usage",
                metric="cpu_usage_percent",
                threshold=90.0,
                operator="gt",
                severity=AlertSeverity.WARNING,
                enabled=True,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
                escalation_minutes=10,
                description="CPU usage exceeds 90%",
                runbook_url="https://docs.centuryproptax.com/runbooks/high-cpu"
            )
        ]

        for rule in default_rules:
            self.alert_rules[rule.name] = rule

        logger.info(f"✅ Loaded {len(default_rules)} default alert rules")

    def load_alert_rules(self, config_file: str):
        """Load alert rules from configuration file."""
        try:
            config_path = Path(config_file)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    rules_config = json.load(f)

                for rule_data in rules_config.get('alert_rules', []):
                    rule = AlertRule(
                        name=rule_data['name'],
                        metric=rule_data['metric'],
                        threshold=rule_data['threshold'],
                        operator=rule_data['operator'],
                        severity=AlertSeverity(rule_data['severity']),
                        enabled=rule_data.get('enabled', True),
                        notification_channels=[
                            NotificationChannel(ch) for ch in rule_data.get('notification_channels', ['email'])
                        ],
                        escalation_minutes=rule_data.get('escalation_minutes', 15),
                        max_escalations=rule_data.get('max_escalations', 3),
                        suppression_duration=rule_data.get('suppression_duration', 60),
                        description=rule_data.get('description', ''),
                        runbook_url=rule_data.get('runbook_url', '')
                    )
                    self.alert_rules[rule.name] = rule

                logger.info(f"✅ Loaded {len(self.alert_rules)} alert rules from {config_file}")
            else:
                logger.warning(f"Alert config file {config_file} not found, using defaults")
                self.load_default_alert_rules()

        except Exception as e:
            logger.error(f"Failed to load alert rules from {config_file}: {e}")
            self.load_default_alert_rules()

    async def evaluate_metrics(self, metrics: Dict[str, Any]):
        """Evaluate metrics against alert rules and trigger alerts."""
        for rule_name, rule in self.alert_rules.items():
            if not rule.enabled:
                continue

            # Check if alert is suppressed
            if self._is_suppressed(rule_name):
                continue

            # Get metric value
            metric_value = metrics.get(rule.metric)
            if metric_value is None:
                continue

            # Evaluate threshold
            if self._evaluate_threshold(metric_value, rule.threshold, rule.operator):
                await self._trigger_alert(rule, metric_value)
            else:
                # Check if we need to resolve an active alert
                if rule_name in self.active_alerts:
                    await self._resolve_alert(rule_name)

    def _evaluate_threshold(self, value: Any, threshold: float, operator: str) -> bool:
        """Evaluate if value breaches threshold according to operator."""
        try:
            if operator == "gt":
                return float(value) > threshold
            elif operator == "lt":
                return float(value) < threshold
            elif operator == "eq":
                return float(value) == threshold
            elif operator == "ne":
                return float(value) != threshold
            else:
                logger.warning(f"Unknown operator: {operator}")
                return False
        except (ValueError, TypeError):
            return False

    def _is_suppressed(self, rule_name: str) -> bool:
        """Check if alert is currently suppressed."""
        if rule_name in self.suppressed_alerts:
            suppression_end = self.suppressed_alerts[rule_name]
            if datetime.now() < suppression_end:
                return True
            else:
                # Remove expired suppression
                del self.suppressed_alerts[rule_name]
        return False

    async def _trigger_alert(self, rule: AlertRule, metric_value: float):
        """Trigger an alert for the given rule."""
        now = datetime.now()

        # Check if this is an existing alert
        if rule.name in self.active_alerts:
            alert = self.active_alerts[rule.name]
            alert.current_value = metric_value
            alert.updated_at = now
            alert.notification_count += 1

            # Check if escalation is needed
            if self._should_escalate(alert, rule):
                alert.escalation_level += 1
                await self._send_notifications(rule, alert, escalation=True)
        else:
            # Create new alert
            alert = AlertInstance(
                rule_name=rule.name,
                metric=rule.metric,
                current_value=metric_value,
                threshold=rule.threshold,
                severity=rule.severity,
                status=AlertStatus.ACTIVE,
                created_at=now,
                updated_at=now,
                notification_count=1
            )
            self.active_alerts[rule.name] = alert
            await self._send_notifications(rule, alert)

        logger.warning(
            f"🚨 Alert triggered: {rule.name}",
            extra={
                "rule": rule.name,
                "metric": rule.metric,
                "value": metric_value,
                "threshold": rule.threshold,
                "severity": rule.severity.value
            }
        )

    def _should_escalate(self, alert: AlertInstance, rule: AlertRule) -> bool:
        """Check if alert should be escalated."""
        if alert.escalation_level >= rule.max_escalations:
            return False

        if alert.status != AlertStatus.ACTIVE:
            return False

        time_since_last_notification = datetime.now() - alert.updated_at
        return time_since_last_notification.total_seconds() >= (rule.escalation_minutes * 60)

    async def _resolve_alert(self, rule_name: str):
        """Resolve an active alert."""
        if rule_name in self.active_alerts:
            alert = self.active_alerts[rule_name]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now()

            # Move to history
            self.alert_history.append(alert)
            del self.active_alerts[rule_name]

            logger.info(f"✅ Alert resolved: {rule_name}")

    async def _send_notifications(self, rule: AlertRule, alert: AlertInstance, escalation: bool = False):
        """Send notifications through configured channels."""
        notification_tasks = []

        for channel in rule.notification_channels:
            if channel == NotificationChannel.EMAIL:
                notification_tasks.append(self._send_email_notification(rule, alert, escalation))
            elif channel == NotificationChannel.SLACK:
                notification_tasks.append(self._send_slack_notification(rule, alert, escalation))
            elif channel == NotificationChannel.WEBHOOK:
                notification_tasks.append(self._send_webhook_notification(rule, alert, escalation))
            elif channel == NotificationChannel.SMS:
                notification_tasks.append(self._send_sms_notification(rule, alert, escalation))

        # Send all notifications concurrently
        if notification_tasks:
            results = await asyncio.gather(*notification_tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    channel = rule.notification_channels[i].value
                    logger.error(f"Failed to send {channel} notification for {rule.name}: {result}")

    async def _send_email_notification(self, rule: AlertRule, alert: AlertInstance, escalation: bool = False):
        """Send email notification."""
        try:
            if not self.config.smtp_username or not self.config.email_to:
                return

            subject_prefix = "🚨 ESCALATION" if escalation else "🚨 ALERT"
            severity_emoji = {
                AlertSeverity.INFO: "ℹ️",
                AlertSeverity.WARNING: "⚠️",
                AlertSeverity.CRITICAL: "🔥",
                AlertSeverity.EMERGENCY: "🆘"
            }

            subject = f"{subject_prefix}: {rule.name} - {severity_emoji.get(rule.severity, '🚨')} {rule.severity.value.upper()}"

            body = f"""
Alert Details:
--------------
Alert Name: {rule.name}
Severity: {rule.severity.value.upper()}
Status: {alert.status.value.upper()}
Metric: {rule.metric}
Current Value: {alert.current_value}
Threshold: {alert.threshold}
Triggered: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
Escalation Level: {alert.escalation_level}

Description:
{rule.description}

Runbook:
{rule.runbook_url}

System Information:
------------------
Environment: Production
Service: Century Property Tax API
Dashboard: https://monitoring.centuryproptax.com/dashboard

Actions Required:
----------------
1. Acknowledge this alert in the monitoring dashboard
2. Follow the runbook procedures: {rule.runbook_url}
3. Investigate and resolve the underlying issue
4. Update the incident tracking system

This is an automated alert from the Century Property Tax monitoring system.
            """

            msg = MIMEMultipart()
            msg['From'] = self.config.email_from
            msg['To'] = ", ".join(self.config.email_to)
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            # Send email
            await asyncio.to_thread(self._send_smtp_email, msg)
            logger.info(f"📧 Email alert sent for {rule.name}")

        except Exception as e:
            logger.error(f"Failed to send email alert for {rule.name}: {e}")
            raise

    def _send_smtp_email(self, msg: MIMEMultipart):
        """Send email via SMTP (synchronous)."""
        with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
            server.starttls()
            server.login(self.config.smtp_username, self.config.smtp_password)
            server.send_message(msg)

    async def _send_slack_notification(self, rule: AlertRule, alert: AlertInstance, escalation: bool = False):
        """Send Slack notification."""
        try:
            if not self.config.slack_webhook_url:
                return

            severity_colors = {
                AlertSeverity.INFO: "#36a64f",
                AlertSeverity.WARNING: "#ff9500",
                AlertSeverity.CRITICAL: "#ff0000",
                AlertSeverity.EMERGENCY: "#8b0000"
            }

            prefix = "🚨 ESCALATION" if escalation else "🚨 ALERT"
            title = f"{prefix}: {rule.name}"

            payload = {
                "channel": self.config.slack_channel,
                "username": "Century Property Tax Monitoring",
                "icon_emoji": ":warning:",
                "attachments": [
                    {
                        "color": severity_colors.get(rule.severity, "#ff0000"),
                        "title": title,
                        "fields": [
                            {
                                "title": "Severity",
                                "value": rule.severity.value.upper(),
                                "short": True
                            },
                            {
                                "title": "Metric",
                                "value": f"{rule.metric}: {alert.current_value}",
                                "short": True
                            },
                            {
                                "title": "Threshold",
                                "value": str(rule.threshold),
                                "short": True
                            },
                            {
                                "title": "Escalation",
                                "value": f"Level {alert.escalation_level}",
                                "short": True
                            }
                        ],
                        "text": rule.description,
                        "footer": "Century Property Tax Monitoring",
                        "ts": int(alert.created_at.timestamp())
                    }
                ]
            }

            if rule.runbook_url:
                payload["attachments"][0]["actions"] = [
                    {
                        "type": "button",
                        "text": "View Runbook",
                        "url": rule.runbook_url
                    }
                ]

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.slack_webhook_url,
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        logger.info(f"💬 Slack alert sent for {rule.name}")
                    else:
                        logger.error(f"Slack notification failed: {response.status}")

        except Exception as e:
            logger.error(f"Failed to send Slack alert for {rule.name}: {e}")
            raise

    async def _send_webhook_notification(self, rule: AlertRule, alert: AlertInstance, escalation: bool = False):
        """Send webhook notification."""
        try:
            if not self.config.webhook_url:
                return

            payload = {
                "alert_name": rule.name,
                "metric": rule.metric,
                "current_value": alert.current_value,
                "threshold": rule.threshold,
                "severity": rule.severity.value,
                "status": alert.status.value,
                "escalation_level": alert.escalation_level,
                "escalation": escalation,
                "description": rule.description,
                "runbook_url": rule.runbook_url,
                "timestamp": alert.created_at.isoformat(),
                "environment": "production",
                "service": "centuryproptax-api"
            }

            headers = {'Content-Type': 'application/json'}
            if self.config.webhook_secret:
                # Add authentication header if secret is configured
                headers['Authorization'] = f"Bearer {self.config.webhook_secret}"

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.webhook_url,
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        logger.info(f"🔗 Webhook alert sent for {rule.name}")
                    else:
                        logger.error(f"Webhook notification failed: {response.status}")

        except Exception as e:
            logger.error(f"Failed to send webhook alert for {rule.name}: {e}")
            raise

    async def _send_sms_notification(self, rule: AlertRule, alert: AlertInstance, escalation: bool = False):
        """Send SMS notification (optional)."""
        try:
            if not self.config.sms_api_key or not self.config.sms_phone_numbers:
                return

            prefix = "ESCALATION" if escalation else "ALERT"
            message = f"{prefix}: {rule.name} - {rule.severity.value.upper()} - {rule.metric}: {alert.current_value}"

            # Implementation would depend on SMS provider (Twilio, AWS SNS, etc.)
            logger.info(f"📱 SMS alert would be sent for {rule.name}")

        except Exception as e:
            logger.error(f"Failed to send SMS alert for {rule.name}: {e}")
            raise

    async def acknowledge_alert(self, rule_name: str, acknowledged_by: str) -> bool:
        """Acknowledge an active alert."""
        if rule_name in self.active_alerts:
            alert = self.active_alerts[rule_name]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.now()
            alert.acknowledged_by = acknowledged_by

            logger.info(f"✅ Alert acknowledged: {rule_name} by {acknowledged_by}")
            return True
        return False

    async def suppress_alert(self, rule_name: str, duration_minutes: int) -> bool:
        """Suppress an alert for a specified duration."""
        if rule_name in self.alert_rules:
            suppression_end = datetime.now() + timedelta(minutes=duration_minutes)
            self.suppressed_alerts[rule_name] = suppression_end

            logger.info(f"🔇 Alert suppressed: {rule_name} for {duration_minutes} minutes")
            return True
        return False

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of current alert status."""
        return {
            "active_alerts": len(self.active_alerts),
            "total_rules": len(self.alert_rules),
            "enabled_rules": len([r for r in self.alert_rules.values() if r.enabled]),
            "suppressed_alerts": len(self.suppressed_alerts),
            "alerts_by_severity": {
                severity.value: len([
                    a for a in self.active_alerts.values()
                    if self.alert_rules[a.rule_name].severity == severity
                ])
                for severity in AlertSeverity
            }
        }

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get list of active alerts."""
        return [
            {
                **asdict(alert),
                "rule": asdict(self.alert_rules[alert.rule_name])
            }
            for alert in self.active_alerts.values()
        ]


# Global alert manager instance
alert_manager = AlertManager()