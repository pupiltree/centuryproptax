"""Security policies and configuration for TDLR compliance."""

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv

load_dotenv()


class SecurityLevel(Enum):
    """Security assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class VulnerabilityCategory(Enum):
    """Categories of security vulnerabilities."""
    INJECTION = "injection"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_EXPOSURE = "data_exposure"
    CONFIGURATION = "configuration"
    CRYPTOGRAPHY = "cryptography"
    LOGGING = "logging"
    VALIDATION = "validation"
    SESSION_MANAGEMENT = "session_management"
    INFRASTRUCTURE = "infrastructure"


class ComplianceFramework(Enum):
    """Security compliance frameworks."""
    NIST_CSF = "nist_csf"
    SOC2_TYPE_II = "soc2_type_ii"
    WCAG_2_1_AA = "wcag_2_1_aa"
    TDLR_REQUIREMENTS = "tdlr_requirements"
    OWASP_TOP_10 = "owasp_top_10"


@dataclass
class SecurityPolicy:
    """Security policy definition."""
    policy_id: str
    name: str
    description: str
    category: VulnerabilityCategory
    severity: SecurityLevel
    compliance_frameworks: List[ComplianceFramework]
    validation_rules: List[str]
    remediation_guidance: str
    mandatory: bool


@dataclass
class SecurityConfiguration:
    """Security configuration parameters."""
    encryption_required: bool
    min_password_length: int
    session_timeout_minutes: int
    max_login_attempts: int
    require_mfa: bool
    audit_logging_enabled: bool
    data_classification_required: bool
    vulnerability_scan_frequency: str
    penetration_test_frequency: str


class SecurityPolicies:
    """Comprehensive security policies for TDLR compliance."""

    # Security Configuration
    ENCRYPTION_REQUIRED = os.getenv("ENCRYPTION_REQUIRED", "true").lower() == "true"
    MIN_PASSWORD_LENGTH = int(os.getenv("MIN_PASSWORD_LENGTH", "12"))
    SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
    MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "3"))
    REQUIRE_MFA = os.getenv("REQUIRE_MFA", "true").lower() == "true"
    AUDIT_LOGGING_ENABLED = os.getenv("AUDIT_LOGGING_ENABLED", "true").lower() == "true"

    # Vulnerability Scanning Configuration
    VULNERABILITY_SCAN_FREQUENCY = os.getenv("VULNERABILITY_SCAN_FREQUENCY", "weekly")
    PENETRATION_TEST_FREQUENCY = os.getenv("PENETRATION_TEST_FREQUENCY", "quarterly")
    AUTOMATED_SECURITY_TESTING = os.getenv("AUTOMATED_SECURITY_TESTING", "true").lower() == "true"

    # Data Protection Policies
    DATA_CLASSIFICATION_REQUIRED = os.getenv("DATA_CLASSIFICATION_REQUIRED", "true").lower() == "true"
    PII_ENCRYPTION_MANDATORY = os.getenv("PII_ENCRYPTION_MANDATORY", "true").lower() == "true"
    DATA_RETENTION_ENFORCEMENT = os.getenv("DATA_RETENTION_ENFORCEMENT", "true").lower() == "true"

    # Security Policies Database
    SECURITY_POLICIES: List[SecurityPolicy] = [
        # Authentication Policies
        SecurityPolicy(
            policy_id="AUTH_001",
            name="Strong Password Requirements",
            description="Enforce strong password policies for all user accounts",
            category=VulnerabilityCategory.AUTHENTICATION,
            severity=SecurityLevel.HIGH,
            compliance_frameworks=[ComplianceFramework.NIST_CSF, ComplianceFramework.SOC2_TYPE_II],
            validation_rules=[
                "password_length >= 12",
                "contains_uppercase",
                "contains_lowercase",
                "contains_number",
                "contains_special_character",
                "not_in_common_passwords"
            ],
            remediation_guidance="Implement password complexity requirements and validation",
            mandatory=True
        ),
        SecurityPolicy(
            policy_id="AUTH_002",
            name="Multi-Factor Authentication",
            description="Require MFA for all administrative and sensitive access",
            category=VulnerabilityCategory.AUTHENTICATION,
            severity=SecurityLevel.CRITICAL,
            compliance_frameworks=[ComplianceFramework.NIST_CSF, ComplianceFramework.SOC2_TYPE_II],
            validation_rules=[
                "mfa_enabled_for_admins",
                "mfa_enabled_for_sensitive_data_access",
                "backup_authentication_methods"
            ],
            remediation_guidance="Deploy MFA solution with backup recovery methods",
            mandatory=True
        ),
        SecurityPolicy(
            policy_id="AUTH_003",
            name="Session Management",
            description="Secure session management and timeout controls",
            category=VulnerabilityCategory.SESSION_MANAGEMENT,
            severity=SecurityLevel.HIGH,
            compliance_frameworks=[ComplianceFramework.OWASP_TOP_10, ComplianceFramework.NIST_CSF],
            validation_rules=[
                "session_timeout <= 30_minutes",
                "secure_session_tokens",
                "session_invalidation_on_logout",
                "concurrent_session_limits"
            ],
            remediation_guidance="Implement secure session management with proper timeouts",
            mandatory=True
        ),

        # Authorization Policies
        SecurityPolicy(
            policy_id="AUTHZ_001",
            name="Role-Based Access Control",
            description="Implement least privilege access control",
            category=VulnerabilityCategory.AUTHORIZATION,
            severity=SecurityLevel.HIGH,
            compliance_frameworks=[ComplianceFramework.SOC2_TYPE_II, ComplianceFramework.NIST_CSF],
            validation_rules=[
                "rbac_implemented",
                "least_privilege_principle",
                "regular_access_reviews",
                "privilege_escalation_controls"
            ],
            remediation_guidance="Deploy comprehensive RBAC with regular access reviews",
            mandatory=True
        ),
        SecurityPolicy(
            policy_id="AUTHZ_002",
            name="API Authorization",
            description="Secure API endpoint authorization",
            category=VulnerabilityCategory.AUTHORIZATION,
            severity=SecurityLevel.HIGH,
            compliance_frameworks=[ComplianceFramework.OWASP_TOP_10],
            validation_rules=[
                "api_authentication_required",
                "endpoint_authorization_checks",
                "resource_level_permissions",
                "rate_limiting_implemented"
            ],
            remediation_guidance="Implement API gateway with comprehensive authorization",
            mandatory=True
        ),

        # Data Protection Policies
        SecurityPolicy(
            policy_id="DATA_001",
            name="Data Encryption at Rest",
            description="Encrypt all sensitive data at rest",
            category=VulnerabilityCategory.CRYPTOGRAPHY,
            severity=SecurityLevel.CRITICAL,
            compliance_frameworks=[ComplianceFramework.SOC2_TYPE_II, ComplianceFramework.TDLR_REQUIREMENTS],
            validation_rules=[
                "database_encryption_enabled",
                "file_system_encryption",
                "encryption_key_management",
                "strong_encryption_algorithms"
            ],
            remediation_guidance="Deploy full database and filesystem encryption",
            mandatory=True
        ),
        SecurityPolicy(
            policy_id="DATA_002",
            name="Data Encryption in Transit",
            description="Encrypt all data transmissions",
            category=VulnerabilityCategory.CRYPTOGRAPHY,
            severity=SecurityLevel.CRITICAL,
            compliance_frameworks=[ComplianceFramework.SOC2_TYPE_II, ComplianceFramework.NIST_CSF],
            validation_rules=[
                "tls_1_3_minimum",
                "certificate_validation",
                "no_plaintext_transmission",
                "api_encryption_required"
            ],
            remediation_guidance="Enforce TLS 1.3+ for all communications",
            mandatory=True
        ),
        SecurityPolicy(
            policy_id="DATA_003",
            name="Data Classification and Handling",
            description="Classify and handle data according to sensitivity",
            category=VulnerabilityCategory.DATA_EXPOSURE,
            severity=SecurityLevel.HIGH,
            compliance_frameworks=[ComplianceFramework.TDLR_REQUIREMENTS, ComplianceFramework.SOC2_TYPE_II],
            validation_rules=[
                "data_classification_implemented",
                "handling_procedures_defined",
                "access_controls_by_classification",
                "retention_policies_enforced"
            ],
            remediation_guidance="Implement data classification with appropriate controls",
            mandatory=True
        ),

        # Input Validation Policies
        SecurityPolicy(
            policy_id="INPUT_001",
            name="Input Validation and Sanitization",
            description="Validate and sanitize all user inputs",
            category=VulnerabilityCategory.INJECTION,
            severity=SecurityLevel.HIGH,
            compliance_frameworks=[ComplianceFramework.OWASP_TOP_10],
            validation_rules=[
                "input_validation_all_endpoints",
                "sql_injection_prevention",
                "xss_prevention",
                "command_injection_prevention",
                "file_upload_validation"
            ],
            remediation_guidance="Implement comprehensive input validation framework",
            mandatory=True
        ),

        # Configuration Security Policies
        SecurityPolicy(
            policy_id="CONFIG_001",
            name="Secure Configuration Management",
            description="Maintain secure system and application configurations",
            category=VulnerabilityCategory.CONFIGURATION,
            severity=SecurityLevel.MEDIUM,
            compliance_frameworks=[ComplianceFramework.NIST_CSF, ComplianceFramework.SOC2_TYPE_II],
            validation_rules=[
                "default_credentials_changed",
                "unnecessary_services_disabled",
                "security_headers_configured",
                "error_handling_secure"
            ],
            remediation_guidance="Harden all system and application configurations",
            mandatory=True
        ),

        # Logging and Monitoring Policies
        SecurityPolicy(
            policy_id="LOG_001",
            name="Security Logging and Monitoring",
            description="Comprehensive security event logging and monitoring",
            category=VulnerabilityCategory.LOGGING,
            severity=SecurityLevel.HIGH,
            compliance_frameworks=[ComplianceFramework.SOC2_TYPE_II, ComplianceFramework.TDLR_REQUIREMENTS],
            validation_rules=[
                "security_events_logged",
                "log_integrity_protection",
                "real_time_monitoring",
                "incident_response_procedures"
            ],
            remediation_guidance="Deploy SIEM solution with real-time monitoring",
            mandatory=True
        ),

        # Infrastructure Security Policies
        SecurityPolicy(
            policy_id="INFRA_001",
            name="Infrastructure Security",
            description="Secure infrastructure configuration and management",
            category=VulnerabilityCategory.INFRASTRUCTURE,
            severity=SecurityLevel.HIGH,
            compliance_frameworks=[ComplianceFramework.NIST_CSF],
            validation_rules=[
                "network_segmentation",
                "firewall_configuration",
                "intrusion_detection_system",
                "vulnerability_management"
            ],
            remediation_guidance="Implement defense-in-depth infrastructure security",
            mandatory=True
        ),

        # Accessibility Policies (WCAG 2.1 AA)
        SecurityPolicy(
            policy_id="ACCESS_001",
            name="Web Accessibility Compliance",
            description="Ensure WCAG 2.1 AA accessibility compliance",
            category=VulnerabilityCategory.CONFIGURATION,
            severity=SecurityLevel.MEDIUM,
            compliance_frameworks=[ComplianceFramework.WCAG_2_1_AA],
            validation_rules=[
                "keyboard_navigation_support",
                "screen_reader_compatibility",
                "color_contrast_compliance",
                "alt_text_for_images",
                "focus_indicators",
                "semantic_html_structure"
            ],
            remediation_guidance="Implement comprehensive accessibility features",
            mandatory=True
        )
    ]

    # OWASP Top 10 Vulnerability Checks
    OWASP_TOP_10_CHECKS: Dict[str, Dict[str, Any]] = {
        "A01_broken_access_control": {
            "description": "Broken Access Control",
            "checks": [
                "vertical_privilege_escalation",
                "horizontal_privilege_escalation",
                "missing_access_controls",
                "cors_misconfiguration"
            ],
            "severity": SecurityLevel.CRITICAL
        },
        "A02_cryptographic_failures": {
            "description": "Cryptographic Failures",
            "checks": [
                "weak_encryption",
                "hardcoded_secrets",
                "insufficient_entropy",
                "deprecated_algorithms"
            ],
            "severity": SecurityLevel.HIGH
        },
        "A03_injection": {
            "description": "Injection Vulnerabilities",
            "checks": [
                "sql_injection",
                "nosql_injection",
                "command_injection",
                "ldap_injection",
                "xpath_injection"
            ],
            "severity": SecurityLevel.HIGH
        },
        "A04_insecure_design": {
            "description": "Insecure Design",
            "checks": [
                "threat_modeling",
                "secure_design_patterns",
                "defense_in_depth",
                "security_requirements"
            ],
            "severity": SecurityLevel.HIGH
        },
        "A05_security_misconfiguration": {
            "description": "Security Misconfiguration",
            "checks": [
                "default_configurations",
                "unnecessary_features",
                "missing_security_headers",
                "verbose_error_messages"
            ],
            "severity": SecurityLevel.MEDIUM
        },
        "A06_vulnerable_components": {
            "description": "Vulnerable and Outdated Components",
            "checks": [
                "outdated_dependencies",
                "vulnerable_libraries",
                "unpatched_systems",
                "unnecessary_components"
            ],
            "severity": SecurityLevel.HIGH
        },
        "A07_identification_failures": {
            "description": "Identification and Authentication Failures",
            "checks": [
                "weak_authentication",
                "session_management",
                "credential_stuffing",
                "brute_force_protection"
            ],
            "severity": SecurityLevel.HIGH
        },
        "A08_software_integrity": {
            "description": "Software and Data Integrity Failures",
            "checks": [
                "unsigned_code",
                "insecure_ci_cd",
                "auto_update_vulnerabilities",
                "serialization_attacks"
            ],
            "severity": SecurityLevel.MEDIUM
        },
        "A09_logging_failures": {
            "description": "Security Logging and Monitoring Failures",
            "checks": [
                "insufficient_logging",
                "log_tampering",
                "missing_monitoring",
                "ineffective_response"
            ],
            "severity": SecurityLevel.MEDIUM
        },
        "A10_ssrf": {
            "description": "Server-Side Request Forgery",
            "checks": [
                "ssrf_vulnerabilities",
                "url_validation",
                "network_segmentation",
                "allowlist_validation"
            ],
            "severity": SecurityLevel.MEDIUM
        }
    }

    # Security Testing Requirements
    SECURITY_TESTING_REQUIREMENTS = {
        "static_analysis": {
            "tools": ["bandit", "semgrep", "sonarqube"],
            "frequency": "every_commit",
            "coverage_threshold": 90
        },
        "dynamic_analysis": {
            "tools": ["owasp_zap", "burp_suite", "nikto"],
            "frequency": "weekly",
            "scope": "all_endpoints"
        },
        "dependency_scanning": {
            "tools": ["safety", "snyk", "owasp_dependency_check"],
            "frequency": "daily",
            "auto_remediation": True
        },
        "infrastructure_scanning": {
            "tools": ["nessus", "qualys", "openvas"],
            "frequency": "monthly",
            "scope": "all_infrastructure"
        }
    }

    # Compliance Mapping
    COMPLIANCE_MAPPING = {
        ComplianceFramework.NIST_CSF: {
            "identify": ["DATA_003", "CONFIG_001", "INFRA_001"],
            "protect": ["AUTH_001", "AUTH_002", "DATA_001", "DATA_002"],
            "detect": ["LOG_001", "INFRA_001"],
            "respond": ["LOG_001"],
            "recover": ["CONFIG_001", "INFRA_001"]
        },
        ComplianceFramework.SOC2_TYPE_II: {
            "security": ["AUTH_001", "AUTH_002", "AUTHZ_001", "DATA_001", "DATA_002"],
            "availability": ["INFRA_001", "CONFIG_001"],
            "confidentiality": ["DATA_001", "DATA_002", "DATA_003"],
            "processing_integrity": ["INPUT_001", "CONFIG_001"],
            "privacy": ["DATA_003", "LOG_001"]
        },
        ComplianceFramework.WCAG_2_1_AA: {
            "perceivable": ["ACCESS_001"],
            "operable": ["ACCESS_001"],
            "understandable": ["ACCESS_001"],
            "robust": ["ACCESS_001"]
        },
        ComplianceFramework.TDLR_REQUIREMENTS: {
            "data_protection": ["DATA_001", "DATA_002", "DATA_003"],
            "audit_requirements": ["LOG_001"],
            "access_control": ["AUTH_001", "AUTH_002", "AUTHZ_001"]
        }
    }

    @classmethod
    def get_policy_by_id(cls, policy_id: str) -> Optional[SecurityPolicy]:
        """Get security policy by ID."""
        for policy in cls.SECURITY_POLICIES:
            if policy.policy_id == policy_id:
                return policy
        return None

    @classmethod
    def get_policies_by_category(cls, category: VulnerabilityCategory) -> List[SecurityPolicy]:
        """Get all policies for a specific category."""
        return [policy for policy in cls.SECURITY_POLICIES if policy.category == category]

    @classmethod
    def get_policies_by_severity(cls, severity: SecurityLevel) -> List[SecurityPolicy]:
        """Get all policies for a specific severity level."""
        return [policy for policy in cls.SECURITY_POLICIES if policy.severity == severity]

    @classmethod
    def get_policies_by_framework(cls, framework: ComplianceFramework) -> List[SecurityPolicy]:
        """Get all policies for a specific compliance framework."""
        return [policy for policy in cls.SECURITY_POLICIES if framework in policy.compliance_frameworks]

    @classmethod
    def get_mandatory_policies(cls) -> List[SecurityPolicy]:
        """Get all mandatory security policies."""
        return [policy for policy in cls.SECURITY_POLICIES if policy.mandatory]

    @classmethod
    def validate_security_configuration(cls) -> Dict[str, Any]:
        """Validate current security configuration against policies."""
        validation_results = {
            "encryption_configured": cls.ENCRYPTION_REQUIRED,
            "password_policy_adequate": cls.MIN_PASSWORD_LENGTH >= 12,
            "session_timeout_appropriate": cls.SESSION_TIMEOUT_MINUTES <= 30,
            "mfa_required": cls.REQUIRE_MFA,
            "audit_logging_enabled": cls.AUDIT_LOGGING_ENABLED,
            "data_classification_enabled": cls.DATA_CLASSIFICATION_REQUIRED,
            "vulnerability_scanning_scheduled": cls.VULNERABILITY_SCAN_FREQUENCY in ["daily", "weekly"],
            "penetration_testing_scheduled": cls.PENETRATION_TEST_FREQUENCY in ["monthly", "quarterly"]
        }

        compliance_score = sum(1 for result in validation_results.values() if result) / len(validation_results) * 100

        return {
            "validation_results": validation_results,
            "compliance_score": compliance_score,
            "mandatory_policies_count": len(cls.get_mandatory_policies()),
            "total_policies_count": len(cls.SECURITY_POLICIES),
            "owasp_categories_covered": len(cls.OWASP_TOP_10_CHECKS),
            "compliance_frameworks_supported": len(cls.COMPLIANCE_MAPPING)
        }

    @classmethod
    def get_security_configuration(cls) -> SecurityConfiguration:
        """Get current security configuration."""
        return SecurityConfiguration(
            encryption_required=cls.ENCRYPTION_REQUIRED,
            min_password_length=cls.MIN_PASSWORD_LENGTH,
            session_timeout_minutes=cls.SESSION_TIMEOUT_MINUTES,
            max_login_attempts=cls.MAX_LOGIN_ATTEMPTS,
            require_mfa=cls.REQUIRE_MFA,
            audit_logging_enabled=cls.AUDIT_LOGGING_ENABLED,
            data_classification_required=cls.DATA_CLASSIFICATION_REQUIRED,
            vulnerability_scan_frequency=cls.VULNERABILITY_SCAN_FREQUENCY,
            penetration_test_frequency=cls.PENETRATION_TEST_FREQUENCY
        )


# Global security policies instance
security_policies = SecurityPolicies()

if __name__ == "__main__":
    print("Security Policies Configuration Summary:")

    validation = security_policies.validate_security_configuration()
    print(f"\nCompliance Score: {validation['compliance_score']:.1f}%")
    print(f"Mandatory Policies: {validation['mandatory_policies_count']}")
    print(f"Total Policies: {validation['total_policies_count']}")
    print(f"OWASP Categories: {validation['owasp_categories_covered']}")
    print(f"Compliance Frameworks: {validation['compliance_frameworks_supported']}")

    print(f"\nSecurity Configuration:")
    config = security_policies.get_security_configuration()
    print(f"  Encryption Required: {config.encryption_required}")
    print(f"  Min Password Length: {config.min_password_length}")
    print(f"  Session Timeout: {config.session_timeout_minutes} minutes")
    print(f"  MFA Required: {config.require_mfa}")
    print(f"  Audit Logging: {config.audit_logging_enabled}")

    print(f"\nCritical Policies:")
    critical_policies = security_policies.get_policies_by_severity(SecurityLevel.CRITICAL)
    for policy in critical_policies:
        print(f"  {policy.policy_id}: {policy.name}")

    print(f"\nCompliance Framework Coverage:")
    for framework in ComplianceFramework:
        policies = security_policies.get_policies_by_framework(framework)
        print(f"  {framework.value}: {len(policies)} policies")