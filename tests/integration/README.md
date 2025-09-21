# Logging System Integration Tests

This directory contains comprehensive integration tests for the logging system that validate reliability across all deployment scenarios.

## Test Coverage

### TestStartupFailureScenarios
Tests application startup behavior under various failure conditions:
- **Missing log directory permissions**: Validates graceful fallback when log directories cannot be created
- **Filesystem full simulation**: Tests behavior when disk space is exhausted (Linux only)
- **Corrupted log files**: Handles existing corrupted or locked log files
- **Rapid configuration calls**: Ensures no resource leaks during rapid configuration

### TestEnvironmentVariableScenarios
Tests all environment variable combinations and edge cases:
- **Log level combinations**: All valid/invalid LOG_LEVEL values
- **Directory edge cases**: Various LOG_DIR path scenarios including special characters
- **File logging flags**: All LOG_FILE_ENABLED variations
- **Combined configurations**: Multiple environment variable combinations

### TestLogRotationIntegration
Tests log rotation under high volume and stress conditions:
- **High volume stress**: 10,000+ messages with multiple threads
- **System load**: Rotation behavior under CPU pressure
- **Disk space pressure**: Behavior when disk space is limited
- **Compression validation**: Ensures compressed files are readable

### TestCrossEnvironmentCompatibility
Tests behavior in various deployment environments:
- **Container simulation**: Tests container-like environment variables
- **Production environment**: WARNING+ log levels with structured logging
- **Development environment**: DEBUG level with full logging
- **Docker containers**: Actual Docker container testing (when available)

### TestMemoryAndResourceConstraints
Tests behavior under resource constraints:
- **Memory pressure**: Logging functionality under memory allocation stress
- **Signal handling**: Resource cleanup on SIGTERM/SIGINT
- **File handle limits**: Behavior when approaching system limits
- **Concurrent access**: Multi-threaded access to log files

### TestCICompatibility
Tests compatibility with CI/CD environments:
- **GitHub Actions**: Environment variables and logging patterns
- **Automated testing**: Test execution with verbose logging

## Test Requirements

### Required Dependencies
- `pytest`: Test framework
- `structlog`: Structured logging (from main application)

### Optional Dependencies (Tests skip if not available)
- `docker`: For actual container testing
- `psutil`: For detailed memory monitoring

### System Requirements
- **Linux**: Full test suite including filesystem simulation
- **Other OS**: Core tests (some advanced tests may be skipped)
- **Root access**: Some tests require sudo for loop device creation

## Running Tests

### All Integration Tests
```bash
python -m pytest tests/integration/ -v
```

### Specific Test Categories
```bash
# Startup failure scenarios
python -m pytest tests/integration/test_logging_integration.py::TestStartupFailureScenarios -v

# Environment variable testing
python -m pytest tests/integration/test_logging_integration.py::TestEnvironmentVariableScenarios -v

# Log rotation testing
python -m pytest tests/integration/test_logging_integration.py::TestLogRotationIntegration -v

# Cross-environment compatibility
python -m pytest tests/integration/test_logging_integration.py::TestCrossEnvironmentCompatibility -v

# Memory and resource constraints
python -m pytest tests/integration/test_logging_integration.py::TestMemoryAndResourceConstraints -v

# CI/CD compatibility
python -m pytest tests/integration/test_logging_integration.py::TestCICompatibility -v
```

### Integration Tests Only
```bash
python tests/run_tests.py --integration
```

### Slow Tests
Some tests are marked as slow (> 5 seconds). To skip them:
```bash
python -m pytest tests/integration/ -v -m "not slow"
```

### Docker Tests
Tests requiring Docker are automatically skipped if Docker is not available:
```bash
python -m pytest tests/integration/ -v -m "requires_docker"
```

## Test Configuration

### Markers
- `integration`: All tests in this directory
- `slow`: Tests that take more than 5 seconds
- `requires_docker`: Tests requiring Docker
- `requires_root`: Tests requiring root/sudo access

### Environment Variables
Tests automatically isolate environment variables and clean up after execution.

### Temporary Directories
All tests use temporary directories that are automatically cleaned up.

## CI/CD Integration

These tests are designed to run in CI/CD environments:

### GitHub Actions
```yaml
- name: Run Integration Tests
  run: python -m pytest tests/integration/ -v --tb=short
```

### Docker CI
```yaml
- name: Run Integration Tests with Docker
  run: |
    docker run --privileged -v /var/run/docker.sock:/var/run/docker.sock \
    python -m pytest tests/integration/ -v
```

## Test Results

### Expected Behavior
- All tests should pass in normal environments
- Tests gracefully skip when dependencies are unavailable
- Resource cleanup occurs even when tests fail
- No resource leaks or file handle exhaustion

### Performance Benchmarks
- High volume tests: > 5,000 messages/second
- Memory pressure: Handles 25MB+ allocation during logging
- Concurrent access: 10+ threads logging simultaneously
- Rotation stress: 20+ backup files with compression

## Troubleshooting

### Common Issues

**Docker tests failing**: Ensure Docker is installed and running
```bash
docker --version
sudo systemctl start docker
```

**Permission errors**: Some tests require write access to temporary directories
```bash
# Check temp directory permissions
ls -la /tmp
```

**Memory tests failing**: Reduce memory allocation in tests if system has < 1GB available RAM

**Loop device tests failing**: These require root access and are Linux-specific
```bash
# Check if loop devices are available
ls /dev/loop*
```

### Debug Logging
Enable debug logging for test troubleshooting:
```bash
LOG_LEVEL=DEBUG python -m pytest tests/integration/ -v -s
```

## Coverage

These integration tests provide comprehensive coverage for:
- ✅ Startup failure scenarios
- ✅ Environment variable edge cases
- ✅ Log rotation under stress
- ✅ Cross-environment compatibility
- ✅ Memory and resource constraints
- ✅ CI/CD environment compatibility
- ✅ Signal handling and cleanup
- ✅ Concurrent access patterns
- ✅ Compression and backup validation

This ensures the logging system is robust and reliable across all deployment scenarios.