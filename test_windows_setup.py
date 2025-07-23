#!/usr/bin/env python3
"""
Test script to verify Windows setup is working correctly.
Run this script after installing dependencies with: pip install -e .
"""

import platform
import sys


def test_basic_imports():
    """Test basic package imports."""
    print("🔍 Testing basic imports...")
    
    try:
        from mcp_log_analyzer.core.models import LogSource, LogType
        print("  ✅ Core models import successful")
    except Exception as e:
        print(f"  ❌ Core models import failed: {e}")
        return False
    
    try:
        from mcp_log_analyzer.parsers.csv_parser import CsvLogParser
        print("  ✅ CSV parser import successful")
    except Exception as e:
        print(f"  ❌ CSV parser import failed: {e}")
        return False
    
    return True


def test_windows_specific():
    """Test Windows-specific functionality."""
    print("\n🪟 Testing Windows-specific functionality...")
    
    if platform.system() != "Windows":
        print("  ⚠️  Skipping Windows tests (not on Windows)")
        return True
    
    try:
        import win32evtlog
        import win32evtlogutil
        import win32con
        print("  ✅ Windows Event Log modules available")
        
        from mcp_log_analyzer.parsers.evt_parser import EvtParser
        print("  ✅ Event Log parser import successful")
        return True
    except ImportError as e:
        print(f"  ❌ Windows Event Log modules not available: {e}")
        print("  💡 Install with: pip install pywin32>=300")
        return False


def test_server_startup():
    """Test MCP server startup."""
    print("\n🚀 Testing MCP server startup...")
    
    try:
        from mcp_log_analyzer.mcp_server.server import mcp
        print("  ✅ MCP server import successful")
        
        # Check available parsers
        from mcp_log_analyzer.mcp_server.server import parsers
        print(f"  📋 Available parsers: {list(parsers.keys())}")
        
        return True
    except Exception as e:
        print(f"  ❌ MCP server startup failed: {e}")
        return False


def test_csv_functionality():
    """Test CSV parsing functionality."""
    print("\n📊 Testing CSV functionality...")
    
    try:
        from mcp_log_analyzer.core.models import LogSource, LogType
        from mcp_log_analyzer.parsers.csv_parser import CsvLogParser
        
        # Create test data
        source = LogSource(name="test", type=LogType.CSV, path="test.csv")
        parser = CsvLogParser({
            'has_header': False,
            'field_names': ['timestamp', 'level', 'message']
        })
        
        # Test parsing
        test_content = """2025-01-01 10:00:00,INFO,Test message
2025-01-01 10:01:00,ERROR,Test error"""
        
        records = list(parser.parse_content(source, test_content))
        print(f"  ✅ Parsed {len(records)} test records")
        
        # Test analysis
        analysis = parser.analyze(records)
        print(f"  ✅ Analysis completed: {analysis['summary']['total_records']} records")
        
        return True
    except Exception as e:
        print(f"  ❌ CSV functionality test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 MCP Log Analyzer Windows Setup Test")
    print("=" * 50)
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}")
    print()
    
    tests = [
        test_basic_imports,
        test_windows_specific,
        test_server_startup,
        test_csv_functionality,
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! The setup is working correctly.")
        print("\n💡 You can now run: python main.py")
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")
        if platform.system() == "Windows":
            print("\n💡 Try installing Windows dependencies:")
            print("   pip install pywin32>=300")
    
    return passed == len(tests)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)