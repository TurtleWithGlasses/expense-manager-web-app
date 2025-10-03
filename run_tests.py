#!/usr/bin/env python3
"""
Test runner script for AI features
"""
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit code {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False


def run_ai_tests():
    """Run AI-specific tests"""
    print("🧪 Running AI Test Suite...")
    
    # Unit tests for AI services
    success1 = run_command(
        "python -m pytest tests/test_ai_services.py -v --tb=short",
        "AI Services Unit Tests"
    )
    
    # Integration tests for AI API
    success2 = run_command(
        "python -m pytest tests/test_ai_api.py -v --tb=short",
        "AI API Integration Tests"
    )
    
    return success1 and success2


def run_performance_tests():
    """Run performance tests"""
    print("⚡ Running Performance Tests...")
    
    success = run_command(
        "python tests/test_ai_performance.py",
        "AI Performance Tests"
    )
    
    return success


def run_all_tests():
    """Run all tests"""
    print("🔬 Running Complete Test Suite...")
    
    # All tests with coverage
    success = run_command(
        "python -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing",
        "Complete Test Suite with Coverage"
    )
    
    return success


def run_specific_tests(test_pattern):
    """Run specific tests matching pattern"""
    print(f"🎯 Running Tests Matching: {test_pattern}")
    
    success = run_command(
        f"python -m pytest tests/ -k '{test_pattern}' -v --tb=short",
        f"Tests matching '{test_pattern}'"
    )
    
    return success


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="AI Test Runner")
    parser.add_argument(
        "test_type",
        choices=["ai", "performance", "all", "specific"],
        help="Type of tests to run"
    )
    parser.add_argument(
        "--pattern",
        help="Pattern for specific tests (used with 'specific' type)"
    )
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install test dependencies first"
    )
    
    args = parser.parse_args()
    
    # Install dependencies if requested
    if args.install_deps:
        print("📦 Installing test dependencies...")
        success = run_command(
            "pip install -r requirements.txt",
            "Installing Dependencies"
        )
        if not success:
            print("❌ Failed to install dependencies")
            sys.exit(1)
    
    # Run tests based on type
    if args.test_type == "ai":
        success = run_ai_tests()
    elif args.test_type == "performance":
        success = run_performance_tests()
    elif args.test_type == "all":
        success = run_all_tests()
    elif args.test_type == "specific":
        if not args.pattern:
            print("❌ Pattern required for specific tests")
            sys.exit(1)
        success = run_specific_tests(args.pattern)
    
    # Report results
    print(f"\n{'='*60}")
    if success:
        print("✅ All tests passed successfully!")
        print("🎉 Phase 1 testing is complete!")
    else:
        print("❌ Some tests failed!")
        print("🔧 Please check the output above for details.")
    print(f"{'='*60}")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
