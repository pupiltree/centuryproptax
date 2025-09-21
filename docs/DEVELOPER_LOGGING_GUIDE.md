# Developer Logging Guide - Century Property Tax Application

This guide provides developers with comprehensive standards and best practices for implementing structured logging in the Century Property Tax application.

## Quick Start

### Basic Setup
```python
from src.core.logging import get_logger, create_structured_log_entry

# Get a logger for your component
logger = get_logger('your_component_name')

# Basic structured logging
logger.info("User login successful",
           event="user_login",
           user_id="user_123")

# Using the structured helper
entry = create_structured_log_entry(
    event="user_login",
    message="User login successful",
    user_id="user_123"
)
logger.info(**entry)
```

### Initialize Logging in Your Module
```python
# At the top of your module
from src.core.logging import ensure_logging_configured, get_logger

# Ensure logging is configured (safe to call multiple times)
ensure_logging_configured()

# Get component-specific logger
logger = get_logger(__name__)
```

## Structured Logging Standards

### Mandatory Fields
Every log entry must contain these fields:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `timestamp` | ISO string | When the event occurred | `2023-12-07T10:30:45.123Z` |
| `level` | string | Log level | `INFO`, `ERROR`, `DEBUG` |
| `component` | string | Source component/module | `whatsapp_client`, `property_validator` |
| `event` | string | What happened (machine-readable) | `user_login`, `property_validated` |
| `message` | string | Human-readable description | `User logged in successfully` |

### Optional Contextual Fields
Include these fields when relevant:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `user_id` | string | User identifier | `user_123` |
| `request_id` | string | Request tracking ID | `req_456` |
| `correlation_id` | string | Cross-service correlation | `corr_789` |
| `session_id` | string | User session identifier | `sess_abc` |
| `trace_id` | string | Distributed tracing ID | `trace_def` |
| `error_type` | string | Exception class name | `ValidationError` |
| `error_message` | string | Exception message | `Invalid property address` |
| `stack_trace` | string | Full stack trace | `Traceback (most recent call last)...` |

## Event Naming Conventions

### Standard Event Categories

#### User Events
- `user_login` - User authentication
- `user_logout` - User session termination
- `user_registration` - New user creation
- `user_profile_update` - Profile modifications

#### Property Tax Events
- `property_validated` - Property address/parcel validation
- `tax_calculated` - Tax amount calculation
- `deadline_checked` - Tax deadline lookup
- `consultation_scheduled` - Expert consultation booking
- `payment_processed` - Payment completion
- `document_generated` - Report/receipt creation

#### System Events
- `webhook_received` - WhatsApp webhook processing
- `api_request` - External API calls
- `database_query` - Database operations
- `file_upload` - File processing
- `cache_operation` - Cache hit/miss/update

#### Error Events
- `validation_failed` - Input validation errors
- `api_error` - External service failures
- `database_error` - Database operation failures
- `authentication_failed` - Auth failures
- `rate_limit_exceeded` - Rate limiting triggered

### Event Naming Rules
1. Use `snake_case` for all event names
2. Use verb_noun format: `action_subject`
3. Be specific but concise: `tax_calculated` not `calculation`
4. Use past tense: `user_logged_in` not `user_logging_in`

## Implementation Patterns

### 1. Component Logger Setup
```python
# module_name.py
from src.core.logging import ensure_logging_configured, get_logger

# Initialize logging once per module
ensure_logging_configured()
logger = get_logger(__name__)

class PropertyValidator:
    def __init__(self):
        # No need to reconfigure logging in __init__
        pass

    def validate_property(self, address: str, user_id: str) -> bool:
        logger.info("Starting property validation",
                   event="property_validation_started",
                   user_id=user_id,
                   address=address)

        try:
            # Validation logic here
            result = self._perform_validation(address)

            logger.info("Property validation completed",
                       event="property_validated",
                       user_id=user_id,
                       address=address,
                       is_valid=result.is_valid,
                       parcel_id=result.parcel_id)

            return result.is_valid

        except ValidationError as e:
            logger.error("Property validation failed",
                        event="property_validation_failed",
                        user_id=user_id,
                        address=address,
                        error_type=type(e).__name__,
                        error_message=str(e))
            raise
```

