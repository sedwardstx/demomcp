#!/usr/bin/env python3
"""
Script to verify the MCP server is working correctly.
This simulates what Claude Code does when it connects to the server.
"""

import json
import subprocess
import sys
import time
from typing import Dict, Any


def send_mcp_request(process: subprocess.Popen, request: Dict[str, Any]) -> Dict[str, Any]:
    """Send an MCP request and get response."""
    request_json = json.dumps(request) + '\n'
    
    print(f"📤 Sending: {request['method']}")
    process.stdin.write(request_json.encode())
    process.stdin.flush()
    
    # Read response
    response_line = process.stdout.readline().decode().strip()
    if response_line:
        response = json.loads(response_line)
        print(f"📥 Response: {response.get('result', {}).get('meta', {}).get('name', 'Success')}")
        return response
    
    return {}


def send_mcp_notification(process: subprocess.Popen, notification: Dict[str, Any]) -> None:
    """Send an MCP notification (no response expected)."""
    notification_json = json.dumps(notification) + '\n'
    
    print(f"📤 Sending notification: {notification['method']}")
    process.stdin.write(notification_json.encode())
    process.stdin.flush()


def test_mcp_server():
    """Test the MCP server functionality."""
    print("🚀 Testing MCP Log Analyzer Server")
    print("=" * 50)
    
    # Start the server process
    try:
        process = subprocess.Popen(
            [sys.executable, 'main.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False  # We'll handle encoding ourselves
        )
        
        print("✅ Server process started (PID: {})".format(process.pid))
        
        # Give the server a moment to start
        time.sleep(0.5)
        
        # Test 1: Initialize connection
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "prompts": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        init_response = send_mcp_request(process, init_request)
        
        if 'result' in init_response:
            server_info = init_response['result']
            print(f"📋 Server Name: {server_info.get('serverInfo', {}).get('name', 'Unknown')}")
            print(f"📋 Server Version: {server_info.get('serverInfo', {}).get('version', 'Unknown')}")
            
            # Show capabilities
            capabilities = server_info.get('capabilities', {})
            if 'tools' in capabilities:
                print(f"🔧 Tools: Available")
            if 'resources' in capabilities:
                print(f"📂 Resources: Available")
            if 'prompts' in capabilities:
                print(f"💬 Prompts: Available")
        
        # CRITICAL: Send initialized notification to complete the handshake
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        
        send_mcp_notification(process, initialized_notification)
        print("✅ Initialization handshake completed")
        
        # Small delay to ensure the notification is processed
        time.sleep(0.1)
        
        # Test 2: List available tools
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        tools_response = send_mcp_request(process, tools_request)
        
        if 'result' in tools_response:
            tools = tools_response['result'].get('tools', [])
            if isinstance(tools, list):
                print(f"\n🔧 Available Tools ({len(tools)}):")
                for tool in tools[:10]:  # Show first 10
                    print(f"  • {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')[:60]}...")
                if len(tools) > 10:
                    print(f"  ... and {len(tools) - 10} more tools")
            else:
                print(f"\n🔧 Tools response: {tools}")
        
        # Test 3: List available resources
        resources_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "resources/list",
            "params": {}
        }
        
        resources_response = send_mcp_request(process, resources_request)
        
        if 'result' in resources_response:
            resources = resources_response['result'].get('resources', [])
            if isinstance(resources, list):
                print(f"\n📂 Available Resources ({len(resources)}):")
                for resource in resources[:10]:  # Show first 10
                    print(f"  • {resource.get('uri', 'Unknown')}: {resource.get('description', 'No description')[:60]}...")
                if len(resources) > 10:
                    print(f"  ... and {len(resources) - 10} more resources")
            else:
                print(f"\n📂 Resources response: {resources}")
        
        print(f"\n✅ MCP Server is working correctly!")
        print(f"\n💡 To use with Claude Code:")
        print(f"   claude mcp add mcp-log-analyzer python main.py")
        print(f"   claude mcp list")
        
        # Clean shutdown
        process.terminate()
        process.wait(timeout=5)
        
    except subprocess.TimeoutExpired:
        print("⚠️  Server didn't respond in time")
        process.kill()
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        if 'process' in locals():
            process.terminate()


def show_usage_instructions():
    """Show how to use the MCP server."""
    print("\n" + "=" * 50)
    print("📖 HOW TO USE THE MCP SERVER")
    print("=" * 50)
    
    print("\n1. 🚀 START THE SERVER:")
    print("   python main.py")
    print("   (Server runs silently, waiting for MCP connections)")
    
    print("\n2. 🔗 CONNECT WITH CLAUDE CODE:")
    print("   claude mcp add mcp-log-analyzer python main.py")
    print("   claude mcp list")
    
    print("\n3. 📊 USE IN CLAUDE CONVERSATIONS:")
    print("   - Register log sources")
    print("   - Analyze CSV/Event logs") 
    print("   - Monitor system resources")
    print("   - Get network diagnostics")
    
    print("\n4. 🧪 TEST THE SERVER:")
    print("   python check_server.py")
    
    print("\n📚 Available Tools:")
    print("   • register_log_source - Add new log sources")
    print("   • list_log_sources - View registered sources") 
    print("   • query_logs - Search and filter logs")
    print("   • analyze_logs - Perform log analysis")
    print("   • test_network_tools_availability - Check network tools")
    print("   • diagnose_network_issues - Network diagnostics")
    print("   • And many more...")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--usage":
        show_usage_instructions()
    else:
        test_mcp_server()
        show_usage_instructions()