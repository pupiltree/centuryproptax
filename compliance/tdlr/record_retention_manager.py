"""TDLR record retention management and automated enforcement."""

import logging
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import os

from config.compliance_settings import (
    TDLRComplianceSettings,
    DataClassification,
    RetentionPeriod,
    compliance_settings
)


class RetentionAction(Enum):
    """Actions to take when retention period expires."""
    DELETE = "delete"
    ARCHIVE = "archive"
    ANONYMIZE = "anonymize"
    RETAIN = "retain"
    LEGAL_HOLD = "legal_hold"


class RetentionStatus(Enum):
    """Status of retention policy enforcement."""
    ACTIVE = "active"
    APPROACHING_EXPIRY = "approaching_expiry"
    EXPIRED = "expired"
    ARCHIVED = "archived"
    DELETED = "deleted"
    LEGAL_HOLD = "legal_hold"


@dataclass
class RetentionPolicy:
    """Retention policy definition."""
    policy_id: str
    name: str
    description: str
    data_classification: DataClassification
    retention_period: RetentionPeriod
    retention_action: RetentionAction
    applicable_contexts: List[str]
    legal_basis: str
    created_date: datetime
    active: bool


@dataclass
class RetentionRecord:
    """Individual record retention tracking."""
    record_id: str
    data_classification: DataClassification
    retention_policy_id: str
    created_timestamp: datetime
    retention_deadline: datetime
    status: RetentionStatus
    last_accessed: Optional[datetime]
    legal_hold: bool
    retention_action: RetentionAction
    metadata: Dict[str, Any]


@dataclass
class RetentionEvent:
    """Retention lifecycle event."""
    event_id: str
    record_id: str
    event_type: str  # created, accessed, retention_applied, deleted, archived
    timestamp: datetime
    action_taken: Optional[str]
    user_id: Optional[str]
    details: Dict[str, Any]


