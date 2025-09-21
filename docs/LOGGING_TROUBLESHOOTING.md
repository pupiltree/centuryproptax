# Logging System Troubleshooting Guide

This guide provides solutions for common logging configuration issues and debugging procedures for the Century Property Tax application.

## Quick Diagnostics

### Check Current Logging Configuration
```bash
# View current environment variables
echo "LOG_LEVEL: $LOG_LEVEL"
echo "LOG_DIR: $LOG_DIR"
echo "LOG_FILE_ENABLED: $LOG_FILE_ENABLED"

# Check if log directory exists and is writable
ls -la logs/ 2>/dev/null || echo "Log directory not found"

# Check recent log entries
tail -f logs/app.log 2>/dev/null || echo "Log file not accessible"
```

### Test Logging Functionality
```python
# Quick logging test script
from src.core.logging import configure_logging, get_logger

# Configure logging
configure_logging()

# Test structured logging
logger = get_logger('test_component')
logger.info("Test message", event="test_event", test_field="test_value")

print("If you see the message above, logging is working correctly")
```

## Common Issues and Solutions

### 1. No Log Files Being Created

**Symptoms:**
- Console logging works but no log files appear
- Application runs without error but logs directory is empty

**Possible Causes & Solutions:**

#### LOG_FILE_ENABLED is disabled
```bash
# Check the setting
echo $LOG_FILE_ENABLED

# Enable file logging
export LOG_FILE_ENABLED=true
# Or add to .env file: LOG_FILE_ENABLED=true
```

#### Permission denied on log directory
```bash
# Check directory permissions
ls -la logs/

# Fix permissions
chmod 755 logs/
# Or for production: sudo chown app:app /var/log/centuryproptax
```

#### Log directory doesn't exist
```bash
# Check if directory exists
ls -d logs/ 2>/dev/null || echo "Directory missing"

# Create directory
mkdir -p logs/
# Or for production: sudo mkdir -p /var/log/centuryproptax
```

### 2. Log Level Not Working as Expected

**Symptoms:**
- Too many debug messages in production
- Missing error messages
- Inconsistent log verbosity

**Solutions:**

#### Verify log level setting
```bash
# Check current setting
echo "Current LOG_LEVEL: $LOG_LEVEL"

# Valid values (case-insensitive)
export LOG_LEVEL=INFO    # Recommended for production
export LOG_LEVEL=DEBUG   # For development only
export LOG_LEVEL=WARNING # Minimal logging
export LOG_LEVEL=ERROR   # Errors only
```

#### Test different log levels
```python
from src.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger('test')

logger.debug("Debug message - only visible with DEBUG level")
logger.info("Info message - visible with INFO and DEBUG levels")
logger.warning("Warning message - visible with WARNING and above")
logger.error("Error message - visible with ERROR and above")
```

### 3. Log Rotation Issues

**Symptoms:**
- Single large log file not rotating
- Missing compressed backup files
- Disk space filling up

**Solutions:**

#### Check log file size limits
```bash
# Check current log file size
ls -lh logs/app.log

# Default configuration: 100MB max file size, 10 backups
# Files should rotate automatically at 100MB
```

#### Verify backup files
```bash
# Check for rotated files
ls -la logs/app.log.*

# You should see:
# app.log.2.gz, app.log.3.gz, etc. (compressed backups)
```

#### Manual rotation test
```python
# Generate large log volume to trigger rotation
from src.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger('rotation_test')

# Generate ~1MB of log data
for i in range(10000):
    logger.info(f"Test message {i}", event="rotation_test", data="x" * 100)
```

### 4. Structured Logging Format Issues

**Symptoms:**
- Log entries missing required fields
- Validation warnings in logs
- Inconsistent log structure

**Solutions:**

#### Use structured logging helpers
```python
from src.core.logging import create_structured_log_entry, log_error_with_trace

# Correct way to create structured logs
entry = create_structured_log_entry(
    event="user_action",
    message="User performed action",
    user_id="user123",
    request_id="req456"
)
logger.info(**entry)

# For error logging with stack traces
try:
    # Some operation
    pass
except Exception as e:
    log_error_with_trace(
        logger,
        "operation_failed",
        "Operation failed unexpectedly",
        error=e,
        user_id="user123"
    )
```

#### Fix validation warnings
```python
# Common validation issues and fixes:

# ❌ Missing mandatory fields
logger.info("Simple message")

# ✅ Proper structured format
logger.info("User login successful",
           event="user_login",
           user_id="user123",
           component="auth")
```

### 5. Performance Issues

**Symptoms:**
- Application slowdown with logging enabled
- High CPU usage during logging
- Memory usage growing over time

**Solutions:**

#### Check log level in production
```bash
# Ensure production uses INFO or higher
echo $LOG_LEVEL
# Should be INFO, WARNING, ERROR, or CRITICAL in production
# Never use DEBUG in production
```

#### Monitor log volume
```bash
# Check log file growth rate
watch -n 5 'ls -lh logs/app.log'

# Check for excessive logging
grep -c "DEBUG\|INFO\|WARNING\|ERROR" logs/app.log
```

