"""TDLR audit trail generation and management system."""

import logging
import hashlib
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import asyncio

from config.compliance_settings import (
    TDLRComplianceSettings,
    DataClassification,
    compliance_settings
)


class AuditEventType(Enum):
    """Types of audit events."""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_DELETION = "data_deletion"
    SYSTEM_ACCESS = "system_access"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_EVENT = "security_event"
    COMPLIANCE_VIOLATION = "compliance_violation"
    RETENTION_ACTION = "retention_action"
    PRIVACY_REQUEST = "privacy_request"
    REPORT_GENERATION = "report_generation"
    API_ACCESS = "api_access"
    FILE_ACCESS = "file_access"
    PAYMENT_PROCESSING = "payment_processing"
    EXEMPTION_APPLICATION = "exemption_application"
    ASSESSMENT_APPEAL = "assessment_appeal"


class AuditLevel(Enum):
    """Audit detail levels."""
    BASIC = "basic"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


class RiskLevel(Enum):
    """Risk levels for audit events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Individual audit event record."""
    event_id: str
    timestamp: datetime
    event_type: AuditEventType
    user_id: Optional[str]
    session_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    resource_type: str
    resource_id: str
    action: str
    outcome: str  # success, failure, partial
    risk_level: RiskLevel
    data_classification: Optional[DataClassification]
    before_state: Optional[Dict[str, Any]]
    after_state: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]
    checksum: str


@dataclass
class AuditChain:
    """Audit chain for integrity verification."""
    chain_id: str
    sequence_number: int
    previous_hash: Optional[str]
    current_hash: str
    events_count: int
    timestamp: datetime


@dataclass
class ComplianceAuditSummary:
    """Summary of compliance-related audit events."""
    period_start: datetime
    period_end: datetime
    total_events: int
    events_by_type: Dict[str, int]
    events_by_risk_level: Dict[str, int]
    compliance_violations: int
    security_events: int
    data_access_events: int
    privacy_requests: int
    retention_actions: int


