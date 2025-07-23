#!/usr/bin/env python3
"""
Standalone TCP MCP server for remote connections.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_log_analyzer.mcp_server.server import mcp


class TCPMCPServer:
    """TCP-based MCP server for remote connections."""
    
    def __init__(self, host="0.0.0.0", port=8080):
        self.host = host
        self.port = port
        self.logger = logging.getLogger(__name__)
        
    async def handle_client(self, reader, writer):
        """Handle a single client connection."""
        client_addr = writer.get_extra_info('peername')
        self.logger.info(f"Client connected from {client_addr}")
        
        try:
            while True:
                # Read JSON-RPC message
                line = await reader.readline()
                if not line:
                    break
                    
                try:
                    message = line.decode('utf-8').strip()
                    if not message:
                        continue
                        
                    self.logger.debug(f"Received: {message}")
                    
                    # Parse JSON-RPC message
                    request = json.loads(message)
                    
                    # Process the request through the MCP server
                    response = await self.process_mcp_request(request)
                    
                    # Send response
                    if response:
                        response_line = json.dumps(response) + '\n'
                        writer.write(response_line.encode('utf-8'))
                        await writer.drain()
                        self.logger.debug(f"Sent: {response_line.strip()}")
                        
                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON decode error: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    error_line = json.dumps(error_response) + '\n'
                    writer.write(error_line.encode('utf-8'))
                    await writer.drain()
                    
                except Exception as e:
                    self.logger.error(f"Error processing request: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32603,
                            "message": f"Internal error: {str(e)}"
                        }
                    }
                    error_line = json.dumps(error_response) + '\n'
                    writer.write(error_line.encode('utf-8'))
                    await writer.drain()
                    
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
        finally:
            self.logger.info(f"Client {client_addr} disconnected")
            writer.close()
            await writer.wait_closed()
    
    async def process_mcp_request(self, request):
        """Process an MCP request and return the response."""
        # This is a simplified implementation
        # In practice, you'd need to integrate with the actual MCP server logic
        
        method = request.get('method')
        params = request.get('params', {})
        request_id = request.get('id')
        
        if method == 'initialize':
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "resources": {"subscribe": False, "listChanged": False},
                        "prompts": {"listChanged": False}
                    },
                    "serverInfo": {
                        "name": "mcp-log-analyzer",
                        "version": "1.0.0"
                    }
                }
            }
        
        elif method == 'notifications/initialized':
            # No response needed for notifications
            return None
            
        elif method == 'tools/list':
            # Return available tools
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": "register_log_source",
                            "description": "Register a new log source for analysis",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "source_type": {"type": "string"},
                                    "path": {"type": "string"}
                                },
                                "required": ["name", "source_type", "path"]
                            }
                        }
                        # Add more tools as needed
                    ]
                }
            }
            
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
    
    async def start(self):
        """Start the TCP server."""
        self.logger.info(f"Starting MCP TCP server on {self.host}:{self.port}")
        
        server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port
        )
        
        addr = server.sockets[0].getsockname()
        self.logger.info(f"MCP server listening on {addr[0]}:{addr[1]}")
        
        async with server:
            await server.serve_forever()


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='MCP Log Analyzer TCP Server')
    parser.add_argument('--host', default='0.0.0.0', 
                       help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8080, 
                       help='Port to bind to (default: 8080)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Configure logging
    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and start server
    server = TCPMCPServer(args.host, args.port)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        print("\nServer stopped.")


if __name__ == "__main__":
    asyncio.run(main())