### 2. Error Logging with Stack Traces
```python
from src.core.logging import log_error_with_trace

def process_payment(payment_data: dict) -> PaymentResult:
    try:
        result = payment_gateway.process(payment_data)

        logger.info("Payment processed successfully",
                   event="payment_processed",
                   user_id=payment_data.get('user_id'),
                   amount=payment_data.get('amount'),
                   payment_id=result.payment_id)

        return result

    except PaymentGatewayError as e:
        # Use helper for error logging with stack trace
        log_error_with_trace(
            logger,
            event="payment_processing_failed",
            message="Payment gateway returned an error",
            error=e,
            user_id=payment_data.get('user_id'),
            amount=payment_data.get('amount'),
            gateway_error_code=e.error_code
        )
        raise

    except Exception as e:
        # Catch-all for unexpected errors
        log_error_with_trace(
            logger,
            event="payment_processing_error",
            message="Unexpected error during payment processing",
            error=e,
            user_id=payment_data.get('user_id'),
            payment_data=payment_data  # Include context for debugging
        )
        raise
```

### 3. Request Tracing and Correlation
```python
from src.core.logging import generate_correlation_id

async def webhook_handler(request: Request) -> Response:
    # Generate correlation ID for request tracing
    correlation_id = generate_correlation_id()

    # Bind correlation ID to logger for this request
    request_logger = logger.bind(correlation_id=correlation_id)

    request_logger.info("Webhook request received",
                       event="webhook_received",
                       method=request.method,
                       content_type=request.headers.get('content-type'),
                       content_length=request.headers.get('content-length'))

    try:
        # Process webhook
        message = await parse_webhook_message(request)

        request_logger.info("Webhook message parsed",
                           event="webhook_message_parsed",
                           message_type=message.type,
                           sender=message.sender,
                           message_id=message.id)

        response = await process_message(message, correlation_id)

        request_logger.info("Webhook processed successfully",
                           event="webhook_processed",
                           response_type=response.type,
                           processing_time_ms=response.processing_time)

        return response

    except Exception as e:
        log_error_with_trace(
            request_logger,
            event="webhook_processing_failed",
            message="Failed to process webhook request",
            error=e,
            request_method=request.method,
            request_url=str(request.url)
        )
        raise
```

### 4. Performance Logging
```python
import time
from functools import wraps

def log_performance(event_name: str):
    """Decorator to log function performance."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            logger.debug(f"Starting {func.__name__}",
                        event=f"{event_name}_started",
                        function=func.__name__)

            try:
                result = func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000

                logger.info(f"Completed {func.__name__}",
                           event=f"{event_name}_completed",
                           function=func.__name__,
                           execution_time_ms=round(execution_time, 2))

                return result

            except Exception as e:
                execution_time = (time.time() - start_time) * 1000

                log_error_with_trace(
                    logger,
                    event=f"{event_name}_failed",
                    message=f"Function {func.__name__} failed",
                    error=e,
                    function=func.__name__,
                    execution_time_ms=round(execution_time, 2)
                )
                raise

        return wrapper
    return decorator

# Usage
@log_performance("tax_calculation")
def calculate_property_tax(property_data: dict) -> TaxCalculation:
    # Tax calculation logic
    pass
```

### 5. Configuration-Aware Logging
```python
import os

def should_log_sensitive_data() -> bool:
    """Check if sensitive data logging is enabled."""
    return os.getenv('LOG_SENSITIVE_DATA', 'false').lower() == 'true'

def log_user_action(user_id: str, action: str, **context):
    """Log user action with optional sensitive data."""
    log_data = {
        'event': 'user_action',
        'user_id': user_id,
        'action': action
    }

    # Only include sensitive context in development
    if should_log_sensitive_data():
        log_data.update(context)
    else:
        # Sanitize sensitive fields
        sanitized_context = {
            k: v for k, v in context.items()
            if k not in ['password', 'token', 'api_key', 'ssn']
        }
        log_data.update(sanitized_context)

    logger.info("User action performed", **log_data)
```

## Best Practices

### 1. Log Levels

#### DEBUG
Use for detailed diagnostic information, typically only when diagnosing problems.

```python
# Detailed function entry/exit
logger.debug("Entering tax calculation function",
            event="function_entry",
            function="calculate_tax",
            parameters={'property_id': prop_id, 'year': tax_year})

# Variable states during processing
logger.debug("Intermediate calculation result",
            event="calculation_step",
            step="exemption_applied",
            base_amount=base_amount,
            exemption_amount=exemption_amount,
            remaining_amount=remaining_amount)
```

#### INFO
Use for general application flow and business events.

