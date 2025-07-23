# TCP Proxy for MCP Servers

This TCP proxy allows MCP servers that use stdio communication to be accessed over TCP connections.

## Architecture

The proxy works by:
1. Accepting TCP connections from clients
2. Spawning a new MCP server process for each client
3. Bridging communication between the TCP socket and the MCP process stdio

## Usage

### Running the TCP Proxy

```bash
# Basic usage
python tcp_proxy.py python main.py

# With custom host and port
python tcp_proxy.py --host 0.0.0.0 --port 9000 python main.py

# With debug logging
python tcp_proxy.py --debug python main.py

# For any MCP server command
python tcp_proxy.py node my-mcp-server.js
python tcp_proxy.py ./my-mcp-binary
```

### Testing the Proxy

```bash
# Run the test script
python test_tcp_proxy.py
```

The test script will:
1. Connect to the TCP proxy
2. Send initialize request
3. List available tools
4. List available resources  
5. Call a sample tool
6. Send shutdown request

### Example Client Code

```python
import asyncio
import json

async def connect_to_mcp():
    reader, writer = await asyncio.open_connection('localhost', 8080)
    
    # Send initialize
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "my-client",
                "version": "1.0.0"
            }
        }
    }
    
    writer.write((json.dumps(request) + '\n').encode('utf-8'))
    await writer.drain()
    
    # Read response
    response = await reader.readline()
    print(json.loads(response))
    
    # Close connection
    writer.close()
    await writer.wait_closed()

asyncio.run(connect_to_mcp())
```

## Features

- **Process Isolation**: Each client gets its own MCP server process
- **Bidirectional Communication**: Full duplex between TCP and stdio
- **Error Handling**: Graceful handling of disconnections and errors
- **Debug Logging**: Optional debug mode to trace all messages
- **Stderr Monitoring**: Captures and logs MCP server stderr output

## Protocol

The proxy uses newline-delimited JSON-RPC 2.0 messages:
- Each message must be a complete JSON object
- Messages are separated by newline characters (`\n`)
- The proxy does not modify messages, it only forwards them

## Limitations

- The current `main_tcp.py` implementation has issues with stdio redirection
- Use `tcp_proxy.py` instead for reliable TCP access to MCP servers
- Each connection spawns a new process (consider connection pooling for production)

## Troubleshooting

If you get connection refused errors:
1. Make sure the proxy is running
2. Check the port is not already in use
3. Verify firewall settings

If you get timeout errors:
1. The MCP server may be taking too long to start
2. Check for errors in the MCP server stderr (use --debug)
3. Verify the MCP command is correct