"""TDLR privacy compliance validation and enforcement."""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import hashlib
import json

from config.compliance_settings import (
    TDLRComplianceSettings,
    DataClassification,
    RetentionPeriod,
    compliance_settings
)


class PrivacyViolationType(Enum):
    """Types of privacy compliance violations."""
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PII_EXPOSURE = "pii_exposure"
    RETENTION_VIOLATION = "retention_violation"
    CONSENT_MISSING = "consent_missing"
    DATA_MINIMIZATION_FAILURE = "data_minimization_failure"
    ENCRYPTION_FAILURE = "encryption_failure"
    ACCESS_LOG_MISSING = "access_log_missing"


@dataclass
class PrivacyViolation:
    """Privacy compliance violation record."""
    violation_type: PrivacyViolationType
    severity: str  # critical, high, medium, low
    description: str
    data_subject: Optional[str]
    timestamp: datetime
    remediation_required: bool
    remediation_deadline: Optional[datetime]
    metadata: Dict[str, Any]


@dataclass
class DataSubjectRequest:
    """Data subject privacy request record."""
    request_id: str
    request_type: str  # access, rectification, erasure, portability
    data_subject_id: str
    request_timestamp: datetime
    status: str  # pending, in_progress, completed, rejected
    completion_deadline: datetime
    request_details: Dict[str, Any]
    response_data: Optional[Dict[str, Any]]