```python
# Business events
logger.info("Property tax calculation completed",
           event="tax_calculated",
           user_id=user_id,
           property_id=property_id,
           tax_amount=result.total_tax)

# Important state changes
logger.info("User consultation scheduled",
           event="consultation_scheduled",
           user_id=user_id,
           appointment_date=appointment.date,
           expert_id=appointment.expert_id)
```

#### WARNING
Use for unexpected situations that don't prevent operation.

```python
# Deprecated API usage
logger.warning("Using deprecated API endpoint",
              event="deprecated_api_used",
              endpoint="/api/v1/calculate",
              user_id=user_id,
              migration_deadline="2024-01-01")

# Performance issues
logger.warning("Database query took longer than expected",
              event="slow_query_detected",
              query_time_ms=query_time,
              threshold_ms=1000,
              query_type="property_lookup")
```

#### ERROR
Use for errors that affect functionality but allow continued operation.

```python
# External service failures
logger.error("Payment gateway returned error",
            event="payment_gateway_error",
            user_id=user_id,
            gateway_response_code=response.status_code,
            gateway_error_message=response.error_message)

# Validation failures
logger.error("Property validation failed",
            event="property_validation_failed",
            user_id=user_id,
            property_address=address,
            validation_errors=validation_result.errors)
```

#### CRITICAL
Use for serious errors that may cause system instability.

```python
# Database connection failures
logger.critical("Database connection lost",
                event="database_connection_lost",
                database_url=db_config.url,
                error_message=str(connection_error))

# Critical system resources exhausted
logger.critical("Disk space critically low",
                event="disk_space_critical",
                available_space_mb=available_space,
                threshold_mb=threshold)
```

### 2. Context Management
```python
# Use bound loggers for maintaining context
user_logger = logger.bind(user_id=user_id, session_id=session_id)

# All subsequent log calls will include user_id and session_id
user_logger.info("Property search initiated", event="property_search_started")
user_logger.info("Property found", event="property_found", property_id=prop_id)
user_logger.info("Search completed", event="property_search_completed")
```

### 3. Sensitive Data Handling
```python
def sanitize_log_data(data: dict) -> dict:
    """Remove sensitive fields from log data."""
    sensitive_fields = {
        'password', 'token', 'api_key', 'ssn', 'credit_card',
        'phone_number', 'email', 'address'
    }

    return {
        k: '[REDACTED]' if k.lower() in sensitive_fields else v
        for k, v in data.items()
    }

# Usage
user_data = {'name': 'John Doe', 'ssn': '123-45-6789', 'email': 'john@example.com'}
logger.info("User profile updated",
           event="user_profile_updated",
           user_id=user_id,
           updated_fields=list(user_data.keys()),
           **sanitize_log_data(user_data))
```

### 4. Performance Considerations
```python
import logging

# Use lazy evaluation for expensive operations
logger.debug("Complex data structure: %s", lambda: json.dumps(complex_object, indent=2))

# Check log level before expensive operations
if logger.isEnabledFor(logging.DEBUG):
    expensive_debug_info = generate_debug_report()
    logger.debug("Debug report generated",
                event="debug_report",
                report_data=expensive_debug_info)

# Avoid string formatting in log calls
# ❌ Bad - string formatting happens even if log level is too high
logger.debug(f"Processing item {item.id} with data {json.dumps(item.data)}")

# ✅ Good - formatting only happens if message will be logged
logger.debug("Processing item %s with data %s", item.id, lambda: json.dumps(item.data))
```

## Testing Logging

### Unit Tests for Logging
```python
import pytest
from unittest.mock import patch, MagicMock
from src.core.logging import get_logger

def test_user_login_logging():
    """Test that user login events are logged correctly."""
    with patch('src.core.logging.structlog.get_logger') as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Test the function that should log
        result = authenticate_user('user123', 'password')

        # Verify logging was called correctly
        mock_logger.info.assert_called_with(
            "User login successful",
            event="user_login",
            user_id="user123"
        )

def test_error_logging_with_trace():
    """Test that errors are logged with proper structure."""
    with patch('src.core.logging.log_error_with_trace') as mock_log_error:
        try:
            # Function that should raise and log error
            process_invalid_property("invalid_address")
        except ValidationError:
            pass

        # Verify error logging was called
        mock_log_error.assert_called_once()
        call_args = mock_log_error.call_args[1]
        assert call_args['event'] == 'property_validation_failed'
        assert 'error' in call_args
```