class AuditTrailGenerator:
    """TDLR audit trail generation and management system."""

    def __init__(self):
        self.settings = compliance_settings
        self.logger = logging.getLogger(__name__)
        self.audit_events: List[AuditEvent] = []
        self.audit_chains: List[AuditChain] = []
        self.current_chain_id = str(uuid.uuid4())
        self.sequence_number = 0

    def log_audit_event(self, event_type: AuditEventType, action: str, resource_type: str,
                       resource_id: str, outcome: str = "success", user_id: Optional[str] = None,
                       session_id: Optional[str] = None, ip_address: Optional[str] = None,
                       user_agent: Optional[str] = None, risk_level: RiskLevel = RiskLevel.LOW,
                       data_classification: Optional[DataClassification] = None,
                       before_state: Optional[Dict[str, Any]] = None,
                       after_state: Optional[Dict[str, Any]] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log a comprehensive audit event."""

        event_id = str(uuid.uuid4())
        timestamp = datetime.now()

        # Create audit event
        audit_event = AuditEvent(
            event_id=event_id,
            timestamp=timestamp,
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            outcome=outcome,
            risk_level=risk_level,
            data_classification=data_classification,
            before_state=before_state,
            after_state=after_state,
            metadata=metadata or {},
            checksum=""  # Will be calculated
        )

        # Calculate checksum for integrity
        audit_event.checksum = self._calculate_event_checksum(audit_event)

        # Add to audit trail
        self.audit_events.append(audit_event)
        self.sequence_number += 1

        # Update audit chain
        self._update_audit_chain()

        # Log high-risk events immediately
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            self.logger.warning(f"High-risk audit event: {event_type.value} - {action} on {resource_type}:{resource_id}")

        # Log compliance-related events
        if event_type in [AuditEventType.COMPLIANCE_VIOLATION, AuditEventType.PRIVACY_REQUEST, AuditEventType.RETENTION_ACTION]:
            self.logger.info(f"Compliance audit event: {event_type.value} - {action}")

        return event_id

    def log_user_authentication(self, user_id: str, action: str, outcome: str,
                              ip_address: Optional[str] = None, user_agent: Optional[str] = None,
                              session_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log user authentication events."""
        event_type = AuditEventType.USER_LOGIN if action == "login" else AuditEventType.USER_LOGOUT
        risk_level = RiskLevel.MEDIUM if outcome == "failure" else RiskLevel.LOW

        return self.log_audit_event(
            event_type=event_type,
            action=action,
            resource_type="user_session",
            resource_id=user_id,
            outcome=outcome,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            risk_level=risk_level,
            metadata=metadata
        )

    def log_data_access(self, user_id: str, resource_type: str, resource_id: str,
                       action: str, data_classification: DataClassification,
                       outcome: str = "success", ip_address: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log data access events."""
        risk_level = RiskLevel.HIGH if data_classification in [DataClassification.RESTRICTED, DataClassification.PRIVATE] else RiskLevel.MEDIUM

        return self.log_audit_event(
            event_type=AuditEventType.DATA_ACCESS,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            user_id=user_id,
            ip_address=ip_address,
            risk_level=risk_level,
            data_classification=data_classification,
            metadata=metadata
        )

    def log_data_modification(self, user_id: str, resource_type: str, resource_id: str,
                            action: str, before_state: Dict[str, Any], after_state: Dict[str, Any],
                            data_classification: DataClassification, outcome: str = "success",
                            ip_address: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log data modification events with before/after states."""
        risk_level = RiskLevel.HIGH if data_classification in [DataClassification.RESTRICTED, DataClassification.PRIVATE] else RiskLevel.MEDIUM

        return self.log_audit_event(
            event_type=AuditEventType.DATA_MODIFICATION,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            user_id=user_id,
            ip_address=ip_address,
            risk_level=risk_level,
            data_classification=data_classification,
            before_state=before_state,
            after_state=after_state,
            metadata=metadata
        )

    def log_security_event(self, event_description: str, resource_type: str, resource_id: str,
                          risk_level: RiskLevel = RiskLevel.HIGH, user_id: Optional[str] = None,
                          ip_address: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log security-related events."""
        return self.log_audit_event(
            event_type=AuditEventType.SECURITY_EVENT,
            action=event_description,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome="detected",
            user_id=user_id,
            ip_address=ip_address,
            risk_level=risk_level,
            metadata=metadata
        )

    def log_compliance_violation(self, violation_type: str, resource_type: str, resource_id: str,
                               description: str, user_id: Optional[str] = None,
                               metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log compliance violations."""
        return self.log_audit_event(
            event_type=AuditEventType.COMPLIANCE_VIOLATION,
            action=f"violation_detected_{violation_type}",
            resource_type=resource_type,
            resource_id=resource_id,
            outcome="violation",
            user_id=user_id,
            risk_level=RiskLevel.CRITICAL,
            metadata={**(metadata or {}), "violation_description": description}
        )

    def log_privacy_request(self, request_type: str, data_subject_id: str, user_id: str,
                          outcome: str = "initiated", metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log privacy-related requests (GDPR-style rights)."""
        return self.log_audit_event(
            event_type=AuditEventType.PRIVACY_REQUEST,
            action=f"privacy_request_{request_type}",
            resource_type="data_subject",
            resource_id=data_subject_id,
            outcome=outcome,
            user_id=user_id,
            risk_level=RiskLevel.MEDIUM,
            data_classification=DataClassification.PRIVATE,
            metadata=metadata
        )

    def log_property_tax_operation(self, operation_type: str, property_id: str, user_id: str,
                                 action_details: Dict[str, Any], outcome: str = "success",
                                 ip_address: Optional[str] = None) -> str:
        """Log property tax specific operations."""
        event_type_mapping = {
            "payment": AuditEventType.PAYMENT_PROCESSING,
            "exemption": AuditEventType.EXEMPTION_APPLICATION,
            "appeal": AuditEventType.ASSESSMENT_APPEAL,
            "inquiry": AuditEventType.DATA_ACCESS
        }

        event_type = event_type_mapping.get(operation_type, AuditEventType.DATA_ACCESS)
        risk_level = RiskLevel.MEDIUM if operation_type in ["payment", "exemption", "appeal"] else RiskLevel.LOW

        return self.log_audit_event(
            event_type=event_type,
            action=f"property_tax_{operation_type}",
            resource_type="property",
            resource_id=property_id,
            outcome=outcome,
            user_id=user_id,
            ip_address=ip_address,
            risk_level=risk_level,
            data_classification=DataClassification.CONFIDENTIAL,
            metadata=action_details
        )

    def search_audit_events(self, criteria: Dict[str, Any]) -> List[AuditEvent]:
        """Search audit events based on criteria."""
        filtered_events = self.audit_events

        # Filter by date range
        if "start_date" in criteria:
            start_date = datetime.fromisoformat(criteria["start_date"])
            filtered_events = [e for e in filtered_events if e.timestamp >= start_date]

        if "end_date" in criteria:
            end_date = datetime.fromisoformat(criteria["end_date"])
            filtered_events = [e for e in filtered_events if e.timestamp <= end_date]

        # Filter by event type
        if "event_type" in criteria:
            event_types = criteria["event_type"] if isinstance(criteria["event_type"], list) else [criteria["event_type"]]
            filtered_events = [e for e in filtered_events if e.event_type.value in event_types]

        # Filter by user
        if "user_id" in criteria:
            filtered_events = [e for e in filtered_events if e.user_id == criteria["user_id"]]

        # Filter by resource
        if "resource_type" in criteria:
            filtered_events = [e for e in filtered_events if e.resource_type == criteria["resource_type"]]

        if "resource_id" in criteria:
            filtered_events = [e for e in filtered_events if e.resource_id == criteria["resource_id"]]

        # Filter by risk level
        if "risk_level" in criteria:
            risk_levels = criteria["risk_level"] if isinstance(criteria["risk_level"], list) else [criteria["risk_level"]]
            filtered_events = [e for e in filtered_events if e.risk_level.value in risk_levels]

        # Filter by outcome
        if "outcome" in criteria:
            outcomes = criteria["outcome"] if isinstance(criteria["outcome"], list) else [criteria["outcome"]]
            filtered_events = [e for e in filtered_events if e.outcome in outcomes]

        return filtered_events

    def generate_compliance_audit_report(self, start_date: datetime, end_date: datetime) -> ComplianceAuditSummary:
        """Generate comprehensive compliance audit report."""
        period_events = self.search_audit_events({
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        })

        events_by_type = {}
        events_by_risk_level = {}
        compliance_violations = 0
        security_events = 0
        data_access_events = 0
        privacy_requests = 0
        retention_actions = 0

        for event in period_events:
            # Count by type
            event_type = event.event_type.value
            events_by_type[event_type] = events_by_type.get(event_type, 0) + 1

            # Count by risk level
            risk_level = event.risk_level.value
            events_by_risk_level[risk_level] = events_by_risk_level.get(risk_level, 0) + 1

            # Count specific compliance-related events
            if event.event_type == AuditEventType.COMPLIANCE_VIOLATION:
                compliance_violations += 1
            elif event.event_type == AuditEventType.SECURITY_EVENT:
                security_events += 1
            elif event.event_type == AuditEventType.DATA_ACCESS:
                data_access_events += 1
            elif event.event_type == AuditEventType.PRIVACY_REQUEST:
                privacy_requests += 1
            elif event.event_type == AuditEventType.RETENTION_ACTION:
                retention_actions += 1

        return ComplianceAuditSummary(
            period_start=start_date,
            period_end=end_date,
            total_events=len(period_events),
            events_by_type=events_by_type,
            events_by_risk_level=events_by_risk_level,
            compliance_violations=compliance_violations,
            security_events=security_events,
            data_access_events=data_access_events,
            privacy_requests=privacy_requests,
            retention_actions=retention_actions
        )

    def verify_audit_integrity(self) -> Dict[str, Any]:
        """Verify audit trail integrity using checksums and chain verification."""
        integrity_results = {
            "total_events": len(self.audit_events),
            "checksum_failures": 0,
            "chain_integrity": True,
            "corrupted_events": [],
            "missing_chains": 0,
            "verification_timestamp": datetime.now().isoformat()
        }

        # Verify individual event checksums
        for event in self.audit_events:
            calculated_checksum = self._calculate_event_checksum(event, verify=True)
            if calculated_checksum != event.checksum:
                integrity_results["checksum_failures"] += 1
                integrity_results["corrupted_events"].append({
                    "event_id": event.event_id,
                    "timestamp": event.timestamp.isoformat(),
                    "expected_checksum": event.checksum,
                    "calculated_checksum": calculated_checksum
                })

        # Verify audit chain integrity
        for i, chain in enumerate(self.audit_chains[1:], 1):
            previous_chain = self.audit_chains[i-1]
            if chain.previous_hash != previous_chain.current_hash:
                integrity_results["chain_integrity"] = False
                break

        return integrity_results

    def export_audit_trail(self, format_type: str = "json", criteria: Optional[Dict[str, Any]] = None) -> str:
        """Export audit trail in specified format."""
        events_to_export = self.search_audit_events(criteria or {})

        if format_type.lower() == "json":
            return json.dumps([asdict(event) for event in events_to_export],
                            default=str, indent=2)
        elif format_type.lower() == "csv":
            # Implementation for CSV export would go here
            return self._export_to_csv(events_to_export)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")

    def _calculate_event_checksum(self, event: AuditEvent, verify: bool = False) -> str:
        """Calculate checksum for audit event integrity."""
        # Create a consistent string representation for hashing
        event_dict = asdict(event)
        if verify:
            # Remove checksum field for verification
            event_dict.pop("checksum", None)

        # Convert to JSON string for consistent hashing
        event_string = json.dumps(event_dict, sort_keys=True, default=str)
        return hashlib.sha256(event_string.encode()).hexdigest()

    def _update_audit_chain(self):
        """Update audit chain for integrity verification."""
        events_in_chain = len(self.audit_events)
        previous_hash = self.audit_chains[-1].current_hash if self.audit_chains else None

        # Calculate current hash based on recent events
        recent_events = self.audit_events[-10:] if events_in_chain >= 10 else self.audit_events
        events_string = json.dumps([asdict(e) for e in recent_events], sort_keys=True, default=str)
        current_hash = hashlib.sha256(events_string.encode()).hexdigest()

        chain = AuditChain(
            chain_id=self.current_chain_id,
            sequence_number=self.sequence_number,
            previous_hash=previous_hash,
            current_hash=current_hash,
            events_count=events_in_chain,
            timestamp=datetime.now()
        )

        self.audit_chains.append(chain)

    def _export_to_csv(self, events: List[AuditEvent]) -> str:
        """Export audit events to CSV format."""
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "Event ID", "Timestamp", "Event Type", "User ID", "Resource Type",
            "Resource ID", "Action", "Outcome", "Risk Level", "IP Address", "Checksum"
        ])

        # Write events
        for event in events:
            writer.writerow([
                event.event_id,
                event.timestamp.isoformat(),
                event.event_type.value,
                event.user_id or "",
                event.resource_type,
                event.resource_id,
                event.action,
                event.outcome,
                event.risk_level.value,
                event.ip_address or "",
                event.checksum
            ])

        return output.getvalue()


# Example usage and testing
if __name__ == "__main__":
    audit_generator = AuditTrailGenerator()

    print("Testing audit trail generation...")

    # Test user authentication
    audit_generator.log_user_authentication(
        user_id="user123",
        action="login",
        outcome="success",
        ip_address="192.168.1.100",
        metadata={"login_method": "password"}
    )

    # Test data access
    audit_generator.log_data_access(
        user_id="user123",
        resource_type="property",
        resource_id="PROP789",
        action="view_assessment",
        data_classification=DataClassification.CONFIDENTIAL,
        ip_address="192.168.1.100"
    )

    # Test property tax operation
    audit_generator.log_property_tax_operation(
        operation_type="payment",
        property_id="PROP789",
        user_id="user123",
        action_details={"amount": 2500.00, "payment_method": "credit_card"},
        ip_address="192.168.1.100"
    )

    # Test compliance violation
    audit_generator.log_compliance_violation(
        violation_type="data_retention",
        resource_type="customer_data",
        resource_id="CUST456",
        description="Data retained beyond policy limit",
        user_id="system"
    )

    print(f"Generated {len(audit_generator.audit_events)} audit events")

    # Generate compliance report
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    report = audit_generator.generate_compliance_audit_report(start_date, end_date)

    print(f"\nCompliance Audit Summary:")
    print(f"  Total events: {report.total_events}")
    print(f"  Compliance violations: {report.compliance_violations}")
    print(f"  Security events: {report.security_events}")
    print(f"  Data access events: {report.data_access_events}")

    # Verify integrity
    integrity = audit_generator.verify_audit_integrity()
    print(f"\nAudit Integrity Check:")
    print(f"  Total events verified: {integrity['total_events']}")
    print(f"  Checksum failures: {integrity['checksum_failures']}")
    print(f"  Chain integrity: {integrity['chain_integrity']}")