class PrivacyComplianceValidator:
    """TDLR privacy compliance validation and enforcement system."""

    def __init__(self):
        self.settings = compliance_settings
        self.logger = logging.getLogger(__name__)
        self.violations: List[PrivacyViolation] = []
        self.data_subject_requests: List[DataSubjectRequest] = []

    def validate_data_handling(self, data: Dict[str, Any], context: str) -> List[PrivacyViolation]:
        """Validate data handling compliance with TDLR requirements."""
        violations = []

        # Check for PII exposure
        pii_violations = self._check_pii_exposure(data, context)
        violations.extend(pii_violations)

        # Check data minimization compliance
        minimization_violations = self._check_data_minimization(data, context)
        violations.extend(minimization_violations)

        # Check encryption requirements
        encryption_violations = self._check_encryption_compliance(data, context)
        violations.extend(encryption_violations)

        # Check retention compliance
        retention_violations = self._check_retention_compliance(data, context)
        violations.extend(retention_violations)

        # Check access control compliance
        access_violations = self._check_access_control_compliance(data, context)
        violations.extend(access_violations)

        return violations

    def _check_pii_exposure(self, data: Dict[str, Any], context: str) -> List[PrivacyViolation]:
        """Check for personally identifiable information exposure."""
        violations = []

        if not self.settings.pii_detection_enabled:
            return violations

        for field_name, field_value in data.items():
            if isinstance(field_value, str):
                for pii_type, pattern in self.settings.SENSITIVE_DATA_PATTERNS.items():
                    if re.search(pattern, field_value, re.IGNORECASE):
                        violation = PrivacyViolation(
                            violation_type=PrivacyViolationType.PII_EXPOSURE,
                            severity="high",
                            description=f"PII detected in field '{field_name}': {pii_type}",
                            data_subject=self._extract_data_subject_id(data),
                            timestamp=datetime.now(),
                            remediation_required=True,
                            remediation_deadline=datetime.now() + timedelta(hours=24),
                            metadata={
                                "context": context,
                                "field_name": field_name,
                                "pii_type": pii_type,
                                "pattern_matched": pattern
                            }
                        )
                        violations.append(violation)
                        self.logger.warning(f"PII exposure detected: {pii_type} in {field_name}")

        return violations

    def _check_data_minimization(self, data: Dict[str, Any], context: str) -> List[PrivacyViolation]:
        """Check data minimization compliance."""
        violations = []

        if not self.settings.data_minimization_enabled:
            return violations

        # Check if data contains more fields than necessary for the context
        required_fields = self._get_required_fields_for_context(context)
        excessive_fields = set(data.keys()) - set(required_fields)

        if excessive_fields:
            violation = PrivacyViolation(
                violation_type=PrivacyViolationType.DATA_MINIMIZATION_FAILURE,
                severity="medium",
                description=f"Excessive data collection: {len(excessive_fields)} unnecessary fields",
                data_subject=self._extract_data_subject_id(data),
                timestamp=datetime.now(),
                remediation_required=True,
                remediation_deadline=datetime.now() + timedelta(days=7),
                metadata={
                    "context": context,
                    "excessive_fields": list(excessive_fields),
                    "required_fields": required_fields
                }
            )
            violations.append(violation)

        return violations

    def _check_encryption_compliance(self, data: Dict[str, Any], context: str) -> List[PrivacyViolation]:
        """Check encryption compliance for sensitive data."""
        violations = []

        if not self.settings.data_encryption_required:
            return violations

        classification = self._classify_data(data, context)
        if classification in [DataClassification.CONFIDENTIAL, DataClassification.RESTRICTED, DataClassification.PRIVATE]:
            # Check if sensitive data is properly encrypted
            if not self._is_data_encrypted(data):
                violation = PrivacyViolation(
                    violation_type=PrivacyViolationType.ENCRYPTION_FAILURE,
                    severity="critical",
                    description=f"Sensitive data not encrypted: {classification.value}",
                    data_subject=self._extract_data_subject_id(data),
                    timestamp=datetime.now(),
                    remediation_required=True,
                    remediation_deadline=datetime.now() + timedelta(hours=4),
                    metadata={
                        "context": context,
                        "data_classification": classification.value,
                        "encryption_required": True
                    }
                )
                violations.append(violation)

        return violations

    def _check_retention_compliance(self, data: Dict[str, Any], context: str) -> List[PrivacyViolation]:
        """Check data retention compliance."""
        violations = []

        classification = self._classify_data(data, context)
        retention_period = self.settings.get_retention_period_for_classification(classification)

        # Check if data has proper retention metadata
        if "created_timestamp" in data and "retention_period" not in data:
            violation = PrivacyViolation(
                violation_type=PrivacyViolationType.RETENTION_VIOLATION,
                severity="medium",
                description="Data missing retention period metadata",
                data_subject=self._extract_data_subject_id(data),
                timestamp=datetime.now(),
                remediation_required=True,
                remediation_deadline=datetime.now() + timedelta(days=3),
                metadata={
                    "context": context,
                    "data_classification": classification.value,
                    "required_retention_period": retention_period.value
                }
            )
            violations.append(violation)

        # Check if data has exceeded retention period
        if "created_timestamp" in data and retention_period.value > 0:
            created_date = datetime.fromisoformat(data["created_timestamp"])
            retention_deadline = created_date + timedelta(days=retention_period.value)

            if datetime.now() > retention_deadline:
                violation = PrivacyViolation(
                    violation_type=PrivacyViolationType.RETENTION_VIOLATION,
                    severity="high",
                    description="Data exceeded retention period",
                    data_subject=self._extract_data_subject_id(data),
                    timestamp=datetime.now(),
                    remediation_required=True,
                    remediation_deadline=datetime.now() + timedelta(days=1),
                    metadata={
                        "context": context,
                        "created_date": created_date.isoformat(),
                        "retention_deadline": retention_deadline.isoformat(),
                        "days_overdue": (datetime.now() - retention_deadline).days
                    }
                )
                violations.append(violation)

        return violations

    def _check_access_control_compliance(self, data: Dict[str, Any], context: str) -> List[PrivacyViolation]:
        """Check access control compliance."""
        violations = []

        if not self.settings.role_based_access_enabled:
            return violations

        # Check if access is properly logged
        if "access_log" not in data:
            violation = PrivacyViolation(
                violation_type=PrivacyViolationType.ACCESS_LOG_MISSING,
                severity="medium",
                description="Access log missing for data access",
                data_subject=self._extract_data_subject_id(data),
                timestamp=datetime.now(),
                remediation_required=True,
                remediation_deadline=datetime.now() + timedelta(hours=12),
                metadata={
                    "context": context,
                    "access_logging_required": True
                }
            )
            violations.append(violation)

        return violations

    def process_data_subject_request(self, request: DataSubjectRequest) -> Dict[str, Any]:
        """Process data subject privacy rights request."""
        self.logger.info(f"Processing data subject request: {request.request_type} for {request.data_subject_id}")

        response = {
            "request_id": request.request_id,
            "status": "in_progress",
            "timestamp": datetime.now().isoformat(),
            "estimated_completion": request.completion_deadline.isoformat()
        }

        try:
            if request.request_type == "access":
                response.update(self._handle_data_access_request(request))
            elif request.request_type == "rectification":
                response.update(self._handle_data_rectification_request(request))
            elif request.request_type == "erasure":
                response.update(self._handle_data_erasure_request(request))
            elif request.request_type == "portability":
                response.update(self._handle_data_portability_request(request))
            else:
                response.update({
                    "status": "rejected",
                    "reason": f"Unsupported request type: {request.request_type}"
                })

        except Exception as e:
            self.logger.error(f"Error processing data subject request: {str(e)}")
            response.update({
                "status": "error",
                "error_message": str(e)
            })

        return response

    def _handle_data_access_request(self, request: DataSubjectRequest) -> Dict[str, Any]:
        """Handle data access request (right to access)."""
        # Implementation would retrieve all data for the data subject
        return {
            "status": "completed",
            "data_categories": ["customer_profile", "interaction_history", "preferences"],
            "data_format": "JSON",
            "access_method": "secure_download_link"
        }

    def _handle_data_rectification_request(self, request: DataSubjectRequest) -> Dict[str, Any]:
        """Handle data rectification request (right to rectification)."""
        # Implementation would update incorrect data
        return {
            "status": "completed",
            "fields_updated": request.request_details.get("fields_to_update", []),
            "update_timestamp": datetime.now().isoformat()
        }

    def _handle_data_erasure_request(self, request: DataSubjectRequest) -> Dict[str, Any]:
        """Handle data erasure request (right to be forgotten)."""
        # Implementation would delete personal data
        return {
            "status": "completed",
            "data_erased": True,
            "retention_exceptions": ["legal_obligations", "public_records"],
            "erasure_timestamp": datetime.now().isoformat()
        }

    def _handle_data_portability_request(self, request: DataSubjectRequest) -> Dict[str, Any]:
        """Handle data portability request (right to data portability)."""
        # Implementation would export data in machine-readable format
        return {
            "status": "completed",
            "export_format": "JSON",
            "export_size": "2.5MB",
            "download_expires": (datetime.now() + timedelta(days=30)).isoformat()
        }

    def _classify_data(self, data: Dict[str, Any], context: str) -> DataClassification:
        """Classify data based on content and context."""
        # Check for sensitive patterns
        for field_value in data.values():
            if isinstance(field_value, str):
                for pii_type, pattern in self.settings.SENSITIVE_DATA_PATTERNS.items():
                    if re.search(pattern, field_value, re.IGNORECASE):
                        if pii_type in ["ssn", "bank_account", "credit_card"]:
                            return DataClassification.RESTRICTED
                        else:
                            return DataClassification.CONFIDENTIAL

        # Check if it's public record information
        if self.settings.is_public_record_category(context):
            return DataClassification.PUBLIC

        # Check if it's restricted information
        if self.settings.is_restricted_information(context):
            return DataClassification.RESTRICTED

        # Default classification
        return DataClassification.CONFIDENTIAL

    def _extract_data_subject_id(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract data subject identifier from data."""
        possible_id_fields = ["customer_id", "user_id", "data_subject_id", "id"]
        for field in possible_id_fields:
            if field in data:
                return str(data[field])
        return None

    def _get_required_fields_for_context(self, context: str) -> List[str]:
        """Get required fields for specific context."""
        context_field_mapping = {
            "property_inquiry": ["property_id", "inquiry_type"],
            "payment_processing": ["property_id", "amount", "payment_method"],
            "assessment_appeal": ["property_id", "appeal_reason", "contact_info"],
            "exemption_application": ["property_id", "exemption_type", "eligibility_documents"],
            "general_inquiry": ["inquiry_type", "contact_preference"]
        }
        return context_field_mapping.get(context, self.settings.REQUIRED_TDLR_FIELDS)

    def _is_data_encrypted(self, data: Dict[str, Any]) -> bool:
        """Check if data is properly encrypted."""
        # Simple check for encryption indicators
        encrypted_indicators = ["encrypted", "cipher", "hash", "_enc"]
        for key in data.keys():
            if any(indicator in key.lower() for indicator in encrypted_indicators):
                return True

        # Check for encrypted value patterns (base64, hex, etc.)
        for value in data.values():
            if isinstance(value, str) and len(value) > 20:
                # Check for base64 pattern
                if re.match(r'^[A-Za-z0-9+/]*={0,2}$', value):
                    return True
                # Check for hex pattern
                if re.match(r'^[0-9a-fA-F]+$', value):
                    return True

        return False

    def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate comprehensive privacy compliance report."""
        total_violations = len(self.violations)
        critical_violations = len([v for v in self.violations if v.severity == "critical"])
        high_violations = len([v for v in self.violations if v.severity == "high"])

        violation_by_type = {}
        for violation in self.violations:
            violation_type = violation.violation_type.value
            violation_by_type[violation_type] = violation_by_type.get(violation_type, 0) + 1

        return {
            "report_timestamp": datetime.now().isoformat(),
            "compliance_summary": {
                "total_violations": total_violations,
                "critical_violations": critical_violations,
                "high_violations": high_violations,
                "compliance_score": max(0, 100 - (critical_violations * 20 + high_violations * 10))
            },
            "violation_breakdown": violation_by_type,
            "data_subject_requests": {
                "total_requests": len(self.data_subject_requests),
                "pending_requests": len([r for r in self.data_subject_requests if r.status == "pending"]),
                "completed_requests": len([r for r in self.data_subject_requests if r.status == "completed"])
            },
            "compliance_status": "compliant" if critical_violations == 0 else "non_compliant",
            "remediation_required": total_violations > 0,
            "next_audit_date": (datetime.now() + timedelta(days=30)).isoformat()
        }


# Example usage and testing
if __name__ == "__main__":
    validator = PrivacyComplianceValidator()

    # Test data with potential privacy issues
    test_data = {
        "customer_id": "CUST123456",
        "name": "John Doe",
        "ssn": "123-45-6789",
        "phone": "555-123-4567",
        "property_id": "PROP789012",
        "created_timestamp": "2024-01-01T00:00:00",
        "inquiry_type": "property_tax_calculation"
    }

    print("Testing privacy compliance validation...")
    violations = validator.validate_data_handling(test_data, "property_inquiry")

    print(f"\nFound {len(violations)} privacy violations:")
    for violation in violations:
        print(f"  - {violation.violation_type.value}: {violation.description} (Severity: {violation.severity})")

    print("\nGenerating compliance report...")
    report = validator.generate_compliance_report()
    print(f"Compliance Score: {report['compliance_summary']['compliance_score']}/100")
    print(f"Status: {report['compliance_status']}")