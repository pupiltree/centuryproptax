#!/usr/bin/env python3
"""
Test runner script for the AI Chatbot Automation Engine.
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path

def run_command(command, cwd=None):
    """Run a command and return the result"""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def run_tests(test_path=None, verbose=False, coverage=False, specific_test=None):
    """Run the test suite"""
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"
    
    # Build pytest command
    cmd_parts = ["pytest"]
    
    if verbose:
        cmd_parts.append("-v")
    
    if coverage:
        cmd_parts.extend([
            "--cov=engine",
            "--cov-report=html",
            "--cov-report=term-missing"
        ])
    
    # Add specific test path or pattern
    if specific_test:
        cmd_parts.append(str(tests_dir / specific_test))
    elif test_path:
        cmd_parts.append(str(tests_dir / test_path))
    else:
        cmd_parts.append(str(tests_dir))
    
    # Add additional pytest options
    cmd_parts.extend([
        "--tb=short",
        "--strict-markers",
        "--disable-warnings"
    ])
    
    command = " ".join(cmd_parts)
    print(f"Running: {command}")
    print("-" * 50)
    
    success, stdout, stderr = run_command(command, cwd=project_root)
    
    if stdout:
        print(stdout)
    if stderr:
        print(stderr, file=sys.stderr)
    
    return success

def check_dependencies():
    """Check if required test dependencies are installed"""
    required_packages = [
        "pytest",
        "pytest-asyncio", 
        "pytest-cov",
        "pytest-mock",
        "httpx",
        "fastapi[all]"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("Missing required test dependencies:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nInstall them with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Run tests for the AI Chatbot Automation Engine")
    parser.add_argument(
        "--test",
        help="Run specific test file (e.g., test_config_generator.py)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Run tests in verbose mode"
    )
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Run tests with coverage reporting"
    )
    parser.add_argument(
        "--specific", "-s",
        help="Run specific test function (e.g., test_config_generator.py::TestConfigurationGenerator::test_initialization)"
    )
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check if test dependencies are installed"
    )
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run only unit tests"
    )
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run only integration tests"
    )
    
    args = parser.parse_args()
    
    # Check dependencies if requested
    if args.check_deps:
        if check_dependencies():
            print("All test dependencies are installed ✓")
            return 0
        else:
            return 1
    
    # Check dependencies before running tests
    if not check_dependencies():
        print("Please install missing dependencies before running tests.")
        return 1
    
    # Determine test selection
    test_path = None
    if args.unit:
        test_path = "test_*.py"
    elif args.integration:
        test_path = "integration/"
    elif args.test:
        test_path = args.test
    
    # Run tests
    success = run_tests(
        test_path=test_path,
        verbose=args.verbose,
        coverage=args.coverage,
        specific_test=args.specific
    )
    
    if success:
        print("\n" + "=" * 50)
        print("✓ All tests passed successfully!")
        if args.coverage:
            print("Coverage report generated in htmlcov/")
        return 0
    else:
        print("\n" + "=" * 50)
        print("✗ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())