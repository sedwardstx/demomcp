#!/usr/bin/env python3
"""
Test script to verify TCP proxy functionality.
"""

import asyncio
import json
import sys
import time

async def test_tcp_connection(host='localhost', port=8080):
    """Test connection to TCP MCP server."""
    print(f"Testing TCP MCP proxy at {host}:{port}...")
    
    try:
        reader, writer = await asyncio.open_connection(host, port)
        print("✓ Connected to TCP server")
        
        # Test 1: Initialize request
        print("\n1. Testing initialize request...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        # Send request
        request_line = json.dumps(init_request) + '\n'
        writer.write(request_line.encode('utf-8'))
        await writer.drain()
        print("   Sent initialize request")
        
        # Read response
        response_line = await asyncio.wait_for(reader.readline(), timeout=5.0)
        if response_line:
            response = json.loads(response_line.decode('utf-8'))
            print("   ✓ Received initialize response")
            print(f"   Server: {response.get('result', {}).get('serverInfo', {})}")
        else:
            print("   ✗ No response received")
            return
        
        # Test 2: List tools
        print("\n2. Testing tools/list request...")
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        request_line = json.dumps(tools_request) + '\n'
        writer.write(request_line.encode('utf-8'))
        await writer.drain()
        print("   Sent tools/list request")
        
        response_line = await asyncio.wait_for(reader.readline(), timeout=5.0)
        if response_line:
            response = json.loads(response_line.decode('utf-8'))
            tools = response.get('result', {}).get('tools', [])
            print(f"   ✓ Received {len(tools)} tools")
            for tool in tools[:5]:  # Show first 5 tools
                print(f"     - {tool.get('name')}: {tool.get('description', '')[:50]}...")
        
        # Test 3: List resources
        print("\n3. Testing resources/list request...")
        resources_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "resources/list",
            "params": {}
        }
        
        request_line = json.dumps(resources_request) + '\n'
        writer.write(request_line.encode('utf-8'))
        await writer.drain()
        print("   Sent resources/list request")
        
        response_line = await asyncio.wait_for(reader.readline(), timeout=5.0)
        if response_line:
            response = json.loads(response_line.decode('utf-8'))
            resources = response.get('result', {}).get('resources', [])
            print(f"   ✓ Received {len(resources)} resources")
            for resource in resources[:5]:  # Show first 5 resources
                print(f"     - {resource.get('uri')}: {resource.get('name', '')}")
        
        # Test 4: Call a tool
        print("\n4. Testing tool call (list_log_sources)...")
        tool_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "list_log_sources",
                "arguments": {}
            }
        }
        
        request_line = json.dumps(tool_request) + '\n'
        writer.write(request_line.encode('utf-8'))
        await writer.drain()
        print("   Sent tool call request")
        
        response_line = await asyncio.wait_for(reader.readline(), timeout=5.0)
        if response_line:
            response = json.loads(response_line.decode('utf-8'))
            if 'result' in response:
                print("   ✓ Tool call successful")
                result = response.get('result', {})
                if 'content' in result:
                    print(f"   Result: {str(result['content'])[:100]}...")
            elif 'error' in response:
                print(f"   ✗ Tool call error: {response['error']}")
        
        # Test 5: Shutdown
        print("\n5. Testing shutdown...")
        shutdown_request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "shutdown",
            "params": {}
        }
        
        request_line = json.dumps(shutdown_request) + '\n'
        writer.write(request_line.encode('utf-8'))
        await writer.drain()
        print("   Sent shutdown request")
        
        response_line = await asyncio.wait_for(reader.readline(), timeout=5.0)
        if response_line:
            response = json.loads(response_line.decode('utf-8'))
            print("   ✓ Received shutdown response")
        
        # Close connection
        writer.close()
        await writer.wait_closed()
        print("\n✓ All tests completed successfully!")
        
    except asyncio.TimeoutError:
        print("✗ Timeout waiting for response")
        sys.exit(1)
    except ConnectionRefusedError:
        print("✗ Could not connect to TCP server. Make sure the proxy is running:")
        print("  python tcp_proxy.py python main.py")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Test TCP proxy connection')
    parser.add_argument('--host', default='localhost', help='Host to connect to')
    parser.add_argument('--port', type=int, default=8080, help='Port to connect to')
    args = parser.parse_args()
    
    asyncio.run(test_tcp_connection(args.host, args.port))