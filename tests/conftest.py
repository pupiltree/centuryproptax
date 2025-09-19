"""
Test configuration and fixtures for property tax tools tests.
"""

import pytest
import asyncio
import tempfile
import os
import sys
from pathlib import Path
from typing import Dict, Any
import yaml
import json

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def temp_db():
    """Create temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    yield db_path
    
    # Cleanup
    try:
        os.unlink(db_path)
    except OSError:
        pass

@pytest.fixture
def mock_state_data():
    """Mock state data for testing"""
    return {
        "conversation_id": "test_conv_123",
        "user_id": "test_user_456",
        "property_data": {
            "address": "123 Main St, Houston, TX",
            "value": 400000,
            "county": "harris"
        }
    }

@pytest.fixture
def sample_config():
    """Sample configuration for testing"""
    return {
        "version": "1.0",
        "agent": {
            "name": "Test Agent",
            "description": "Test chatbot agent",
            "llm": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "temperature": 0.1
            }
        },
        "tools": {
            "test_tool": {
                "enabled": True,
                "config": {
                    "param1": "value1"
                }
            }
        },
        "workflows": {
            "greeting": {
                "trigger": {
                    "type": "message",
                    "pattern": "hello|hi"
                },
                "steps": [
                    {
                        "type": "message",
                        "content": "Hello! How can I help you?"
                    }
                ]
            }
        },
        "integrations": {
            "messaging": {
                "instagram": {
                    "enabled": True,
                    "page_id": "test_page_id",
                    "access_token": "test_token"
                }
            }
        }
    }

@pytest.fixture
def property_tax_config():
    """Property tax specific configuration for testing"""
    return {
        "counties": ["harris", "dallas", "travis", "bexar", "tarrant", "collin"],
        "property_types": ["residential", "commercial", "agricultural"],
        "test_addresses": [
            "123 Main St, Houston, TX",
            "456 Oak Ave, Dallas, TX",
            "789 Pine Rd, Austin, TX"
        ]
    }

@pytest.fixture
def test_requirements():
    """Sample requirements for testing"""
    return """
    I need a customer service chatbot for my e-commerce business.
    
    Requirements:
    - Handle customer inquiries about orders, products, and shipping
    - Integrate with Instagram and WhatsApp
    - Connect to our existing CRM system
    - Provide order tracking capabilities
    - Handle returns and refunds
    - Escalate complex issues to human agents
    
    Business details:
    - Online clothing store
    - 1000+ orders per month  
    - Currently using Shopify
    - Customer support team of 5 people
    - Peak hours: 9 AM - 6 PM EST
    """

@pytest.fixture
def whatsapp_webhook_data():
    """WhatsApp webhook data for testing"""
    return {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "id": "wamid.123",
                        "from": "1234567890",
                        "timestamp": "1234567890",
                        "text": {"body": "I need help with my property tax"}
                    }]
                }
            }]
        }]
    }

@pytest.fixture
def config_yaml(sample_config):
    """YAML version of sample configuration"""
    return yaml.dump(sample_config, default_flow_style=False)

@pytest.fixture
def config_json(sample_config):
    """JSON version of sample configuration"""
    return json.dumps(sample_config, indent=2)

@pytest.fixture
def invalid_configs():
    """Invalid configurations for testing validation"""
    return {
        "missing_version": {
            "agent": {"name": "Test"}
        },
        "invalid_llm_provider": {
            "version": "1.0",
            "agent": {
                "name": "Test",
                "llm": {"provider": "invalid_provider"}
            }
        },
        "invalid_temperature": {
            "version": "1.0", 
            "agent": {
                "name": "Test",
                "llm": {
                    "provider": "openai",
                    "temperature": 5.0  # Too high
                }
            }
        },
        "malicious_content": {
            "version": "1.0",
            "agent": {
                "name": "<script>alert('xss')</script>",
                "description": "'; DROP TABLE users; --"
            }
        }
    }

# Helper functions for tests
def create_test_property_data(
    address: str = "123 Main St, Houston, TX",
    value: int = 400000,
    county: str = "harris",
    property_type: str = "residential"
) -> Dict[str, Any]:
    """Create test property data"""
    return {
        "address": address,
        "current_assessed_value": value,
        "county_code": county,
        "property_type": property_type,
        "year_built": 2005,
        "square_footage": 2000,
        "lot_size": 0.25
    }

async def wait_for_async(coro, timeout: float = 5.0):
    """Wait for async operation with timeout"""
    return await asyncio.wait_for(coro, timeout=timeout)