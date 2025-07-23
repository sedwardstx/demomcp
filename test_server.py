import sys

sys.path.insert(0, "src")

try:
    from mcp_log_analyzer.mcp_server.server import mcp

    print("=== MCP Server Debug Info ===")
    print(f"Server name: {mcp.name}")
    print("Server imported successfully")

    # Check what attributes the mcp object has
    print(f"MCP object type: {type(mcp)}")
    print(f'MCP attributes: {[attr for attr in dir(mcp) if not attr.startswith("_")]}')

    # Check for tools specifically
    if hasattr(mcp, "_tools"):
        tools = mcp._tools
        print(f"Tools found via _tools: {len(tools)}")
        if tools:
            print("Tool names:", list(tools.keys())[:5])

    if hasattr(mcp, "_handlers"):
        handlers = mcp._handlers
        print(f"Handlers found: {len(handlers)}")
        tool_handlers = {k: v for k, v in handlers.items() if "tool" in str(v)}
        print(f"Tool handlers: {len(tool_handlers)}")
        if tool_handlers:
            print("Tool handler names:", list(tool_handlers.keys())[:5])

    print("\nTesting tool import...")
    from mcp_log_analyzer.mcp_server.tools.network_test_tools import (
        register_network_test_tools,
    )

    print("✅ Network tools module imported successfully")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
