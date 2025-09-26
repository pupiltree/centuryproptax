"""
Performance thresholds configuration - minimal stub for Microsoft Forms registration system.
"""

# Basic performance thresholds for Microsoft Forms registration flow
PERFORMANCE_THRESHOLDS = {
    "response_time": {
        "form_load": 2.0,  # seconds
        "form_submission": 3.0,  # seconds
        "api_response": 1.0  # seconds
    },
    "memory_usage": {
        "max_memory_mb": 512
    },
    "concurrent_users": {
        "max_concurrent": 100
    }
}