#### Optimize logging calls
```python
# ❌ Expensive operations in log calls
logger.debug(f"Complex calculation: {expensive_function()}")

# ✅ Conditional logging for expensive operations
if logger.isEnabledFor(logging.DEBUG):
    logger.debug(f"Complex calculation: {expensive_function()}")

# ✅ Use lazy evaluation
logger.debug("Result: %s", lambda: expensive_function())
```

### 6. Container/Docker Issues

**Symptoms:**
- No logs visible in Docker containers
- Permission errors in containers
- Log files not persisting

**Solutions:**

#### Configure for container logging
```dockerfile
# In Dockerfile
ENV LOG_FILE_ENABLED=false  # Use console logging only
ENV LOG_LEVEL=INFO

# Or mount log volume
VOLUME ["/app/logs"]
```

#### Docker Compose configuration
```yaml
# docker-compose.yml
services:
  app:
    environment:
      - LOG_LEVEL=INFO
      - LOG_DIR=/app/logs
      - LOG_FILE_ENABLED=true
    volumes:
      - ./logs:/app/logs  # Persist logs outside container
```

#### View container logs
```bash
# View application logs
docker logs centuryproptax-app

# Follow logs in real-time
docker logs -f centuryproptax-app

# View structured logs in JSON format
docker logs centuryproptax-app 2>&1 | jq .
```

### 7. Environment Variable Loading Issues

**Symptoms:**
- Environment variables not taking effect
- Default values being used despite setting variables
- Inconsistent behavior across environments

**Solutions:**

#### Verify environment variable loading
```python
import os
print("Environment variables loaded:")
print(f"LOG_LEVEL: {os.getenv('LOG_LEVEL', 'NOT_SET')}")
print(f"LOG_DIR: {os.getenv('LOG_DIR', 'NOT_SET')}")
print(f"LOG_FILE_ENABLED: {os.getenv('LOG_FILE_ENABLED', 'NOT_SET')}")
```

#### Check .env file loading
```bash
# Verify .env file exists and is readable
ls -la .env
cat .env | grep LOG_

# Source environment manually for testing
source .env
echo $LOG_LEVEL
```

#### Environment precedence
```bash
# Environment variable precedence (highest to lowest):
# 1. System environment variables
# 2. .env file variables
# 3. Default values in code

# Set system environment variable (highest precedence)
export LOG_LEVEL=DEBUG

# Verify it overrides .env file
python -c "import os; print(os.getenv('LOG_LEVEL'))"
```

## Debugging Procedures

### 1. Enable Debug Logging
```bash
# Temporarily enable debug logging
export LOG_LEVEL=DEBUG
python your_application.py

# Look for detailed logging configuration messages
grep "Logging configured" logs/app.log
```

### 2. Test Logging Components Individually
```python
# Test basic logging setup
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('test')
logger.info("Basic logging test")

# Test structlog
import structlog
structlog.configure()
logger = structlog.get_logger()
logger.info("Structlog test", component="test")

# Test custom logging module
from src.core.logging import configure_logging, get_logger
configure_logging()
logger = get_logger('custom_test')
logger.info("Custom logging test", event="test")
```

### 3. Validate Log Format
```bash
# Check if logs are properly formatted JSON
tail -n 1 logs/app.log | jq .

# Validate required fields are present
tail -n 10 logs/app.log | jq 'select(.timestamp and .level and .component and .event and .message)'
```

### 4. Performance Profiling
```python
import time
import cProfile
from src.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger('performance_test')

def logging_performance_test():
    start_time = time.time()
    for i in range(1000):
        logger.info(f"Test message {i}", event="performance_test", iteration=i)
    end_time = time.time()
    print(f"1000 log messages took {end_time - start_time:.3f} seconds")

# Profile logging performance
cProfile.run('logging_performance_test()')
```

## Getting Help

### Log Analysis Commands
```bash
# View recent errors
grep -E "(ERROR|CRITICAL)" logs/app.log | tail -20

# Count log levels
grep -o '"level":"[^"]*"' logs/app.log | sort | uniq -c

# Find validation warnings
grep "_validation_warning" logs/app.log

# Monitor log file growth
watch -n 1 'wc -l logs/app.log'
```

### Configuration Validation
```python
# Validate current logging configuration
from src.core.logging import (
    get_log_level, get_log_directory, is_file_logging_enabled
)

print(f"Effective log level: {get_log_level()}")
print(f"Effective log directory: {get_log_directory()}")
print(f"File logging enabled: {is_file_logging_enabled()}")
```

### Support Information to Collect
When reporting logging issues, include:

1. **Environment details:**
   ```bash
   echo "OS: $(uname -a)"
   echo "Python: $(python --version)"
   echo "LOG_LEVEL: $LOG_LEVEL"
   echo "LOG_DIR: $LOG_DIR"
   echo "LOG_FILE_ENABLED: $LOG_FILE_ENABLED"
   ```

2. **Current log configuration:**
   ```bash
   ls -la logs/
   tail -5 logs/app.log 2>/dev/null || echo "No log file"
   ```

3. **Recent error messages:**
   ```bash
   grep -E "(ERROR|CRITICAL)" logs/app.log | tail -10
   ```

4. **Application startup logs:**
   ```bash
   grep "Logging configured" logs/app.log
   ```

This troubleshooting guide covers the most common logging issues. For additional support, consult the developer documentation or contact the development team.