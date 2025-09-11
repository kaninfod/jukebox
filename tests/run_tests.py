#!/usr/bin/env python3
"""
Comprehensive test runner for the jukebox project.

This script can run tests in multiple ways:
1. Simple Python tests (no external dependencies)
2. Pytest with proper configuration
3. Selective test running (skip hardware tests on non-Pi systems)
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_pytest_available():
    """Check if pytest is available"""
    try:
        import pytest
        return True
    except ImportError:
        return False

def check_hardware_available():
    """Check if hardware (GPIO) is available"""
    try:
        import RPi.GPIO as GPIO
        return True
    except (ImportError, RuntimeError):
        return False

def run_simple_tests():
    """Run simple Python tests that don't require pytest"""
    print("🎯 Running Simple Tests (No external dependencies)")
    print("=" * 60)
    
    simple_tests = [
        "tests/test_chromecast_devices_simple.py"
    ]
    
    results = []
    for test_file in simple_tests:
        if os.path.exists(test_file):
            print(f"\n📁 Running {test_file}...")
            try:
                result = subprocess.run([sys.executable, test_file], 
                                      capture_output=True, text=True, cwd=project_root)
                if result.returncode == 0:
                    print("✅ PASSED")
                    results.append(True)
                else:
                    print("❌ FAILED")
                    print(result.stdout)
                    print(result.stderr)
                    results.append(False)
            except Exception as e:
                print(f"❌ ERROR: {e}")
                results.append(False)
        else:
            print(f"⚠️  Test file not found: {test_file}")
    
    return results

def run_pytest_unit_tests():
    """Run pytest with unit tests only (no hardware)"""
    print("🎯 Running Pytest Unit Tests (Software only)")
    print("=" * 60)
    
    # Skip hardware-dependent tests
    skip_patterns = [
        "test_system_integration.py",
        "test_user_workflows.py"  # These have GPIO dependencies
    ]
    
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/",
        "-v",
        "--tb=short"
    ]
    
    # Add skip patterns
    for pattern in skip_patterns:
        cmd.extend(["--ignore", f"tests/{pattern}"])
    
    try:
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running pytest: {e}")
        return False

def run_pytest_all_tests():
    """Run all pytest tests including hardware (if available)"""
    print("🎯 Running All Pytest Tests (Including hardware if available)")
    print("=" * 60)
    
    cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"]
    
    try:
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running pytest: {e}")
        return False

def run_specific_test_file(test_file):
    """Run a specific test file"""
    print(f"🎯 Running Specific Test: {test_file}")
    print("=" * 60)
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
    
    # Try pytest first, fall back to simple Python
    if check_pytest_available():
        cmd = [sys.executable, "-m", "pytest", test_file, "-v"]
        try:
            result = subprocess.run(cmd, cwd=project_root)
            return result.returncode == 0
        except Exception as e:
            print(f"⚠️  Pytest failed: {e}, trying simple Python...")
    
    # Fall back to simple Python execution
    try:
        result = subprocess.run([sys.executable, test_file], cwd=project_root)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

def show_test_info():
    """Show information about available tests"""
    print("📋 Available Test Information")
    print("=" * 50)
    
    tests_dir = Path("tests")
    if tests_dir.exists():
        test_files = list(tests_dir.glob("test_*.py"))
        print(f"📁 Found {len(test_files)} test files:")
        
        for test_file in sorted(test_files):
            print(f"   • {test_file.name}")
    
    print(f"\n🔧 System Information:")
    print(f"   • Python: {sys.version.split()[0]}")
    print(f"   • Pytest available: {'✅' if check_pytest_available() else '❌'}")
    print(f"   • Hardware (GPIO) available: {'✅' if check_hardware_available() else '❌'}")

def main():
    parser = argparse.ArgumentParser(description="Jukebox Test Runner")
    parser.add_argument("--mode", choices=["simple", "unit", "all", "info"], 
                       default="unit", help="Test mode to run")
    parser.add_argument("--file", help="Run specific test file")
    parser.add_argument("--list", action="store_true", help="List available tests")
    
    args = parser.parse_args()
    
    if args.list or args.mode == "info":
        show_test_info()
        return
    
    if args.file:
        success = run_specific_test_file(args.file)
        sys.exit(0 if success else 1)
    
    print("🧪 Jukebox Test Runner")
    print("=" * 50)
    
    if args.mode == "simple":
        results = run_simple_tests()
        success = all(results)
        print(f"\n📊 Simple Tests: {sum(results)}/{len(results)} passed")
        
    elif args.mode == "unit":
        if not check_pytest_available():
            print("⚠️  Pytest not available, falling back to simple tests")
            results = run_simple_tests()
            success = all(results)
        else:
            success = run_pytest_unit_tests()
        
    elif args.mode == "all":
        if not check_pytest_available():
            print("❌ Pytest required for 'all' mode")
            sys.exit(1)
        success = run_pytest_all_tests()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
    else:
        print("❌ Some tests failed")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