### Integration Tests for Log Output
```python
import tempfile
import json
from pathlib import Path

def test_structured_log_output():
    """Test that logs are properly structured."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Configure logging to use temp directory
        os.environ['LOG_DIR'] = temp_dir
        os.environ['LOG_LEVEL'] = 'INFO'

        # Import and configure logging
        from src.core.logging import configure_logging, get_logger
        configure_logging()

        # Generate test log
        logger = get_logger('test_component')
        logger.info("Test message",
                   event="test_event",
                   user_id="test_user")

        # Read and verify log file
        log_file = Path(temp_dir) / 'app.log'
        assert log_file.exists()

        with open(log_file) as f:
            log_line = f.readline().strip()
            log_data = json.loads(log_line)

        # Verify required fields
        assert log_data['level'] == 'info'
        assert log_data['component'] == 'test_component'
        assert log_data['event'] == 'test_event'
        assert log_data['user_id'] == 'test_user'
        assert 'timestamp' in log_data
```

## Common Patterns and Examples

### API Request Logging
```python
from fastapi import Request
from src.core.logging import generate_correlation_id

async def log_api_request(request: Request, call_next):
    """Middleware to log API requests with correlation IDs."""
    correlation_id = generate_correlation_id()
    start_time = time.time()

    # Add correlation ID to request state
    request.state.correlation_id = correlation_id

    # Log request start
    logger.info("API request started",
               event="api_request_started",
               correlation_id=correlation_id,
               method=request.method,
               url=str(request.url),
               user_agent=request.headers.get('user-agent'))

    try:
        response = await call_next(request)
        duration = (time.time() - start_time) * 1000

        # Log successful response
        logger.info("API request completed",
                   event="api_request_completed",
                   correlation_id=correlation_id,
                   status_code=response.status_code,
                   duration_ms=round(duration, 2))

        return response

    except Exception as e:
        duration = (time.time() - start_time) * 1000

        log_error_with_trace(
            logger,
            event="api_request_failed",
            message="API request failed with exception",
            error=e,
            correlation_id=correlation_id,
            duration_ms=round(duration, 2)
        )
        raise
```

### Business Logic Logging
```python
class PropertyTaxCalculator:
    def __init__(self):
        self.logger = get_logger('property_tax_calculator')

    def calculate_tax(self, property_data: dict, user_id: str) -> TaxResult:
        """Calculate property tax with comprehensive logging."""
        calculation_id = generate_correlation_id()
        calc_logger = self.logger.bind(
            calculation_id=calculation_id,
            user_id=user_id,
            property_id=property_data.get('property_id')
        )

        calc_logger.info("Tax calculation started",
                        event="tax_calculation_started",
                        property_type=property_data.get('type'),
                        assessed_value=property_data.get('assessed_value'))

        try:
            # Step 1: Base calculation
            base_tax = self._calculate_base_tax(property_data)
            calc_logger.debug("Base tax calculated",
                             event="base_tax_calculated",
                             base_tax_amount=base_tax)

            # Step 2: Apply exemptions
            exemptions = self._apply_exemptions(property_data, base_tax)
            calc_logger.debug("Exemptions applied",
                             event="exemptions_applied",
                             exemption_amount=exemptions.total_amount,
                             exemption_types=exemptions.types)

            # Step 3: Final calculation
            final_tax = base_tax - exemptions.total_amount

            result = TaxResult(
                base_tax=base_tax,
                exemptions=exemptions,
                final_tax=final_tax,
                calculation_id=calculation_id
            )

            calc_logger.info("Tax calculation completed",
                            event="tax_calculation_completed",
                            base_tax=base_tax,
                            total_exemptions=exemptions.total_amount,
                            final_tax=final_tax,
                            effective_rate=final_tax / property_data.get('assessed_value'))

            return result

        except ExemptionCalculationError as e:
            log_error_with_trace(
                calc_logger,
                event="exemption_calculation_failed",
                message="Failed to calculate property tax exemptions",
                error=e,
                property_data=property_data
            )
            raise

        except Exception as e:
            log_error_with_trace(
                calc_logger,
                event="tax_calculation_failed",
                message="Unexpected error during tax calculation",
                error=e,
                property_data=property_data
            )
            raise
```

This developer guide provides comprehensive standards for implementing consistent, structured logging throughout the Century Property Tax application. Following these patterns ensures logs are useful for debugging, monitoring, and business analytics while maintaining performance and security.