class RecordRetentionManager:
    """TDLR record retention management and automated enforcement system."""

    def __init__(self):
        self.settings = compliance_settings
        self.logger = logging.getLogger(__name__)
        self.retention_policies: Dict[str, RetentionPolicy] = {}
        self.retention_records: Dict[str, RetentionRecord] = {}
        self.retention_events: List[RetentionEvent] = []
        self._initialize_default_policies()

    def _initialize_default_policies(self):
        """Initialize default TDLR retention policies."""
        default_policies = [
            RetentionPolicy(
                policy_id="TDLR_PROPERTY_TAX_RECORDS",
                name="Property Tax Records",
                description="Property tax assessment and payment records per TDLR requirements",
                data_classification=DataClassification.CONFIDENTIAL,
                retention_period=RetentionPeriod.LONG_TERM,  # 7 years
                retention_action=RetentionAction.ARCHIVE,
                applicable_contexts=["property_assessment", "tax_calculation", "payment_processing"],
                legal_basis="Texas Property Tax Code Section 25.26",
                created_date=datetime.now(),
                active=True
            ),
            RetentionPolicy(
                policy_id="TDLR_CUSTOMER_COMMUNICATIONS",
                name="Customer Communications",
                description="Customer support conversations and correspondence",
                data_classification=DataClassification.CONFIDENTIAL,
                retention_period=RetentionPeriod.LONG_TERM,  # 7 years
                retention_action=RetentionAction.ARCHIVE,
                applicable_contexts=["customer_support", "inquiries", "complaints"],
                legal_basis="Texas Government Code Chapter 552",
                created_date=datetime.now(),
                active=True
            ),
            RetentionPolicy(
                policy_id="TDLR_EXEMPTION_APPLICATIONS",
                name="Exemption Applications",
                description="Property tax exemption applications and supporting documents",
                data_classification=DataClassification.RESTRICTED,
                retention_period=RetentionPeriod.LONG_TERM,  # 7 years
                retention_action=RetentionAction.ARCHIVE,
                applicable_contexts=["exemption_application", "eligibility_verification"],
                legal_basis="Texas Tax Code Chapter 11",
                created_date=datetime.now(),
                active=True
            ),
            RetentionPolicy(
                policy_id="TDLR_APPEAL_RECORDS",
                name="Assessment Appeal Records",
                description="Property assessment appeals and related documentation",
                data_classification=DataClassification.RESTRICTED,
                retention_period=RetentionPeriod.LONG_TERM,  # 7 years
                retention_action=RetentionAction.ARCHIVE,
                applicable_contexts=["assessment_appeal", "dispute_resolution"],
                legal_basis="Texas Tax Code Chapter 41",
                created_date=datetime.now(),
                active=True
            ),
            RetentionPolicy(
                policy_id="TDLR_PUBLIC_RECORDS",
                name="Public Records",
                description="Public property information and general inquiries",
                data_classification=DataClassification.PUBLIC,
                retention_period=RetentionPeriod.PERMANENT,  # Permanent
                retention_action=RetentionAction.RETAIN,
                applicable_contexts=["public_inquiry", "general_information"],
                legal_basis="Texas Government Code Chapter 552",
                created_date=datetime.now(),
                active=True
            ),
            RetentionPolicy(
                policy_id="TDLR_AUDIT_LOGS",
                name="System Audit Logs",
                description="System access and operation audit trails",
                data_classification=DataClassification.CONFIDENTIAL,
                retention_period=RetentionPeriod.LONG_TERM,  # 7 years
                retention_action=RetentionAction.ARCHIVE,
                applicable_contexts=["system_access", "data_modification", "security_events"],
                legal_basis="TDLR Administrative Rules",
                created_date=datetime.now(),
                active=True
            ),
            RetentionPolicy(
                policy_id="TDLR_PERSONAL_DATA",
                name="Personal Data",
                description="Customer personal information and preferences",
                data_classification=DataClassification.PRIVATE,
                retention_period=RetentionPeriod.MEDIUM_TERM,  # 1 year
                retention_action=RetentionAction.ANONYMIZE,
                applicable_contexts=["customer_profile", "preferences", "contact_information"],
                legal_basis="Privacy protection requirements",
                created_date=datetime.now(),
                active=True
            )
        ]

        for policy in default_policies:
            self.retention_policies[policy.policy_id] = policy

    def register_record(self, record_id: str, data_classification: DataClassification,
                       context: str, metadata: Optional[Dict[str, Any]] = None) -> RetentionRecord:
        """Register a new record for retention tracking."""
        policy = self._find_applicable_policy(data_classification, context)
        if not policy:
            self.logger.warning(f"No applicable retention policy found for {context} with {data_classification}")
            policy = self._get_default_policy()

        created_timestamp = datetime.now()
        retention_deadline = self._calculate_retention_deadline(created_timestamp, policy.retention_period)

        retention_record = RetentionRecord(
            record_id=record_id,
            data_classification=data_classification,
            retention_policy_id=policy.policy_id,
            created_timestamp=created_timestamp,
            retention_deadline=retention_deadline,
            status=RetentionStatus.ACTIVE,
            last_accessed=created_timestamp,
            legal_hold=False,
            retention_action=policy.retention_action,
            metadata=metadata or {}
        )

        self.retention_records[record_id] = retention_record

        # Log creation event
        self._log_retention_event(
            record_id=record_id,
            event_type="created",
            action_taken="record_registered",
            details={
                "policy_id": policy.policy_id,
                "retention_deadline": retention_deadline.isoformat(),
                "context": context
            }
        )

        self.logger.info(f"Registered record {record_id} for retention under policy {policy.policy_id}")
        return retention_record

    def update_record_access(self, record_id: str, user_id: Optional[str] = None):
        """Update record access timestamp."""
        if record_id in self.retention_records:
            self.retention_records[record_id].last_accessed = datetime.now()

            self._log_retention_event(
                record_id=record_id,
                event_type="accessed",
                user_id=user_id,
                details={"access_timestamp": datetime.now().isoformat()}
            )

    def apply_legal_hold(self, record_id: str, reason: str, user_id: Optional[str] = None) -> bool:
        """Apply legal hold to prevent retention policy enforcement."""
        if record_id not in self.retention_records:
            self.logger.error(f"Record {record_id} not found for legal hold")
            return False

        self.retention_records[record_id].legal_hold = True
        self.retention_records[record_id].status = RetentionStatus.LEGAL_HOLD

        self._log_retention_event(
            record_id=record_id,
            event_type="legal_hold_applied",
            user_id=user_id,
            action_taken="legal_hold",
            details={"reason": reason}
        )

        self.logger.info(f"Legal hold applied to record {record_id}: {reason}")
        return True

    def remove_legal_hold(self, record_id: str, reason: str, user_id: Optional[str] = None) -> bool:
        """Remove legal hold from record."""
        if record_id not in self.retention_records:
            self.logger.error(f"Record {record_id} not found for legal hold removal")
            return False

        self.retention_records[record_id].legal_hold = False
        self.retention_records[record_id].status = RetentionStatus.ACTIVE

        self._log_retention_event(
            record_id=record_id,
            event_type="legal_hold_removed",
            user_id=user_id,
            action_taken="legal_hold_removed",
            details={"reason": reason}
        )

        self.logger.info(f"Legal hold removed from record {record_id}: {reason}")
        return True

    async def enforce_retention_policies(self) -> Dict[str, Any]:
        """Enforce retention policies across all tracked records."""
        enforcement_results = {
            "total_records_processed": 0,
            "records_approaching_expiry": 0,
            "records_expired": 0,
            "records_archived": 0,
            "records_deleted": 0,
            "records_anonymized": 0,
            "records_on_legal_hold": 0,
            "errors": []
        }

        current_time = datetime.now()
        warning_threshold = timedelta(days=30)  # 30 days warning before expiry

        for record_id, record in self.retention_records.items():
            try:
                enforcement_results["total_records_processed"] += 1

                # Skip records on legal hold
                if record.legal_hold:
                    enforcement_results["records_on_legal_hold"] += 1
                    continue

                # Check if approaching expiry
                time_to_expiry = record.retention_deadline - current_time
                if timedelta(0) < time_to_expiry <= warning_threshold:
                    record.status = RetentionStatus.APPROACHING_EXPIRY
                    enforcement_results["records_approaching_expiry"] += 1

                    self._log_retention_event(
                        record_id=record_id,
                        event_type="approaching_expiry",
                        details={"days_until_expiry": time_to_expiry.days}
                    )
                    continue

                # Check if expired
                if current_time >= record.retention_deadline:
                    enforcement_results["records_expired"] += 1

                    # Apply retention action
                    action_result = await self._apply_retention_action(record)
                    if action_result["success"]:
                        if record.retention_action == RetentionAction.ARCHIVE:
                            enforcement_results["records_archived"] += 1
                        elif record.retention_action == RetentionAction.DELETE:
                            enforcement_results["records_deleted"] += 1
                        elif record.retention_action == RetentionAction.ANONYMIZE:
                            enforcement_results["records_anonymized"] += 1
                    else:
                        enforcement_results["errors"].append({
                            "record_id": record_id,
                            "error": action_result["error"]
                        })

            except Exception as e:
                self.logger.error(f"Error enforcing retention for record {record_id}: {str(e)}")
                enforcement_results["errors"].append({
                    "record_id": record_id,
                    "error": str(e)
                })

        self.logger.info(f"Retention enforcement completed: {enforcement_results}")
        return enforcement_results

    async def _apply_retention_action(self, record: RetentionRecord) -> Dict[str, Any]:
        """Apply the specified retention action to a record."""
        try:
            if record.retention_action == RetentionAction.ARCHIVE:
                success = await self._archive_record(record)
                if success:
                    record.status = RetentionStatus.ARCHIVED
            elif record.retention_action == RetentionAction.DELETE:
                success = await self._delete_record(record)
                if success:
                    record.status = RetentionStatus.DELETED
            elif record.retention_action == RetentionAction.ANONYMIZE:
                success = await self._anonymize_record(record)
                if success:
                    record.status = RetentionStatus.ARCHIVED
            elif record.retention_action == RetentionAction.RETAIN:
                success = True  # No action needed for retention
            else:
                success = False
                error_msg = f"Unknown retention action: {record.retention_action}"

            if success:
                self._log_retention_event(
                    record_id=record.record_id,
                    event_type="retention_applied",
                    action_taken=record.retention_action.value,
                    details={"retention_deadline": record.retention_deadline.isoformat()}
                )

            return {"success": success, "error": error_msg if not success else None}

        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error applying retention action for {record.record_id}: {error_msg}")
            return {"success": False, "error": error_msg}

    async def _archive_record(self, record: RetentionRecord) -> bool:
        """Archive a record (move to long-term storage)."""
        # Implementation would move record to archive storage
        self.logger.info(f"Archiving record {record.record_id}")
        return True

    async def _delete_record(self, record: RetentionRecord) -> bool:
        """Securely delete a record."""
        # Implementation would securely delete the record
        self.logger.info(f"Deleting record {record.record_id}")
        return True

    async def _anonymize_record(self, record: RetentionRecord) -> bool:
        """Anonymize a record (remove PII while preserving analytics value)."""
        # Implementation would anonymize PII in the record
        self.logger.info(f"Anonymizing record {record.record_id}")
        return True

    def _find_applicable_policy(self, data_classification: DataClassification, context: str) -> Optional[RetentionPolicy]:
        """Find the most applicable retention policy for given classification and context."""
        for policy in self.retention_policies.values():
            if (policy.active and
                policy.data_classification == data_classification and
                context in policy.applicable_contexts):
                return policy
        return None

    def _get_default_policy(self) -> RetentionPolicy:
        """Get default retention policy."""
        return self.retention_policies.get("TDLR_PROPERTY_TAX_RECORDS")

    def _calculate_retention_deadline(self, created_timestamp: datetime, retention_period: RetentionPeriod) -> datetime:
        """Calculate retention deadline based on creation time and retention period."""
        if retention_period == RetentionPeriod.IMMEDIATE:
            return created_timestamp
        elif retention_period == RetentionPeriod.PERMANENT:
            return datetime.max
        else:
            return created_timestamp + timedelta(days=retention_period.value)

    def _log_retention_event(self, record_id: str, event_type: str, action_taken: Optional[str] = None,
                           user_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """Log retention lifecycle event."""
        event = RetentionEvent(
            event_id=f"{record_id}_{event_type}_{datetime.now().timestamp()}",
            record_id=record_id,
            event_type=event_type,
            timestamp=datetime.now(),
            action_taken=action_taken,
            user_id=user_id,
            details=details or {}
        )
        self.retention_events.append(event)

    def get_retention_status(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Get retention status for a specific record."""
        if record_id not in self.retention_records:
            return None

        record = self.retention_records[record_id]
        policy = self.retention_policies.get(record.retention_policy_id)

        return {
            "record_id": record_id,
            "status": record.status.value,
            "data_classification": record.data_classification.value,
            "retention_policy": policy.name if policy else "Unknown",
            "created_timestamp": record.created_timestamp.isoformat(),
            "retention_deadline": record.retention_deadline.isoformat(),
            "last_accessed": record.last_accessed.isoformat() if record.last_accessed else None,
            "legal_hold": record.legal_hold,
            "retention_action": record.retention_action.value,
            "days_until_expiry": (record.retention_deadline - datetime.now()).days if record.retention_deadline != datetime.max else -1
        }

    def generate_retention_report(self) -> Dict[str, Any]:
        """Generate comprehensive retention management report."""
        total_records = len(self.retention_records)
        active_records = len([r for r in self.retention_records.values() if r.status == RetentionStatus.ACTIVE])
        approaching_expiry = len([r for r in self.retention_records.values() if r.status == RetentionStatus.APPROACHING_EXPIRY])
        expired_records = len([r for r in self.retention_records.values() if r.status == RetentionStatus.EXPIRED])
        archived_records = len([r for r in self.retention_records.values() if r.status == RetentionStatus.ARCHIVED])
        legal_hold_records = len([r for r in self.retention_records.values() if r.legal_hold])

        policy_usage = {}
        for record in self.retention_records.values():
            policy_id = record.retention_policy_id
            policy_usage[policy_id] = policy_usage.get(policy_id, 0) + 1

        return {
            "report_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_records": total_records,
                "active_records": active_records,
                "approaching_expiry": approaching_expiry,
                "expired_records": expired_records,
                "archived_records": archived_records,
                "legal_hold_records": legal_hold_records
            },
            "policy_usage": policy_usage,
            "total_policies": len(self.retention_policies),
            "total_events": len(self.retention_events),
            "compliance_status": "compliant" if expired_records == 0 else "attention_required"
        }


# Example usage and testing
if __name__ == "__main__":
    async def test_retention_manager():
        manager = RecordRetentionManager()

        # Register some test records
        test_records = [
            ("PROP123_INQUIRY", DataClassification.PUBLIC, "public_inquiry"),
            ("CUST456_PAYMENT", DataClassification.CONFIDENTIAL, "payment_processing"),
            ("APPEAL789_DOC", DataClassification.RESTRICTED, "assessment_appeal"),
            ("PERSONAL012_PROFILE", DataClassification.PRIVATE, "customer_profile")
        ]

        print("Registering test records...")
        for record_id, classification, context in test_records:
            record = manager.register_record(record_id, classification, context)
            print(f"  Registered {record_id}: {record.status.value}, expires {record.retention_deadline.date()}")

        # Apply legal hold to one record
        manager.apply_legal_hold("APPEAL789_DOC", "Ongoing litigation")

        # Check retention status
        print(f"\nRetention status for PROP123_INQUIRY:")
        status = manager.get_retention_status("PROP123_INQUIRY")
        if status:
            print(f"  Status: {status['status']}")
            print(f"  Days until expiry: {status['days_until_expiry']}")

        # Run retention enforcement
        print(f"\nRunning retention enforcement...")
        results = await manager.enforce_retention_policies()
        print(f"  Processed {results['total_records_processed']} records")
        print(f"  Legal hold: {results['records_on_legal_hold']} records")

        # Generate report
        print(f"\nRetention management report:")
        report = manager.generate_retention_report()
        print(f"  Total records: {report['summary']['total_records']}")
        print(f"  Active records: {report['summary']['active_records']}")
        print(f"  Compliance status: {report['compliance_status']}")

    # Run the async test
    asyncio.run(test_retention_manager())