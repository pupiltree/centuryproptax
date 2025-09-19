"""
Compatibility shim for integrated_webhook_handler.py
Redirects to the modern_integrated_webhook_handler.py

This file exists to maintain backward compatibility with existing scripts and CI/CD
that reference integrated_webhook_handler. All functionality has been moved to
modern_integrated_webhook_handler.py with improved architecture.
"""

# Import the modern integrated webhook handler
from services.messaging.modern_integrated_webhook_handler import (
    modern_integrated_webhook_handler,
    ModernIntegratedWebhookHandler
)

# Compatibility alias for backward compatibility  
integrated_webhook_handler = modern_integrated_webhook_handler

# Legacy class name mapping
IntegratedWebhookHandler = ModernIntegratedWebhookHandler

# Export commonly used items for import compatibility
__all__ = [
    'integrated_webhook_handler',
    'IntegratedWebhookHandler',
    'modern_integrated_webhook_handler',
    'ModernIntegratedWebhookHandler'
]