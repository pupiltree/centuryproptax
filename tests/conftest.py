"""
Test configuration and fixtures for the automation engine tests.
"""

import pytest
import asyncio
import tempfile
import os
from typing import Dict, Any
import yaml
import json

from engine.core.state_manager import StateManagerFactory, StateManagerConfig, StateBackend
from engine.generator.config_generator import ConfigurationGenerator
from engine.core.message_handler import MessageHandlerRegistry, Message, MessagePlatform, MessageDirection, MessageType
from engine.monitoring.metrics import MetricsCollector
from engine.monitoring.analytics import AnalyticsEngine
from engine.security.auth import AuthManager, User, UserRole
from engine.api.app import EngineAPI

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
async def memory_state_manager():
    """Create in-memory state manager for testing"""
    config = StateManagerConfig(backend=StateBackend.MEMORY)
    manager = StateManagerFactory.create_manager(config)
    await manager.initialize()
    
    yield manager
    
    await manager.cleanup()

@pytest.fixture
async def sqlite_state_manager(temp_db):
    """Create SQLite state manager for testing"""
    config = StateManagerConfig(
        backend=StateBackend.SQLITE,
        database_path=temp_db,
        async_mode=False
    )
    manager = StateManagerFactory.create_manager(config)
    await manager.initialize()
    
    yield manager
    
    await manager.cleanup()

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
def config_generator():
    """Configuration generator for testing"""
    # Mock configuration generator without real API keys
    return ConfigurationGenerator(
        provider="openai",
        model_name="gpt-4o-mini",
        api_key="test_key",
        temperature=0.1
    )

@pytest.fixture
def message_registry():
    """Message handler registry for testing"""
    return MessageHandlerRegistry()

@pytest.fixture
def sample_messages():
    """Sample messages for testing"""
    return [
        Message(
            id="msg_1",
            platform=MessagePlatform.INSTAGRAM,
            direction=MessageDirection.INBOUND,
            user_id="user_123",
            conversation_id="conv_123",
            message_type=MessageType.TEXT,
            content={"text": "Hello, I need help"},
            timestamp=1234567890.0
        ),
        Message(
            id="msg_2",
            platform=MessagePlatform.WHATSAPP,
            direction=MessageDirection.OUTBOUND,
            user_id="user_456",
            conversation_id="conv_456",
            message_type=MessageType.TEXT,
            content={"text": "How can I assist you today?"},
            timestamp=1234567891.0
        )
    ]

@pytest.fixture
def metrics_collector():
    """Metrics collector for testing"""
    return MetricsCollector(retention_seconds=300)  # 5 minutes for testing

@pytest.fixture
def analytics_engine():
    """Analytics engine for testing"""
    return AnalyticsEngine()

@pytest.fixture
def auth_manager():
    """Authentication manager for testing"""
    return AuthManager()

@pytest.fixture
def test_user(auth_manager):
    """Create a test user"""
    return auth_manager.create_user(
        username="testuser",
        password="testpass123",
        email="test@example.com",
        role=UserRole.USER
    )

@pytest.fixture
def admin_user(auth_manager):
    """Create an admin user"""
    return auth_manager.create_user(
        username="admin",
        password="adminpass123", 
        email="admin@example.com",
        role=UserRole.ADMIN
    )

@pytest.fixture
async def engine_api(sample_config, memory_state_manager):
    """Engine API instance for testing"""
    config = {
        "state": {
            "backend": "memory"
        },
        "llm": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "api_key": "test_key"
        }
    }
    
    api = EngineAPI(config)
    await api.initialize()
    
    yield api
    
    await api.cleanup()

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
def webhook_data():
    """Sample webhook data for testing"""
    return {
        "instagram": {
            "entry": [{
                "messaging": [{
                    "sender": {"id": "123456789"},
                    "recipient": {"id": "987654321"},
                    "timestamp": 1234567890000,
                    "message": {
                        "mid": "msg_id_123",
                        "text": "Hello, I need help with my order"
                    }
                }]
            }]
        },
        "whatsapp": {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "id": "wamid.123",
                            "from": "1234567890",
                            "timestamp": "1234567890",
                            "text": {"body": "Hi, can you help me?"}
                        }]
                    }
                }]
            }]
        },
        "telegram": {
            "message": {
                "message_id": 123,
                "from": {"id": 123456789, "first_name": "John"},
                "chat": {"id": 123456789, "type": "private"},
                "date": 1234567890,
                "text": "Hello bot!"
            }
        }
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
def create_test_message(
    platform: MessagePlatform = MessagePlatform.INSTAGRAM,
    direction: MessageDirection = MessageDirection.INBOUND,
    message_type: MessageType = MessageType.TEXT,
    content: Dict[str, Any] = None,
    user_id: str = "test_user"
) -> Message:
    """Create a test message"""
    if content is None:
        content = {"text": "Test message"}
    
    return Message(
        id=f"test_msg_{hash(str(content))}",
        platform=platform,
        direction=direction,
        user_id=user_id,
        conversation_id=f"conv_{user_id}",
        message_type=message_type,
        content=content,
        timestamp=1234567890.0
    )

async def wait_for_async(coro, timeout: float = 5.0):
    """Wait for async operation with timeout"""
    return await asyncio.wait_for(coro, timeout=timeout)