"""
Security policies configuration - minimal stub for Microsoft Forms registration system.
"""

# Basic security settings for Microsoft Forms registration flow
SECURITY_POLICIES = {
    "rate_limiting": {
        "enabled": True,
        "requests_per_minute": 60
    },
    "form_validation": {
        "enabled": True,
        "max_field_length": 500
    },
    "logging": {
        "audit_trail": True,
        "security_events": True
    }
}