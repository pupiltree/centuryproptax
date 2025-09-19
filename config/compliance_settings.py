"""TDLR compliance configuration and settings."""

import os
from datetime import timedelta
from typing import Dict, List, Optional
from enum import Enum
from dotenv import load_dotenv

load_dotenv()


class ComplianceLevel(Enum):
    """Compliance validation levels."""
    BASIC = "basic"
    ENHANCED = "enhanced"
    FULL_AUDIT = "full_audit"


class DataClassification(Enum):
    """Data classification levels per TDLR requirements."""
    PUBLIC = "public"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    PRIVATE = "private"


class RetentionPeriod(Enum):
    """Data retention periods per TDLR requirements."""
    IMMEDIATE = 0  # Delete immediately
    SHORT_TERM = 30  # 30 days
    MEDIUM_TERM = 365  # 1 year
    LONG_TERM = 2555  # 7 years (property tax records)
    PERMANENT = -1  # Permanent retention


class TDLRComplianceSettings:
    """TDLR compliance configuration and validation settings."""

    # TDLR Regulatory Compliance Configuration
    tdlr_compliance_mode: bool = os.getenv("TDLR_COMPLIANCE_MODE", "true").lower() == "true"
    compliance_validation_level: ComplianceLevel = ComplianceLevel(
        os.getenv("COMPLIANCE_VALIDATION_LEVEL", "enhanced")
    )

    # Data Privacy and Protection Settings
    data_encryption_required: bool = os.getenv("DATA_ENCRYPTION_REQUIRED", "true").lower() == "true"
    pii_detection_enabled: bool = os.getenv("PII_DETECTION_ENABLED", "true").lower() == "true"
    data_minimization_enabled: bool = os.getenv("DATA_MINIMIZATION_ENABLED", "true").lower() == "true"

    # Record Retention Configuration
    default_retention_period: RetentionPeriod = RetentionPeriod(
        int(os.getenv("DEFAULT_RETENTION_PERIOD", str(RetentionPeriod.LONG_TERM.value)))
    )

    # Data classification retention mapping
    RETENTION_POLICY: Dict[DataClassification, RetentionPeriod] = {
        DataClassification.PUBLIC: RetentionPeriod.PERMANENT,
        DataClassification.CONFIDENTIAL: RetentionPeriod.LONG_TERM,
        DataClassification.RESTRICTED: RetentionPeriod.LONG_TERM,
        DataClassification.PRIVATE: RetentionPeriod.MEDIUM_TERM
    }

    # Audit Trail Configuration
    audit_trail_enabled: bool = os.getenv("AUDIT_TRAIL_ENABLED", "true").lower() == "true"
    audit_retention_days: int = int(os.getenv("AUDIT_RETENTION_DAYS", "2555"))  # 7 years
    audit_compression_enabled: bool = os.getenv("AUDIT_COMPRESSION_ENABLED", "true").lower() == "true"

    # Texas Government Code Chapter 552 Configuration
    public_records_mode: bool = os.getenv("PUBLIC_RECORDS_MODE", "true").lower() == "true"
    information_request_tracking: bool = os.getenv("INFO_REQUEST_TRACKING", "true").lower() == "true"

    # Customer Communication Retention
    communication_retention_days: int = int(os.getenv("COMMUNICATION_RETENTION_DAYS", "2555"))  # 7 years
    conversation_archival_enabled: bool = os.getenv("CONVERSATION_ARCHIVAL_ENABLED", "true").lower() == "true"

    # Compliance Reporting Configuration
    regulatory_reporting_enabled: bool = os.getenv("REGULATORY_REPORTING_ENABLED", "true").lower() == "true"
    report_generation_schedule: str = os.getenv("REPORT_GENERATION_SCHEDULE", "monthly")
    compliance_report_retention_days: int = int(os.getenv("COMPLIANCE_REPORT_RETENTION_DAYS", "3650"))  # 10 years

    # Security and Access Control
    role_based_access_enabled: bool = os.getenv("RBAC_ENABLED", "true").lower() == "true"
    session_timeout_minutes: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
    failed_login_threshold: int = int(os.getenv("FAILED_LOGIN_THRESHOLD", "3"))

    # Data Subject Rights (Privacy)
    data_subject_request_tracking: bool = os.getenv("DATA_SUBJECT_REQUEST_TRACKING", "true").lower() == "true"
    data_portability_enabled: bool = os.getenv("DATA_PORTABILITY_ENABLED", "true").lower() == "true"
    right_to_erasure_enabled: bool = os.getenv("RIGHT_TO_ERASURE_ENABLED", "true").lower() == "true"

    # Compliance Monitoring and Alerting
    real_time_monitoring_enabled: bool = os.getenv("REAL_TIME_MONITORING_ENABLED", "true").lower() == "true"
    compliance_violation_alerts: bool = os.getenv("COMPLIANCE_VIOLATION_ALERTS", "true").lower() == "true"
    automated_remediation_enabled: bool = os.getenv("AUTOMATED_REMEDIATION_ENABLED", "false").lower() == "true"

    # External Compliance Services
    third_party_audit_integration: bool = os.getenv("THIRD_PARTY_AUDIT_INTEGRATION", "false").lower() == "true"
    compliance_service_api_url: Optional[str] = os.getenv("COMPLIANCE_SERVICE_API_URL")
    compliance_service_api_key: Optional[str] = os.getenv("COMPLIANCE_SERVICE_API_KEY")

    # TDLR Specific Requirements
    REQUIRED_TDLR_FIELDS: List[str] = [
        "customer_id",
        "property_id",
        "interaction_timestamp",
        "interaction_type",
        "data_classification",
        "retention_period",
        "access_log"
    ]

    # Sensitive Data Categories for TDLR Compliance
    SENSITIVE_DATA_PATTERNS: Dict[str, str] = {
        "ssn": r"\b\d{3}-?\d{2}-?\d{4}\b",
        "property_tax_id": r"\b\d{8,12}\b",
        "bank_account": r"\b\d{8,17}\b",
        "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
        "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    }

    # Public Records Categories (Texas Government Code Chapter 552)
    PUBLIC_RECORD_CATEGORIES: List[str] = [
        "property_assessments",
        "tax_rates",
        "exemption_eligibility",
        "appeal_procedures",
        "payment_schedules",
        "general_information"
    ]

    # Restricted Information Categories
    RESTRICTED_INFORMATION_CATEGORIES: List[str] = [
        "personal_financial_information",
        "private_property_details",
        "customer_payment_history",
        "confidential_appeals",
        "internal_assessments"
    ]

    @classmethod
    def validate_compliance_configuration(cls) -> Dict[str, bool]:
        """Validate compliance configuration completeness."""
        validation_results = {
            "tdlr_compliance_enabled": cls.tdlr_compliance_mode,
            "data_encryption_configured": cls.data_encryption_required,
            "audit_trail_configured": cls.audit_trail_enabled,
            "retention_policy_defined": bool(cls.RETENTION_POLICY),
            "public_records_compliance": cls.public_records_mode,
            "communication_retention_configured": cls.conversation_archival_enabled,
            "regulatory_reporting_enabled": cls.regulatory_reporting_enabled,
            "access_control_configured": cls.role_based_access_enabled,
            "monitoring_configured": cls.real_time_monitoring_enabled
        }

        return validation_results

    @classmethod
    def get_retention_period_for_classification(cls, classification: DataClassification) -> RetentionPeriod:
        """Get retention period for specific data classification."""
        return cls.RETENTION_POLICY.get(classification, cls.default_retention_period)

    @classmethod
    def is_public_record_category(cls, category: str) -> bool:
        """Check if data category is considered public record."""
        return category.lower() in [cat.lower() for cat in cls.PUBLIC_RECORD_CATEGORIES]

    @classmethod
    def is_restricted_information(cls, category: str) -> bool:
        """Check if data category is restricted information."""
        return category.lower() in [cat.lower() for cat in cls.RESTRICTED_INFORMATION_CATEGORIES]

    @classmethod
    def get_compliance_summary(cls) -> Dict[str, any]:
        """Get comprehensive compliance configuration summary."""
        return {
            "compliance_mode": cls.tdlr_compliance_mode,
            "validation_level": cls.compliance_validation_level.value,
            "data_protection": {
                "encryption_required": cls.data_encryption_required,
                "pii_detection": cls.pii_detection_enabled,
                "data_minimization": cls.data_minimization_enabled
            },
            "retention_policy": {
                "default_period": cls.default_retention_period.value,
                "communication_retention": cls.communication_retention_days,
                "audit_retention": cls.audit_retention_days
            },
            "public_records": {
                "mode_enabled": cls.public_records_mode,
                "request_tracking": cls.information_request_tracking,
                "categories_count": len(cls.PUBLIC_RECORD_CATEGORIES)
            },
            "monitoring": {
                "real_time": cls.real_time_monitoring_enabled,
                "violation_alerts": cls.compliance_violation_alerts,
                "automated_remediation": cls.automated_remediation_enabled
            },
            "external_integrations": {
                "third_party_audit": cls.third_party_audit_integration,
                "compliance_service": bool(cls.compliance_service_api_url)
            }
        }


# Global compliance settings instance
compliance_settings = TDLRComplianceSettings()

if __name__ == "__main__":
    print("TDLR Compliance Configuration Summary:")
    summary = compliance_settings.get_compliance_summary()
    for category, details in summary.items():
        print(f"\n{category.upper().replace('_', ' ')}:")
        if isinstance(details, dict):
            for key, value in details.items():
                print(f"  {key}: {value}")
        else:
            print(f"  {details}")

    print("\nCompliance Validation Results:")
    validation = compliance_settings.validate_compliance_configuration()
    for check, result in validation.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check.replace('_', ' ').title()}")