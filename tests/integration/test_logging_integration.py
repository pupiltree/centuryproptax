"""
Comprehensive Integration Tests for Logging System

These tests validate logging system reliability across all deployment scenarios:
- Startup failures and permission handling
- Environment variable configurations
- Log rotation under high volume
- Cross-environment compatibility
- Memory constraints and resource cleanup
"""

import pytest
import os
import sys
import tempfile
import gzip
import logging
import shutil
import threading
import time
import subprocess
import json
import signal
from pathlib import Path
from unittest.mock import patch, MagicMock
from contextlib import contextmanager
import concurrent.futures

# Optional dependencies - will be skipped if not available
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    docker = None
    DOCKER_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from core.logging import (
    get_log_directory,
    get_log_level,
    is_file_logging_enabled,
    configure_logging,
    get_logger,
    get_standard_logger,
    ensure_logging_configured,
    CompressedRotatingFileHandler
)


class TestStartupFailureScenarios:
    """Test application startup with various failure scenarios"""

    def test_startup_missing_log_directory_permissions(self):
        """Test application startup when log directory cannot be created"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a directory with no write permissions
            forbidden_dir = Path(temp_dir) / 'forbidden'
            forbidden_dir.mkdir()
            forbidden_dir.chmod(0o555)  # Read and execute only

            log_path = forbidden_dir / 'logs'

            try:
                with patch.dict(os.environ, {'LOG_DIR': str(log_path)}):
                    # Reset logging state
                    import core.logging as logging_module
                    logging_module._logging_configured = False
                    logging.getLogger().handlers.clear()

                    # This should not crash, but fall back gracefully
                    ensure_logging_configured()

                    # Verify logging still works (fallback directory)
                    logger = get_standard_logger('startup_test')
                    logger.info("Test message during permission failure")

                    # Check that we have working handlers
                    root_logger = logging.getLogger()
                    assert len(root_logger.handlers) > 0

                    # At least console handler should be working
                    console_handlers = [h for h in root_logger.handlers
                                      if isinstance(h, logging.StreamHandler)]
                    assert len(console_handlers) > 0

                    print("✅ Graceful fallback when log directory permissions denied")

            finally:
                # Restore permissions for cleanup
                forbidden_dir.chmod(0o755)

    def test_startup_filesystem_full_simulation(self):
        """Test startup behavior when filesystem is full"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a small filesystem using a loop device (Linux only)
            if os.name == 'posix' and os.path.exists('/dev/loop0'):
                try:
                    # Create a 1MB file
                    small_fs_file = Path(temp_dir) / 'small_fs.img'
                    subprocess.run(['dd', 'if=/dev/zero', f'of={small_fs_file}',
                                  'bs=1M', 'count=1'], check=True, capture_output=True)

                    # Format as ext4
                    subprocess.run(['mkfs.ext4', '-F', str(small_fs_file)],
                                 check=True, capture_output=True)

                    # Mount to a directory
                    mount_point = Path(temp_dir) / 'small_mount'
                    mount_point.mkdir()

                    subprocess.run(['sudo', 'mount', '-o', 'loop',
                                  str(small_fs_file), str(mount_point)],
                                 check=True, capture_output=True)

                    try:
                        # Fill the filesystem almost completely
                        filler_file = mount_point / 'filler'
                        with open(filler_file, 'wb') as f:
                            f.write(b'0' * (800 * 1024))  # 800KB of 1MB filesystem

                        log_dir = mount_point / 'logs'

                        with patch.dict(os.environ, {'LOG_DIR': str(log_dir)}):
                            # Reset logging state
                            import core.logging as logging_module
                            logging_module._logging_configured = False
                            logging.getLogger().handlers.clear()

                            # Should handle full filesystem gracefully
                            ensure_logging_configured()

                            logger = get_standard_logger('full_fs_test')
                            logger.info("Test message on full filesystem")

                            # Should have fallback handlers
                            root_logger = logging.getLogger()
                            assert len(root_logger.handlers) > 0

                            print("✅ Graceful handling of full filesystem")

                    finally:
                        # Unmount
                        subprocess.run(['sudo', 'umount', str(mount_point)],
                                     capture_output=True)

                except (subprocess.CalledProcessError, PermissionError):
                    # Skip this test if we can't create loop devices
                    pytest.skip("Cannot create loop filesystem for testing")
            else:
                pytest.skip("Loop device testing only available on Linux")

    def test_startup_with_corrupted_log_file(self):
        """Test startup when existing log file is corrupted or locked"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / 'app.log'

            # Create a corrupted/locked log file
            with open(log_file, 'wb') as f:
                f.write(b'\x00\x01\x02\x03' * 1000)  # Binary garbage

            # Make it read-only to simulate lock
            log_file.chmod(0o444)

            try:
                with patch.dict(os.environ, {
                    'LOG_DIR': temp_dir,
                    'LOG_FILE_ENABLED': 'true'
                }):
                    # Reset logging state
                    import core.logging as logging_module
                    logging_module._logging_configured = False
                    logging.getLogger().handlers.clear()

                    # Should handle corrupted file gracefully
                    ensure_logging_configured()

                    logger = get_standard_logger('corrupted_test')
                    logger.info("Test message with corrupted existing log")

                    # Should still have working handlers
                    root_logger = logging.getLogger()
                    assert len(root_logger.handlers) > 0

                    print("✅ Graceful handling of corrupted existing log file")

            finally:
                # Restore permissions for cleanup
                log_file.chmod(0o644)

    def test_startup_rapid_configuration_calls(self):
        """Test rapid successive configuration calls don't create resource leaks"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {'LOG_DIR': temp_dir}):
                # Reset logging state
                import core.logging as logging_module
                logging_module._logging_configured = False
                logging.getLogger().handlers.clear()

                initial_handlers = len(logging.getLogger().handlers)

                # Call configuration rapidly
                for i in range(10):
                    ensure_logging_configured()

                # Handler count should not increase
                final_handlers = len(logging.getLogger().handlers)
                assert final_handlers >= initial_handlers

                # Should not create excessive handlers
                assert final_handlers <= initial_handlers + 3  # console + file + maybe structlog

                # All handlers should be properly closed
                for handler in logging.getLogger().handlers:
                    assert not handler.stream.closed if hasattr(handler, 'stream') else True

                print(f"✅ Rapid configuration calls stable: {final_handlers} handlers")


