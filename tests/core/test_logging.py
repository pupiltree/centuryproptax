"""
Unit Tests for Core Logging Module

Comprehensive tests for centralized logging configuration, log rotation,
and compression functionality.
"""

import pytest
import os
import sys
import tempfile
import gzip
import logging
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

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


class TestLogDirectoryConfiguration:
    """Test log directory configuration functionality"""

    def test_get_log_directory_with_env_var(self):
        """Test log directory configuration with valid environment variable"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {'LOG_DIR': temp_dir}):
                result = get_log_directory()
                assert result == str(Path(temp_dir).absolute())
                print(f"✅ Log directory from env var: {result}")

    def test_get_log_directory_with_invalid_env_var(self):
        """Test log directory fallback with invalid environment variable"""
        with patch.dict(os.environ, {'LOG_DIR': '/invalid/nonexistent/path'}):
            result = get_log_directory()
            # Should fall back to default logs directory or temp
            assert result is not None
            assert Path(result).exists()
            print(f"✅ Log directory fallback: {result}")

    def test_get_log_directory_permission_error(self):
        """Test log directory fallback with permission error"""
        with patch.dict(os.environ, {'LOG_DIR': '/root/forbidden'}):
            result = get_log_directory()
            # Should fall back to accessible directory
            assert result is not None
            # Test that we can actually write to the directory
            test_file = Path(result) / 'test_write'
            test_file.touch()
            test_file.unlink()
            print(f"✅ Log directory with permission fallback: {result}")

    def test_get_log_directory_default_fallback(self):
        """Test default log directory creation"""
        with patch.dict(os.environ, {}, clear=True):
            # Remove LOG_DIR if it exists
            result = get_log_directory()
            assert result is not None
            assert Path(result).exists()
            print(f"✅ Default log directory: {result}")


class TestLogLevelConfiguration:
    """Test log level configuration functionality"""

    def test_get_log_level_valid_levels(self):
        """Test log level configuration with valid levels"""
        test_cases = [
            ('DEBUG', logging.DEBUG),
            ('INFO', logging.INFO),
            ('WARNING', logging.WARNING),
            ('WARN', logging.WARNING),  # Alternative form
            ('ERROR', logging.ERROR),
            ('CRITICAL', logging.CRITICAL),
            ('debug', logging.DEBUG),  # Test case insensitivity
            ('info', logging.INFO),
        ]

        for level_str, expected_level in test_cases:
            with patch.dict(os.environ, {'LOG_LEVEL': level_str}):
                result = get_log_level()
                assert result == expected_level
                print(f"✅ Log level {level_str} -> {logging.getLevelName(result)}")

    def test_get_log_level_invalid_level(self):
        """Test log level fallback with invalid level"""
        with patch.dict(os.environ, {'LOG_LEVEL': 'INVALID_LEVEL'}):
            result = get_log_level()
            assert result == logging.INFO  # Default fallback
            print(f"✅ Invalid log level fallback: {logging.getLevelName(result)}")

    def test_get_log_level_no_env_var(self):
        """Test log level default when no environment variable"""
        with patch.dict(os.environ, {}, clear=True):
            result = get_log_level()
            assert result == logging.INFO  # Default
            print(f"✅ Default log level: {logging.getLevelName(result)}")


class TestFileLoggingConfiguration:
    """Test file logging enablement configuration"""

    def test_is_file_logging_enabled_true_values(self):
        """Test file logging enabled with various true values"""
        true_values = ['true', '1', 'yes', 'on', 'enabled', 'TRUE', 'True']

        for value in true_values:
            with patch.dict(os.environ, {'LOG_FILE_ENABLED': value}):
                result = is_file_logging_enabled()
                assert result is True
                print(f"✅ File logging enabled for: {value}")

    def test_is_file_logging_enabled_false_values(self):
        """Test file logging disabled with various false values"""
        false_values = ['false', '0', 'no', 'off', 'disabled', 'FALSE', 'False']

        for value in false_values:
            with patch.dict(os.environ, {'LOG_FILE_ENABLED': value}):
                result = is_file_logging_enabled()
                assert result is False
                print(f"✅ File logging disabled for: {value}")

    def test_is_file_logging_enabled_default(self):
        """Test file logging default when no environment variable"""
        with patch.dict(os.environ, {}, clear=True):
            result = is_file_logging_enabled()
            assert result is True  # Default is enabled
            print(f"✅ File logging default: {result}")


class TestCompressedRotatingFileHandler:
    """Test custom compressed rotating file handler"""

    def test_compressed_rotating_handler_creation(self):
        """Test creation of compressed rotating file handler"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / 'test.log'

            handler = CompressedRotatingFileHandler(
                filename=str(log_file),
                maxBytes=1024,  # Small size for testing
                backupCount=3,
                encoding='utf-8'
            )

            assert handler.maxBytes == 1024
            assert handler.backupCount == 3
            assert handler.encoding == 'utf-8'
            assert str(log_file) in handler.baseFilename

            handler.close()
            print("✅ Compressed rotating handler created successfully")

    def test_compressed_rotating_handler_logging(self):
        """Test logging with compressed rotating file handler"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / 'test.log'

            # Create handler with very small max size to force rotation
            handler = CompressedRotatingFileHandler(
                filename=str(log_file),
                maxBytes=500,  # Very small to trigger rotation quickly
                backupCount=2,
                encoding='utf-8'
            )

            # Create a logger and add our handler
            logger = logging.getLogger('test_rotation')
            logger.setLevel(logging.DEBUG)
            logger.addHandler(handler)

            # Write enough data to trigger rotation
            long_message = "This is a test message that should trigger rotation " * 20

            # Write multiple messages to exceed maxBytes
            for i in range(10):
                logger.info(f"Message {i}: {long_message}")

            # Check that main log file exists
            assert log_file.exists()
            print(f"✅ Main log file exists: {log_file}")

            # Check for compressed backup files
            backup_files = list(Path(temp_dir).glob('test.log.*.gz'))
            print(f"✅ Found {len(backup_files)} compressed backup files")

            # Verify compressed files can be read
            for backup_file in backup_files:
                with gzip.open(backup_file, 'rt', encoding='utf-8') as f:
                    content = f.read()
                    assert 'This is a test message' in content
                    print(f"✅ Compressed file readable: {backup_file.name}")

            handler.close()
            logger.removeHandler(handler)

    def test_compressed_rotating_handler_backup_count_limit(self):
        """Test that backup count limit is respected"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / 'test.log'
            backup_count = 2

            handler = CompressedRotatingFileHandler(
                filename=str(log_file),
                maxBytes=200,  # Very small to force multiple rotations
                backupCount=backup_count,
                encoding='utf-8'
            )

            logger = logging.getLogger('test_backup_limit')
            logger.setLevel(logging.DEBUG)
            logger.addHandler(handler)

            # Generate enough logs to exceed backup count
            long_message = "Test message for backup count verification " * 10
            for i in range(50):  # Generate many messages
                logger.info(f"Message {i}: {long_message}")

            # Count compressed backup files
            backup_files = list(Path(temp_dir).glob('test.log.*.gz'))

            # Should not exceed backup count
            assert len(backup_files) <= backup_count
            print(f"✅ Backup count respected: {len(backup_files)} <= {backup_count}")

            handler.close()
            logger.removeHandler(handler)


