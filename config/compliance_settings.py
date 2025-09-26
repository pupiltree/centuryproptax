"""
Compliance settings configuration - minimal stub for Microsoft Forms registration system.
"""

# Basic compliance settings for Microsoft Forms registration flow
COMPLIANCE_SETTINGS = {
    "data_retention": {
        "conversation_logs_days": 365,
        "form_submissions_days": 2555  # 7 years
    },
    "privacy": {
        "data_anonymization": True,
        "consent_tracking": True
    },
    "audit": {
        "log_all_interactions": True,
        "include_user_agent": False,
        "include_ip_address": False
    },
    "texas_regulations": {
        "property_tax_compliance": True,
        "professional_licensing": True
    }
}