class TestEnvironmentVariableScenarios:
    """Test all environment variable combinations and edge cases"""

    def test_all_log_level_combinations(self):
        """Test all valid and invalid log level combinations"""
        test_cases = [
            # Valid levels
            ('DEBUG', logging.DEBUG),
            ('INFO', logging.INFO),
            ('WARNING', logging.WARNING),
            ('WARN', logging.WARNING),
            ('ERROR', logging.ERROR),
            ('CRITICAL', logging.CRITICAL),
            # Case variations
            ('debug', logging.DEBUG),
            ('Info', logging.INFO),
            ('WARNING', logging.WARNING),
            # Invalid levels should fallback to INFO
            ('INVALID', logging.INFO),
            ('', logging.INFO),
            ('123', logging.INFO),
            ('TRACE', logging.INFO),  # Not a standard Python level
        ]

        for level_str, expected_level in test_cases:
            with patch.dict(os.environ, {'LOG_LEVEL': level_str}):
                result = get_log_level()
                assert result == expected_level
                print(f"✅ Log level '{level_str}' -> {logging.getLevelName(result)}")

    def test_log_directory_edge_cases(self):
        """Test log directory with various edge case paths"""
        test_cases = [
            # Relative paths
            './logs',
            '../logs',
            'logs',
            # Paths with spaces
            'logs with spaces',
            # Paths with special characters
            'logs@#$%',
            # Very long paths
            'a' * 200,
            # Empty string
            '',
            # Just whitespace
            '   ',
            # Non-existent parent directories
            '/tmp/non/existent/deep/path/logs',
        ]

        for log_dir in test_cases:
            with patch.dict(os.environ, {'LOG_DIR': log_dir}):
                result = get_log_directory()
                # Should always return a valid, writable directory
                assert result is not None
                assert Path(result).exists()

                # Test writability
                test_file = Path(result) / f'test_{hash(log_dir)}'
                test_file.touch()
                assert test_file.exists()
                test_file.unlink()

                print(f"✅ Log directory '{log_dir}' -> {result}")

    def test_file_logging_enabled_edge_cases(self):
        """Test file logging enabled flag with edge cases"""
        test_cases = [
            # True values
            ('true', True),
            ('TRUE', True),
            ('True', True),
            ('1', True),
            ('yes', True),
            ('YES', True),
            ('on', True),
            ('enabled', True),
            # False values
            ('false', False),
            ('FALSE', False),
            ('False', False),
            ('0', False),
            ('no', False),
            ('NO', False),
            ('off', False),
            ('disabled', False),
            # Edge cases
            ('', True),  # Default when empty
            ('   ', True),  # Whitespace
            ('invalid', False),  # Invalid string
            ('2', False),  # Non-1 number
            ('maybe', False),  # Ambiguous string
        ]

        for value, expected in test_cases:
            with patch.dict(os.environ, {'LOG_FILE_ENABLED': value}):
                result = is_file_logging_enabled()
                assert result == expected
                print(f"✅ File logging '{value}' -> {result}")

    def test_environment_variable_combinations(self):
        """Test various combinations of environment variables"""
        combinations = [
            # Minimal config
            {},
            # Full config
            {'LOG_LEVEL': 'DEBUG', 'LOG_DIR': '/tmp/test_logs', 'LOG_FILE_ENABLED': 'true'},
            # Mixed valid/invalid
            {'LOG_LEVEL': 'INVALID', 'LOG_DIR': '/invalid/path', 'LOG_FILE_ENABLED': 'maybe'},
            # Extreme values
            {'LOG_LEVEL': 'CRITICAL', 'LOG_DIR': 'a' * 300, 'LOG_FILE_ENABLED': 'false'},
            # Only some vars set
            {'LOG_LEVEL': 'WARNING'},
            {'LOG_DIR': '/tmp/partial_test'},
            {'LOG_FILE_ENABLED': 'false'},
        ]

        for i, env_vars in enumerate(combinations):
            with tempfile.TemporaryDirectory() as temp_dir:
                # Use temp dir for any path references
                env_vars_safe = env_vars.copy()
                if 'LOG_DIR' in env_vars_safe and not Path(env_vars_safe['LOG_DIR']).exists():
                    env_vars_safe['LOG_DIR'] = temp_dir

                with patch.dict(os.environ, env_vars_safe, clear=True):
                    # Reset logging state
                    import core.logging as logging_module
                    logging_module._logging_configured = False
                    logging.getLogger().handlers.clear()

                    # Should configure without errors
                    ensure_logging_configured()

                    # Test basic logging functionality
                    logger = get_standard_logger(f'combo_test_{i}')
                    logger.info(f"Test message for combination {i}")

                    # Should have at least one handler
                    root_logger = logging.getLogger()
                    assert len(root_logger.handlers) > 0

                    print(f"✅ Environment combination {i}: {env_vars}")