class TestLoggingConfiguration:
    """Test complete logging configuration"""

    def test_configure_logging_console_only(self):
        """Test logging configuration with console only"""
        with patch.dict(os.environ, {'LOG_FILE_ENABLED': 'false'}):
            # Reset logging configuration
            logging.getLogger().handlers.clear()

            configure_logging()

            # Check that root logger has handlers
            root_logger = logging.getLogger()
            assert len(root_logger.handlers) > 0

            # Should have console handler but no file handler
            console_handlers = [h for h in root_logger.handlers
                             if isinstance(h, logging.StreamHandler)
                             and not isinstance(h, CompressedRotatingFileHandler)]
            file_handlers = [h for h in root_logger.handlers
                           if isinstance(h, CompressedRotatingFileHandler)]

            assert len(console_handlers) > 0
            assert len(file_handlers) == 0

            print("✅ Console-only logging configured successfully")

    def test_configure_logging_with_file(self):
        """Test logging configuration with file handler"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {
                'LOG_DIR': temp_dir,
                'LOG_FILE_ENABLED': 'true',
                'LOG_LEVEL': 'DEBUG'
            }):
                # Reset logging configuration
                logging.getLogger().handlers.clear()

                configure_logging()

                # Check that root logger has handlers
                root_logger = logging.getLogger()
                assert len(root_logger.handlers) > 0

                # Should have both console and file handlers
                console_handlers = [h for h in root_logger.handlers
                                 if isinstance(h, logging.StreamHandler)
                                 and not isinstance(h, CompressedRotatingFileHandler)]
                file_handlers = [h for h in root_logger.handlers
                               if isinstance(h, CompressedRotatingFileHandler)]

                assert len(console_handlers) > 0
                assert len(file_handlers) > 0

                # Test that the file handler is properly configured
                file_handler = file_handlers[0]
                assert file_handler.maxBytes == 100 * 1024 * 1024  # 100MB
                assert file_handler.backupCount == 10
                assert file_handler.encoding == 'utf-8'

                # Test that log file is created
                log_file = Path(temp_dir) / 'app.log'

                # Write a test message
                test_logger = logging.getLogger('test')
                test_logger.info("Test message for file logging")

                # Check that log file exists and contains the message
                assert log_file.exists()
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    assert 'Test message for file logging' in content

                print(f"✅ File logging configured successfully: {log_file}")

    def test_ensure_logging_configured_idempotent(self):
        """Test that ensure_logging_configured can be called multiple times safely"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {'LOG_DIR': temp_dir}):
                # Reset global state
                import core.logging as logging_module
                logging_module._logging_configured = False
                logging.getLogger().handlers.clear()

                # Call multiple times
                ensure_logging_configured()
                handler_count_1 = len(logging.getLogger().handlers)

                ensure_logging_configured()
                handler_count_2 = len(logging.getLogger().handlers)

                ensure_logging_configured()
                handler_count_3 = len(logging.getLogger().handlers)

                # Handler count should remain the same
                assert handler_count_1 == handler_count_2 == handler_count_3
                print(f"✅ Logging configuration is idempotent: {handler_count_1} handlers")


