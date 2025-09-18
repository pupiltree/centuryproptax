"""
Compatibility shim for simplified_agent_v2.py
Redirects to the consolidated healthcare_assistant_v3.py

This file exists to maintain backward compatibility with existing scripts and CI/CD
that reference simplified_agent_v2. All functionality has been consolidated into
healthcare_assistant_v3.py following TRUE LangGraph patterns.
"""

# Import the consolidated healthcare assistant
from agents.core.healthcare_assistant_v3 import (
    get_healthcare_assistant,
    process_healthcare_message,
    HealthcareState
)

# Compatibility aliases for backward compatibility
get_simplified_agent_v2 = get_healthcare_assistant
SimplifiedDiagnosticsBot = get_healthcare_assistant

# Legacy function name mapping
def process_customer_message(message: str, session_id: str, customer_id: str):
    """Legacy function name - redirects to process_healthcare_message."""
    return process_healthcare_message(message, session_id, customer_id)

# Export commonly used items for import compatibility
__all__ = [
    'get_simplified_agent_v2',
    'SimplifiedDiagnosticsBot', 
    'process_customer_message',
    'process_healthcare_message',
    'HealthcareState'
]