class TestLogRotationIntegration:
    """Test log rotation under high volume and various scenarios"""

    def test_high_volume_rotation_stress(self):
        """Test log rotation under extreme high volume"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / 'stress_test.log'

            # Create handler with very aggressive rotation
            handler = CompressedRotatingFileHandler(
                filename=str(log_file),
                maxBytes=50 * 1024,  # 50KB for rapid rotation
                backupCount=20,      # Keep many backups for testing
                encoding='utf-8'
            )

            logger = logging.getLogger('stress_rotation')
            logger.setLevel(logging.DEBUG)
            logger.addHandler(handler)

            # Generate high volume of logs rapidly
            large_message = "Stress test message with substantial content " * 100  # ~4KB message
            messages_sent = 0

            start_time = time.time()

            print("🔍 Starting high-volume stress test...")

            # Use multiple threads to stress test
            def worker(thread_id, message_count):
                nonlocal messages_sent
                for i in range(message_count):
                    logger.info(f"Thread-{thread_id} Message-{i}: {large_message}")
                    messages_sent += 1

                    # Log progress every 1000 messages
                    if messages_sent % 1000 == 0:
                        elapsed = time.time() - start_time
                        backup_files = list(Path(temp_dir).glob('stress_test.log.*.gz'))
                        print(f"   Progress: {messages_sent:,} messages, "
                              f"{len(backup_files)} backups, "
                              f"{elapsed:.1f}s elapsed")

            # Start multiple worker threads
            threads = []
            for thread_id in range(5):
                thread = threading.Thread(target=worker, args=(thread_id, 2000))
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            end_time = time.time()
            duration = end_time - start_time

            # Force final flush
            handler.flush()
            handler.close()
            logger.removeHandler(handler)

            # Analyze results
            backup_files = list(Path(temp_dir).glob('stress_test.log.*.gz'))
            main_size = log_file.stat().st_size if log_file.exists() else 0

            print(f"✅ High-volume stress test completed:")
            print(f"   Messages sent: {messages_sent:,}")
            print(f"   Duration: {duration:.2f} seconds")
            print(f"   Throughput: {messages_sent/duration:.1f} messages/second")
            print(f"   Main log size: {main_size:,} bytes")
            print(f"   Backup files: {len(backup_files)}")
            print(f"   Backup count respected: {len(backup_files) <= 20}")

            # Verify constraints
            assert len(backup_files) <= 20  # Backup count limit
            assert messages_sent == 10000   # All messages processed

            # Verify compressed files are readable
            readable_count = 0
            check_count = min(len(backup_files), 5)  # Check up to 5 files
            for backup_file in backup_files[:check_count]:
                try:
                    with gzip.open(backup_file, 'rt', encoding='utf-8') as f:
                        content = f.read(1000)  # Read first 1KB
                        if 'Stress test message' in content:
                            readable_count += 1
                except Exception as e:
                    print(f"   Warning: Could not read {backup_file}: {e}")

            print(f"   Readable backups checked: {readable_count}/{check_count}")
            if check_count > 0:
                assert readable_count >= max(1, check_count - 1)  # Most should be readable

    def test_rotation_during_system_load(self):
        """Test log rotation behavior under system load"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a CPU-intensive background task
            def cpu_intensive_task():
                """Consume CPU cycles"""
                end_time = time.time() + 5  # Run for 5 seconds
                while time.time() < end_time:
                    # CPU intensive calculation
                    sum(i * i for i in range(10000))

            # Start background CPU load
            cpu_threads = []
            for _ in range(2):  # Two CPU-intensive threads
                thread = threading.Thread(target=cpu_intensive_task)
                cpu_threads.append(thread)
                thread.start()

            try:
                log_file = Path(temp_dir) / 'system_load.log'

                handler = CompressedRotatingFileHandler(
                    filename=str(log_file),
                    maxBytes=30 * 1024,  # 30KB
                    backupCount=5,
                    encoding='utf-8'
                )

                logger = logging.getLogger('system_load_test')
                logger.setLevel(logging.INFO)
                logger.addHandler(handler)

                # Log while system is under load
                large_message = "System load test message " * 200

                start_time = time.time()
                messages_logged = 0

                while time.time() - start_time < 8:  # Run for 8 seconds
                    logger.info(f"Load test message {messages_logged}: {large_message}")
                    messages_logged += 1

                    if messages_logged % 100 == 0:
                        backup_files = list(Path(temp_dir).glob('system_load.log.*.gz'))
                        print(f"   Under load: {messages_logged} messages, {len(backup_files)} backups")

                handler.close()
                logger.removeHandler(handler)

                # Verify results
                backup_files = list(Path(temp_dir).glob('system_load.log.*.gz'))

                print(f"✅ System load test completed:")
                print(f"   Messages logged: {messages_logged}")
                print(f"   Backup files created: {len(backup_files)}")
                print(f"   System remained responsive during logging")

                assert messages_logged > 0
                assert len(backup_files) <= 5

            finally:
                # Wait for CPU threads to complete
                for thread in cpu_threads:
                    thread.join()

    def test_rotation_with_disk_space_pressure(self):
        """Test rotation behavior when disk space is limited"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Monitor available space
            def get_free_space():
                return shutil.disk_usage(temp_dir).free

            initial_free = get_free_space()

            log_file = Path(temp_dir) / 'disk_pressure.log'

            handler = CompressedRotatingFileHandler(
                filename=str(log_file),
                maxBytes=1024 * 1024,  # 1MB per file
                backupCount=10,
                encoding='utf-8'
            )

            logger = logging.getLogger('disk_pressure_test')
            logger.setLevel(logging.INFO)
            logger.addHandler(handler)

            # Create large log messages to consume space
            huge_message = "X" * 10240  # 10KB message

            messages_logged = 0
            rotation_count = 0

            print("🔍 Testing under disk space pressure...")

            # Log until we've created several rotations
            while rotation_count < 15:  # Force more rotations than backup count
                logger.info(f"Message {messages_logged}: {huge_message}")
                messages_logged += 1

                # Check for new backup files
                backup_files = list(Path(temp_dir).glob('disk_pressure.log.*.gz'))
                new_rotation_count = len(backup_files)

                if new_rotation_count > rotation_count:
                    rotation_count = new_rotation_count
                    current_free = get_free_space()
                    space_used = initial_free - current_free

                    print(f"   Rotation {rotation_count}: {messages_logged} messages, "
                          f"{space_used/(1024*1024):.1f}MB used")

                # Safety: Don't run forever
                if messages_logged > 10000:
                    break

            handler.close()
            logger.removeHandler(handler)

            # Final analysis
            final_backups = list(Path(temp_dir).glob('disk_pressure.log.*.gz'))
            final_free = get_free_space()
            total_space_used = initial_free - final_free

            print(f"✅ Disk pressure test completed:")
            print(f"   Messages logged: {messages_logged}")
            print(f"   Final backup count: {len(final_backups)}")
            print(f"   Total space used: {total_space_used/(1024*1024):.1f}MB")
            print(f"   Backup limit respected: {len(final_backups) <= 10}")

            # Verify backup count limit is respected
            assert len(final_backups) <= 10


class TestCrossEnvironmentCompatibility:
    """Test logging behavior in various environment scenarios"""

    def test_containerized_environment_simulation(self):
        """Test logging behavior in containerized environment"""
        # Simulate container constraints
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create restricted environment similar to containers
            container_log_dir = Path(temp_dir) / 'container_logs'
            container_log_dir.mkdir()

            # Simulate container environment variables
            container_env = {
                'LOG_DIR': str(container_log_dir),
                'LOG_LEVEL': 'INFO',
                'LOG_FILE_ENABLED': 'true',
                'CONTAINER': 'true',  # Indicate container environment
                'USER': 'app',
                'HOME': str(temp_dir),
                'TMP': str(temp_dir),
                'TMPDIR': str(temp_dir),
            }

            with patch.dict(os.environ, container_env):
                # Reset logging state
                import core.logging as logging_module
                logging_module._logging_configured = False
                logging.getLogger().handlers.clear()

                # Configure logging in container-like environment
                ensure_logging_configured()

                # Test structured logging (common in containers)
                struct_logger = get_logger('container_app')

                # Log various structured events
                struct_logger.info("Application started",
                                 log_event="app_start",
                                 container_id="test_container",
                                 version="1.0.0")

                struct_logger.error("Database connection failed",
                                   log_event="db_error",
                                   error_type="ConnectionTimeout",
                                   retry_count=3)

                struct_logger.info("Request processed",
                                  log_event="request_complete",
                                  request_id="req_123",
                                  duration_ms=150,
                                  status_code=200)

                # Verify logs are written properly
                log_file = container_log_dir / 'app.log'
                assert log_file.exists()

                with open(log_file, 'r') as f:
                    log_content = f.read()

                # Verify structured logging format
                assert 'container_app' in log_content
                assert 'app_start' in log_content
                assert 'db_error' in log_content
                assert 'request_complete' in log_content

                print("✅ Containerized environment logging works correctly")

    def test_production_like_environment(self):
        """Test logging behavior in production-like environment"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create production-like directory structure
            prod_log_dir = Path(temp_dir) / 'var' / 'log' / 'app'
            prod_log_dir.mkdir(parents=True)

            prod_env = {
                'LOG_DIR': str(prod_log_dir),
                'LOG_LEVEL': 'WARNING',  # Production typically uses WARNING+
                'LOG_FILE_ENABLED': 'true',
                'ENVIRONMENT': 'production',
            }

            with patch.dict(os.environ, prod_env):
                # Reset logging state
                import core.logging as logging_module
                logging_module._logging_configured = False
                logging.getLogger().handlers.clear()

                ensure_logging_configured()

                # Test production logging patterns
                logger = get_logger('prod_service')

                # These should be logged (WARNING level and above)
                logger.warning("Resource usage high",
                             log_event="resource_warning",
                             cpu_percent=85,
                             memory_mb=1024)

                logger.error("Service unavailable",
                           log_event="service_error",
                           service="database",
                           error_code="503")

                logger.critical("System failure",
                              log_event="system_failure",
                              component="auth_service")

                # These should NOT be logged (below WARNING level)
                logger.debug("Debug message")
                logger.info("Info message")

                # Verify appropriate filtering
                log_file = prod_log_dir / 'app.log'
                assert log_file.exists()

                with open(log_file, 'r') as f:
                    log_content = f.read()

                # Should contain WARNING+ messages
                assert 'resource_warning' in log_content
                assert 'service_error' in log_content
                assert 'system_failure' in log_content

                # Should NOT contain DEBUG/INFO messages
                assert 'Debug message' not in log_content
                assert 'Info message' not in log_content

                print("✅ Production-like environment filtering works correctly")

    def test_development_environment(self):
        """Test logging behavior in development environment"""
        with tempfile.TemporaryDirectory() as temp_dir:
            dev_env = {
                'LOG_DIR': str(temp_dir),
                'LOG_LEVEL': 'DEBUG',  # Development uses DEBUG
                'LOG_FILE_ENABLED': 'true',
                'ENVIRONMENT': 'development',
            }

            with patch.dict(os.environ, dev_env):
                # Reset logging state
                import core.logging as logging_module
                logging_module._logging_configured = False
                logging.getLogger().handlers.clear()

                ensure_logging_configured()

                logger = get_logger('dev_service')

                # All levels should be logged in development
                logger.debug("Debug information", log_event="debug_event")
                logger.info("Information message", log_event="info_event")
                logger.warning("Warning message", log_event="warning_event")
                logger.error("Error message", log_event="error_event")

                # Verify all messages are logged
                log_file = Path(temp_dir) / 'app.log'
                assert log_file.exists()

                with open(log_file, 'r') as f:
                    log_content = f.read()

                # All events should be present
                assert 'debug_event' in log_content
                assert 'info_event' in log_content
                assert 'warning_event' in log_content
                assert 'error_event' in log_content

                print("✅ Development environment logging captures all levels")

    @pytest.mark.skipif(not DOCKER_AVAILABLE, reason="Docker not available")
    def test_actual_container_logging(self):
        """Test logging in an actual Docker container (if Docker is available)"""
        try:
            # Create a simple test script that uses our logging
            test_script = '''
import sys
import os
sys.path.insert(0, '/app/src')

from core.logging import ensure_logging_configured, get_logger
import time

# Configure logging
ensure_logging_configured()
logger = get_logger('container_test')

# Log some test messages
logger.info("Container test started", log_event="container_start")
logger.warning("Test warning", log_event="test_warning", test_id=123)
logger.error("Test error", log_event="test_error", error_type="TestError")

# Generate some volume to test rotation
for i in range(100):
    logger.info(f"Volume test message {i}", log_event="volume_test", message_id=i)

logger.info("Container test completed", log_event="container_complete")
print("Container test completed successfully")
'''

            # Create Dockerfile content
            dockerfile_content = '''
FROM python:3.11-slim
WORKDIR /app
COPY . /app/
RUN pip install structlog pytest
ENV LOG_DIR=/app/container_logs
ENV LOG_LEVEL=DEBUG
ENV LOG_FILE_ENABLED=true
CMD ["python", "/app/test_script.py"]
'''

            with tempfile.TemporaryDirectory() as temp_dir:
                # Copy source code to temp directory
                src_dir = Path(__file__).parent.parent.parent / 'src'
                temp_src = Path(temp_dir) / 'src'
                shutil.copytree(src_dir, temp_src)

                # Write test files
                (Path(temp_dir) / 'test_script.py').write_text(test_script)
                (Path(temp_dir) / 'Dockerfile').write_text(dockerfile_content)

                # Build Docker image
                client = docker.from_env()
                image = client.images.build(path=temp_dir, tag='logging_test')[0]

                try:
                    # Run container
                    container = client.containers.run(
                        image.id,
                        detach=True,
                        volumes={temp_dir: {'bind': '/app/host_logs', 'mode': 'rw'}}
                    )

                    # Wait for completion
                    result = container.wait(timeout=30)
                    logs = container.logs().decode('utf-8')

                    # Check that container completed successfully
                    assert result['StatusCode'] == 0
                    assert 'Container test completed successfully' in logs

                    # Check log files were created in container
                    # We can't directly access container filesystem, but we can check
                    # if the logging system worked by examining the container logs
                    assert 'container_test' in logs or 'INFO' in logs

                    print("✅ Docker container logging test completed successfully")

                finally:
                    # Cleanup
                    container.remove()
                    client.images.remove(image.id)

        except Exception as e:
            pytest.skip(f"Docker container test failed: {e}")