class TestLoggerFactories:
    """Test logger factory functions"""

    def test_get_logger_with_component(self):
        """Test structlog logger creation with component binding"""
        ensure_logging_configured()

        logger = get_logger('test_component')

        # Test that logger has the component bound
        # This is a structlog bound logger
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'debug')

        print("✅ Structlog logger with component binding created")

    def test_get_standard_logger(self):
        """Test standard logger creation"""
        ensure_logging_configured()

        logger = get_standard_logger('test_module')

        # This should be a standard Python logger
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'test_module'

        print("✅ Standard Python logger created")

    def test_logger_integration(self):
        """Test that both logger types work correctly"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {
                'LOG_DIR': temp_dir,
                'LOG_FILE_ENABLED': 'true'
            }):
                # Reset global logging state
                import core.logging as logging_module
                logging_module._logging_configured = False
                logging.getLogger().handlers.clear()

                ensure_logging_configured()

                # Test structlog logger
                struct_logger = get_logger('whatsapp_client')
                struct_logger.info("Test message from structlog", recipient="+1234567890")

                # Test standard logger
                std_logger = get_standard_logger('test_module')
                std_logger.info("Test message from standard logger")

                # Force flush all handlers
                for handler in logging.getLogger().handlers:
                    handler.flush()

                # Check that messages appear in log file
                log_file = Path(temp_dir) / 'app.log'
                assert log_file.exists()

                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    assert 'Test message from standard logger' in content
                    # Structlog message will be JSON formatted and contain component
                    assert 'whatsapp_client' in content

                print("✅ Both logger types work correctly")


class TestHighVolumeLogging:
    """Test logging under high volume scenarios"""

    def test_high_volume_log_rotation(self):
        """Test log rotation under high volume logging"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / 'high_volume.log'

            # Create handler with small size to force frequent rotation
            handler = CompressedRotatingFileHandler(
                filename=str(log_file),
                maxBytes=10 * 1024,  # 10KB for quick rotation
                backupCount=5,
                encoding='utf-8'
            )

            logger = logging.getLogger('high_volume_test')
            logger.setLevel(logging.DEBUG)
            logger.addHandler(handler)

            # Generate high volume of logs
            large_message = "High volume test message with lots of content " * 50

            print("🔍 Generating high volume logs...")
            for i in range(1000):  # Generate many large messages
                logger.info(f"Message {i}: {large_message}")

                # Periodically check file count
                if i % 100 == 0:
                    backup_files = list(Path(temp_dir).glob('high_volume.log.*.gz'))
                    print(f"   Progress: {i}/1000, Backup files: {len(backup_files)}")

            # Final verification
            backup_files = list(Path(temp_dir).glob('high_volume.log.*.gz'))
            main_file_size = log_file.stat().st_size if log_file.exists() else 0

            print(f"✅ High volume test completed:")
            print(f"   Main log file size: {main_file_size:,} bytes")
            print(f"   Compressed backup files: {len(backup_files)}")
            print(f"   Backup count limit respected: {len(backup_files) <= 5}")

            # Verify backup count is respected
            assert len(backup_files) <= 5

            # Verify compressed files are readable
            readable_count = 0
            for backup_file in backup_files:
                try:
                    with gzip.open(backup_file, 'rt', encoding='utf-8') as f:
                        # Just read a small portion to verify it's readable
                        content = f.read(100)
                        if 'High volume test message' in content:
                            readable_count += 1
                except Exception:
                    pass

            print(f"   Readable compressed files: {readable_count}/{len(backup_files)}")
            assert readable_count == len(backup_files)

            handler.close()
            logger.removeHandler(handler)

    def test_concurrent_logging_performance(self):
        """Test logging performance with concurrent access"""
        import threading
        import time

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {
                'LOG_DIR': temp_dir,
                'LOG_FILE_ENABLED': 'true'
            }):
                # Reset global logging state
                import core.logging as logging_module
                logging_module._logging_configured = False
                logging.getLogger().handlers.clear()

                ensure_logging_configured()

                def worker_function(worker_id):
                    """Worker function for concurrent logging"""
                    logger = get_standard_logger(f'worker_{worker_id}')
                    for i in range(100):
                        logger.info(f"Worker {worker_id} message {i}")

                # Start multiple threads
                threads = []
                start_time = time.time()

                for worker_id in range(10):  # 10 concurrent workers
                    thread = threading.Thread(target=worker_function, args=(worker_id,))
                    threads.append(thread)
                    thread.start()

                # Wait for all threads to complete
                for thread in threads:
                    thread.join()

                end_time = time.time()
                duration = end_time - start_time

                # Force flush all handlers
                for handler in logging.getLogger().handlers:
                    handler.flush()

                # Verify log file contains messages from all workers
                log_file = Path(temp_dir) / 'app.log'
                assert log_file.exists()

                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check that we have messages from all workers
                for worker_id in range(10):
                    assert f'worker_{worker_id}' in content

                print(f"✅ Concurrent logging performance test completed:")
                print(f"   Duration: {duration:.2f} seconds")
                print(f"   Messages per second: {1000/duration:.1f}")
                print(f"   Log file size: {log_file.stat().st_size:,} bytes")


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v", "-s"])