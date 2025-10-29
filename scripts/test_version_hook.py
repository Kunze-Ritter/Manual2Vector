#!/usr/bin/env python3
"""
Test script for version hook functionality.
Tests hook logic without creating actual git commits.
"""

import importlib.util
import sys
from pathlib import Path
import tempfile
import shutil
import re
from datetime import datetime

# Add scripts directory to path to import hook functions
sys.path.insert(0, str(Path(__file__).parent / "git_hooks"))

HOOK_MODULE_PATH = Path(__file__).resolve().parent / "git_hooks" / "pre_commit.py"

spec = importlib.util.spec_from_file_location("krai_git_hook_pre_commit", HOOK_MODULE_PATH)
if spec is None or spec.loader is None:  # pragma: no cover - import failure path
    raise ImportError(f"Unable to load hook module from {HOOK_MODULE_PATH}")

_hook_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_hook_module)

parse_version = _hook_module.parse_version
increment_version = _hook_module.increment_version


class TestResults:
    """Track test results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def add_result(self, test_name, passed, message=""):
        """Add a test result."""
        self.tests.append((test_name, passed, message))
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        for test_name, passed, message in self.tests:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} - {test_name}")
            if message:
                print(f"       {message}")
        
        print("=" * 70)
        print(f"Total: {self.passed + self.failed} tests")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print("=" * 70)
        
        return self.failed == 0


def test_version_parsing(results):
    """Test version parsing functionality."""
    print("\n🧪 Testing version parsing...")
    
    test_cases = [
        ("2.1.3", (2, 1, 3)),
        ("1.0.0", (1, 0, 0)),
        ("10.20.30", (10, 20, 30)),
        ("0.0.1", (0, 0, 1)),
    ]
    
    for version_str, expected in test_cases:
        result = parse_version(version_str)
        passed = result == expected
        results.add_result(
            f"Parse version '{version_str}'",
            passed,
            f"Expected {expected}, got {result}"
        )
        print(f"  {'✅' if passed else '❌'} Parse '{version_str}' -> {result}")
    
    # Test invalid version
    result = parse_version("invalid")
    passed = result is None
    results.add_result(
        "Parse invalid version",
        passed,
        f"Expected None, got {result}"
    )
    print(f"  {'✅' if passed else '❌'} Parse 'invalid' -> {result}")


def test_version_increment(results):
    """Test version increment functionality."""
    print("\n🧪 Testing version increment...")
    
    test_cases = [
        ("2.1.3", "RELEASE: New major version", "3.0.0"),
        ("2.1.3", "MAJOR: Breaking changes", "3.0.0"),
        ("2.1.3", "MINOR: Add new feature", "2.2.0"),
        ("2.1.3", "FEATURE: Video enrichment", "2.2.0"),
        ("2.1.3", "PATCH: Fix memory leak", "2.1.4"),
        ("2.1.3", "FIX: Correct chunk_id", "2.1.4"),
        ("2.1.3", "BUGFIX: Handle empty pages", "2.1.4"),
        ("2.1.3", "Regular commit message", "2.1.3"),
        ("2.1.3", "fix: lowercase keyword", "2.1.4"),  # Case insensitive
        ("2.1.3", "minor: lowercase keyword", "2.2.0"),  # Case insensitive
    ]
    
    for version, message, expected in test_cases:
        result = increment_version(version, message)
        passed = result == expected
        results.add_result(
            f"Increment {version} with '{message[:30]}...'",
            passed,
            f"Expected {expected}, got {result}"
        )
        print(f"  {'✅' if passed else '❌'} {version} + '{message[:30]}...' -> {result}")


def test_commit_message_parsing(results):
    """Test commit message parsing."""
    print("\n🧪 Testing commit message parsing...")
    
    test_cases = [
        ("RELEASE: Version 3.0.0", "3.0.0"),
        ("release: lowercase", "3.0.0"),
        ("Release: Mixed case", "3.0.0"),
        ("MINOR: Add feature", "2.2.0"),
        ("FEATURE: New module", "2.2.0"),
        ("PATCH: Quick fix", "2.1.4"),
        ("FIX: Bug in processor", "2.1.4"),
        ("BUGFIX: Memory issue", "2.1.4"),
        ("No keyword here", "2.1.3"),
        ("", "2.1.3"),  # Empty message
    ]
    
    base_version = "2.1.3"
    
    for message, expected in test_cases:
        result = increment_version(base_version, message)
        passed = result == expected
        results.add_result(
            f"Parse message: '{message[:30]}'",
            passed,
            f"Expected {expected}, got {result}"
        )
        print(f"  {'✅' if passed else '❌'} '{message[:30]}' -> {result}")


def test_version_file_format(results):
    """Test version file format validation."""
    print("\n🧪 Testing version file format...")
    
    # Create a temporary version file
    version_content = '''"""Version information for KRAI processors."""

__version__ = "2.1.3"
__commit__ = "b676d3e"
__date__ = "2025-10-23"

# Version History:
# 2.1.3 (b676d3e) - Test version
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(version_content)
        temp_file = Path(f.name)
    
    try:
        # Read and validate format
        content = temp_file.read_text(encoding='utf-8')
        
        # Check for required fields
        has_version = bool(re.search(r'__version__\s*=\s*"[^"]+"', content))
        has_commit = bool(re.search(r'__commit__\s*=\s*"[^"]+"', content))
        has_date = bool(re.search(r'__date__\s*=\s*"[^"]+"', content))
        
        results.add_result("Version file has __version__", has_version)
        results.add_result("Version file has __commit__", has_commit)
        results.add_result("Version file has __date__", has_date)
        
        print(f"  {'✅' if has_version else '❌'} Has __version__ field")
        print(f"  {'✅' if has_commit else '❌'} Has __commit__ field")
        print(f"  {'✅' if has_date else '❌'} Has __date__ field")
        
        # Test regex replacement
        new_content = re.sub(r'__version__\s*=\s*"[^"]+"', '__version__ = "2.2.0"', content)
        new_content = re.sub(r'__commit__\s*=\s*"[^"]+"', '__commit__ = "abc1234"', new_content)
        new_content = re.sub(r'__date__\s*=\s*"[^"]+"', '__date__ = "2025-10-29"', new_content)
        
        has_new_version = '__version__ = "2.2.0"' in new_content
        has_new_commit = '__commit__ = "abc1234"' in new_content
        has_new_date = '__date__ = "2025-10-29"' in new_content
        
        results.add_result("Regex replacement for __version__", has_new_version)
        results.add_result("Regex replacement for __commit__", has_new_commit)
        results.add_result("Regex replacement for __date__", has_new_date)
        
        print(f"  {'✅' if has_new_version else '❌'} Regex replacement for __version__")
        print(f"  {'✅' if has_new_commit else '❌'} Regex replacement for __commit__")
        print(f"  {'✅' if has_new_date else '❌'} Regex replacement for __date__")
        
    finally:
        temp_file.unlink()


def test_error_handling(results):
    """Test error handling."""
    print("\n🧪 Testing error handling...")
    
    # Test with invalid version
    result = parse_version("not.a.version")
    passed = result is None
    results.add_result("Handle invalid version format", passed)
    print(f"  {'✅' if passed else '❌'} Invalid version returns None")
    
    # Test with None commit message
    result = increment_version("2.1.3", None)
    passed = result == "2.1.3"
    results.add_result("Handle None commit message", passed)
    print(f"  {'✅' if passed else '❌'} None message keeps version unchanged")
    
    # Test with empty commit message
    result = increment_version("2.1.3", "")
    passed = result == "2.1.3"
    results.add_result("Handle empty commit message", passed)
    print(f"  {'✅' if passed else '❌'} Empty message keeps version unchanged")


def main():
    """Run all tests."""
    print("=" * 70)
    print("KRAI VERSION HOOK TEST SUITE")
    print("=" * 70)
    
    results = TestResults()
    
    # Run all tests
    test_version_parsing(results)
    test_version_increment(results)
    test_commit_message_parsing(results)
    test_version_file_format(results)
    test_error_handling(results)
    
    # Print summary
    all_passed = results.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
