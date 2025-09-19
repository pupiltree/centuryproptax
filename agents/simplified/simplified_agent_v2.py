"""
Compatibility shim for simplified_agent_v2.py
Redirects to the consolidated property_tax_assistant_v3.py

This file exists to maintain backward compatibility with existing scripts and CI/CD
that reference simplified_agent_v2. All functionality has been consolidated into
property_tax_assistant_v3.py following TRUE LangGraph patterns.
"""

# Import the consolidated property tax assistant
from agents.core.property_tax_assistant_v3 import (
    get_property_tax_assistant,
    process_property_tax_message,
    PropertyTaxState
)

# Compatibility aliases for backward compatibility
get_simplified_agent_v2 = get_property_tax_assistant
SimplifiedPropertyTaxBot = get_property_tax_assistant

# Legacy function name mapping
def process_customer_message(message: str, session_id: str, customer_id: str):
    """Legacy function name - redirects to process_property_tax_message."""
    return process_property_tax_message(message, session_id, customer_id)

# Export commonly used items for import compatibility
__all__ = [
    'get_simplified_agent_v2',
    'SimplifiedPropertyTaxBot',
    'process_customer_message',
    'process_property_tax_message',
    'PropertyTaxState'
]