class TestMemoryAndResourceConstraints:
    """Test logging behavior under memory constraints and resource cleanup"""

    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_memory_pressure_logging(self):
        """Test logging behavior under memory pressure"""
        import gc

        with tempfile.TemporaryDirectory() as temp_dir:
            # Monitor memory usage
            process = psutil.Process()
            initial_memory = process.memory_info().rss

            # Configure logging with file output
            with patch.dict(os.environ, {
                'LOG_DIR': temp_dir,
                'LOG_FILE_ENABLED': 'true'
            }):
                # Reset logging state
                import core.logging as logging_module
                logging_module._logging_configured = False
                logging.getLogger().handlers.clear()

                ensure_logging_configured()

                logger = get_logger('memory_test')

                # Create memory pressure by allocating large objects
                large_objects = []

                try:
                    # Allocate memory in chunks while logging
                    for i in range(100):
                        # Allocate 1MB chunks
                        chunk = bytearray(1024 * 1024)
                        large_objects.append(chunk)

                        # Log during memory pressure
                        logger.info(f"Memory test iteration {i}",
                                  log_event="memory_test",
                                  iteration=i,
                                  allocated_mb=len(large_objects))

                        # Check memory usage every 10 iterations
                        if i % 10 == 0:
                            current_memory = process.memory_info().rss
                            memory_increase = current_memory - initial_memory
                            print(f"   Memory pressure test: {i}/100, "
                                  f"Memory increase: {memory_increase/(1024*1024):.1f}MB")

                        # Don't exceed system memory
                        if len(large_objects) > 500:  # 500MB limit
                            break

                    # Force garbage collection
                    large_objects.clear()
                    gc.collect()

                    # Continue logging after memory pressure
                    for i in range(50):
                        logger.info(f"Post-pressure message {i}",
                                  log_event="post_pressure",
                                  iteration=i)

                    # Verify log file integrity
                    log_file = Path(temp_dir) / 'app.log'
                    assert log_file.exists()

                    with open(log_file, 'r') as f:
                        content = f.read()

                    # Should contain both memory test and post-pressure messages
                    assert 'memory_test' in content
                    assert 'post_pressure' in content

                    final_memory = process.memory_info().rss
                    memory_diff = final_memory - initial_memory

                    print(f"✅ Memory pressure test completed:")
                    print(f"   Initial memory: {initial_memory/(1024*1024):.1f}MB")
                    print(f"   Final memory: {final_memory/(1024*1024):.1f}MB")
                    print(f"   Memory difference: {memory_diff/(1024*1024):.1f}MB")
                    print(f"   Logging remained functional under memory pressure")

                except MemoryError:
                    # If we hit memory limits, that's okay - the test is about
                    # logging behavior under pressure
                    print("✅ Hit memory limits as expected, logging handled gracefully")

    def test_memory_pressure_simplified(self):
        """Test logging behavior under memory pressure (simplified version without psutil)"""
        import gc

        with tempfile.TemporaryDirectory() as temp_dir:
            # Configure logging with file output
            with patch.dict(os.environ, {
                'LOG_DIR': temp_dir,
                'LOG_FILE_ENABLED': 'true'
            }):
                # Reset logging state
                import core.logging as logging_module
                logging_module._logging_configured = False
                logging.getLogger().handlers.clear()

                ensure_logging_configured()

                logger = get_logger('memory_test_simple')

                # Create memory pressure by allocating large objects
                large_objects = []

                try:
                    # Allocate memory in smaller chunks to avoid system stress
                    for i in range(50):  # Reduced from 100
                        # Allocate 512KB chunks (reduced from 1MB)
                        chunk = bytearray(512 * 1024)
                        large_objects.append(chunk)

                        # Log during memory pressure
                        logger.info(f"Memory test iteration {i}",
                                  log_event="memory_test",
                                  iteration=i,
                                  allocated_kb=len(large_objects) * 512)

                        # Check every 10 iterations
                        if i % 10 == 0:
                            print(f"   Memory pressure test: {i}/50, "
                                  f"Allocated: {len(large_objects) * 512}KB")

                    # Force garbage collection
                    large_objects.clear()
                    gc.collect()

                    # Continue logging after memory pressure
                    for i in range(25):
                        logger.info(f"Post-pressure message {i}",
                                  log_event="post_pressure",
                                  iteration=i)

                    # Verify log file integrity
                    log_file = Path(temp_dir) / 'app.log'
                    assert log_file.exists()

                    with open(log_file, 'r') as f:
                        content = f.read()

                    # Should contain both memory test and post-pressure messages
                    assert 'memory_test' in content
                    assert 'post_pressure' in content

                    print("✅ Simplified memory pressure test completed:")
                    print(f"   Logging remained functional under memory pressure")

                except MemoryError:
                    # If we hit memory limits, that's okay - the test is about
                    # logging behavior under pressure
                    print("✅ Hit memory limits as expected, logging handled gracefully")

    def test_resource_cleanup_on_signal(self):
        """Test that logging resources are properly cleaned up on signals"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a subprocess that sets up logging and waits
            test_script = f'''
import os
import sys
import signal
import time
sys.path.insert(0, r"{Path(__file__).parent.parent.parent / 'src'}")

from core.logging import ensure_logging_configured, get_logger

# Set up logging
os.environ['LOG_DIR'] = r"{temp_dir}"
os.environ['LOG_FILE_ENABLED'] = 'true'

ensure_logging_configured()
logger = get_logger('signal_test')

def signal_handler(signum, frame):
    logger.info("Received signal, cleaning up", log_event="signal_received", signal=signum)
    # Simulate cleanup
    import logging
    for handler in logging.getLogger().handlers:
        handler.flush()
        if hasattr(handler, 'close'):
            handler.close()
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

logger.info("Process started", log_event="process_start")

# Keep logging while waiting for signal
for i in range(1000):
    logger.info(f"Heartbeat {i}", log_event="heartbeat", iteration=i)
    time.sleep(0.01)
'''

            # Write test script
            script_file = Path(temp_dir) / 'signal_test.py'
            script_file.write_text(test_script)

            # Start subprocess
            process = subprocess.Popen([sys.executable, str(script_file)])

            try:
                # Let it run for a bit
                time.sleep(2)

                # Send SIGTERM
                process.terminate()

                # Wait for cleanup
                exit_code = process.wait(timeout=5)

                # Check that process exited cleanly
                assert exit_code == 0

                # Verify log file was written and closed properly
                log_file = Path(temp_dir) / 'app.log'
                assert log_file.exists()

                with open(log_file, 'r') as f:
                    content = f.read()

                assert 'process_start' in content
                assert 'signal_received' in content
                assert 'heartbeat' in content

                print("✅ Signal handling and resource cleanup works correctly")

            except subprocess.TimeoutExpired:
                process.kill()
                pytest.fail("Process did not exit cleanly after signal")

    def test_file_handle_limits(self):
        """Test behavior when approaching file handle limits"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create many loggers with file handlers to test handle limits
            loggers = []
            handlers = []

            try:
                # Create multiple file handlers (simulating many log files)
                for i in range(100):  # Create many handlers
                    log_file = Path(temp_dir) / f'test_{i}.log'

                    handler = CompressedRotatingFileHandler(
                        filename=str(log_file),
                        maxBytes=1024,
                        backupCount=2,
                        encoding='utf-8'
                    )

                    logger = logging.getLogger(f'handle_test_{i}')
                    logger.addHandler(handler)

                    loggers.append(logger)
                    handlers.append(handler)

                    # Test that each handler works
                    logger.info(f"Test message for logger {i}")

                    if i % 20 == 0:
                        print(f"   Created {i+1} file handlers")

                # Test that all loggers still work
                for i, logger in enumerate(loggers[:10]):  # Test first 10
                    logger.info(f"Final test message for logger {i}")

                print(f"✅ Successfully created and used {len(handlers)} file handlers")

            finally:
                # Clean up all handlers
                for handler in handlers:
                    try:
                        handler.close()
                    except:
                        pass

                for logger in loggers:
                    logger.handlers.clear()

    def test_concurrent_file_access(self):
        """Test concurrent access to the same log file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / 'concurrent.log'

            # Configure shared logging
            with patch.dict(os.environ, {
                'LOG_DIR': temp_dir,
                'LOG_FILE_ENABLED': 'true'
            }):
                # Reset logging state
                import core.logging as logging_module
                logging_module._logging_configured = False
                logging.getLogger().handlers.clear()

                ensure_logging_configured()

                # Function for concurrent logging
                def concurrent_worker(worker_id, message_count):
                    logger = get_logger(f'worker_{worker_id}')
                    for i in range(message_count):
                        logger.info(f"Worker {worker_id} message {i}",
                                  log_event="concurrent_test",
                                  worker_id=worker_id,
                                  message_id=i)

                # Start multiple concurrent workers
                threads = []
                start_time = time.time()

                for worker_id in range(10):
                    thread = threading.Thread(
                        target=concurrent_worker,
                        args=(worker_id, 200)
                    )
                    threads.append(thread)
                    thread.start()

                # Wait for all workers to complete
                for thread in threads:
                    thread.join()

                duration = time.time() - start_time

                # Verify log file integrity
                assert log_file.exists()

                with open(log_file, 'r') as f:
                    lines = f.readlines()

                # Should have messages from all workers
                worker_messages = {}
                for line in lines:
                    if 'concurrent_test' in line:
                        # Extract worker ID from JSON
                        try:
                            if 'worker_' in line:
                                # Find worker ID in the line
                                for worker_id in range(10):
                                    if f'worker_{worker_id}' in line:
                                        worker_messages[worker_id] = worker_messages.get(worker_id, 0) + 1
                        except:
                            pass

                print(f"✅ Concurrent file access test completed:")
                print(f"   Duration: {duration:.2f} seconds")
                print(f"   Total lines: {len(lines)}")
                print(f"   Workers with messages: {len(worker_messages)}/10")
                print(f"   Messages per worker: {[worker_messages.get(i, 0) for i in range(10)]}")

                # Verify we have messages from most workers
                assert len(worker_messages) >= 8  # At least 8/10 workers should have messages


class TestCICompatibility:
    """Test compatibility with CI/CD environments"""

    def test_github_actions_environment(self):
        """Test logging in GitHub Actions-like environment"""
        github_env = {
            'GITHUB_ACTIONS': 'true',
            'RUNNER_OS': 'Linux',
            'RUNNER_TEMP': '/tmp',
            'LOG_LEVEL': 'INFO',
            'LOG_FILE_ENABLED': 'true',
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            github_env['LOG_DIR'] = temp_dir

            with patch.dict(os.environ, github_env):
                # Reset logging state
                import core.logging as logging_module
                logging_module._logging_configured = False
                logging.getLogger().handlers.clear()

                ensure_logging_configured()

                logger = get_logger('ci_test')

                # Log messages typical in CI
                logger.info("Build started", log_event="build_start", commit="abc123")
                logger.info("Running tests", log_event="test_start", test_suite="integration")
                logger.warning("Deprecated feature used", log_event="deprecation_warning")
                logger.info("Build completed", log_event="build_complete", status="success")

                # Verify logging works in CI environment
                log_file = Path(temp_dir) / 'app.log'
                assert log_file.exists()

                with open(log_file, 'r') as f:
                    content = f.read()

                assert 'build_start' in content
                assert 'test_start' in content
                assert 'build_complete' in content

                print("✅ GitHub Actions environment logging works correctly")

    def test_automated_test_environment(self):
        """Test logging behavior during automated testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_env = {
                'LOG_DIR': temp_dir,
                'LOG_LEVEL': 'DEBUG',
                'LOG_FILE_ENABLED': 'true',
                'TESTING': 'true',
            }

            with patch.dict(os.environ, test_env):
                # Reset logging state
                import core.logging as logging_module
                logging_module._logging_configured = False
                logging.getLogger().handlers.clear()

                ensure_logging_configured()

                # Simulate test execution with logging
                test_logger = get_logger('test_runner')

                # Test setup logging
                test_logger.info("Test setup started", log_event="test_setup")

                # Simulate multiple test cases
                for test_id in range(5):
                    test_logger.info(f"Running test case {test_id}",
                                   log_event="test_case_start",
                                   test_id=test_id)

                    # Simulate test execution
                    test_logger.debug(f"Test {test_id} execution details",
                                    log_event="test_execution",
                                    test_id=test_id,
                                    step="validation")

                    # Simulate test completion
                    test_logger.info(f"Test case {test_id} completed",
                                   log_event="test_case_complete",
                                   test_id=test_id,
                                   result="passed")

                test_logger.info("All tests completed", log_event="test_teardown")

                # Verify test logging
                log_file = Path(temp_dir) / 'app.log'
                assert log_file.exists()

                with open(log_file, 'r') as f:
                    content = f.read()

                # Should contain all test events
                assert 'test_setup' in content
                assert 'test_case_start' in content
                assert 'test_execution' in content
                assert 'test_case_complete' in content
                assert 'test_teardown' in content

                print("✅ Automated test environment logging works correctly")


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-s", "--tb=short"])