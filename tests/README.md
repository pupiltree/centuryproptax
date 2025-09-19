# Test Suite

This directory contains comprehensive tests for the Century Property Tax AI Assistant.

## Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Pytest configuration and fixtures
├── run_tests.py             # Test runner script
├── README.md                # This file
├── test_config_generator.py # Configuration generation tests
├── test_state_manager.py    # State management tests  
├── test_message_handler.py  # Message handling tests
├── test_security.py         # Security component tests
├── test_api.py              # API endpoint tests
├── test_monitoring.py       # Monitoring system tests
└── integration/             # Integration tests (future)
    └── test_e2e.py          # End-to-end workflow tests
```

## Running Tests

### Using the Test Runner

```bash
# Run all tests
python tests/run_tests.py

# Run with verbose output
python tests/run_tests.py --verbose

# Run with coverage reporting
python tests/run_tests.py --coverage

# Run specific test file
python tests/run_tests.py --test test_config_generator.py

# Run specific test function
python tests/run_tests.py --specific test_config_generator.py::TestConfigurationGenerator::test_initialization

# Check test dependencies
python tests/run_tests.py --check-deps
```

### Using Pytest Directly

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=engine --cov-report=html

# Run specific test file
pytest tests/test_config_generator.py

# Run specific test class
pytest tests/test_config_generator.py::TestConfigurationGenerator

# Run specific test method
pytest tests/test_config_generator.py::TestConfigurationGenerator::test_initialization
```

## Test Categories

### Unit Tests
- Property tax tool tests - All 6 specialized tools
- WhatsApp message handling tests
- Payment processing tests (Razorpay & Mock)
- Conversation flow tests
- Database and state management tests

### API Tests
- WhatsApp webhook endpoint tests
- Health check and analytics tests
- Report management API tests

### Integration Tests (Future)
- End-to-end workflow tests
- Multi-component interaction tests
- External service integration tests

## Test Dependencies

Required packages for running tests:
- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking utilities
- `httpx` - HTTP client for API tests
- `fastapi[all]` - FastAPI with test client

Install with:
```bash
pip install pytest pytest-asyncio pytest-cov pytest-mock httpx "fastapi[all]"
```

## Test Configuration

### Fixtures
The `conftest.py` file provides common fixtures:
- `temp_db` - Temporary SQLite database
- `memory_state_manager` - In-memory state manager
- `sqlite_state_manager` - SQLite state manager  
- `sample_config` - Valid configuration for testing
- `config_generator` - Mock configuration generator
- `message_registry` - Message handler registry
- `sample_messages` - Test messages for different platforms
- `metrics_collector` - Metrics collection system
- `auth_manager` - Authentication manager
- `test_user` - Standard test user
- `admin_user` - Admin test user
- `engine_api` - FastAPI application instance

### Markers
Tests are marked with categories:
- `@pytest.mark.asyncio` - Async tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.security` - Security-related tests

## Mock Strategy

Tests use mocking for:
- External API calls (Gemini AI, WhatsApp Business API)
- Payment gateway interactions (Razorpay)
- File system operations
- Network requests
- Time-dependent operations

Real implementations are used for:
- Property tax calculation logic
- WhatsApp message processing
- LangGraph conversation flows
- Database models and persistence
- Property validation algorithms

## Coverage Goals

Target coverage levels:
- Property tax tools: 95%+
- WhatsApp API integration: 90%+
- Payment processing: 95%+
- Conversation flows: 90%+
- Database operations: 95%+
- Overall project: 85%+

## Continuous Testing

For development workflow:
```bash
# Watch mode (requires pytest-watch)
ptw tests/

# Run tests on file changes
find . -name "*.py" | entr pytest tests/
```

## Performance Testing

For performance-sensitive components:
```bash
# Run with timing
pytest tests/ --durations=10

# Profile specific tests
pytest tests/test_message_handler.py --profile
```

## Debugging Tests

```bash
# Run with detailed output
pytest tests/ -vvv

# Drop into debugger on failure
pytest tests/ --pdb

# Run last failed tests only
pytest tests/ --lf
```