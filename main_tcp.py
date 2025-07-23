#!/usr/bin/env python3
"""
TCP-enabled entry point for the MCP Log Analyzer server.
"""

import asyncio
import argparse
import sys
import json
import logging
from pathlib import Path
from typing import Optional

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_log_analyzer.mcp_server.server import mcp

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TCPTransport:
    """Transport layer for TCP-based MCP communication."""
    
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer
        self._buffer = b""
        self._closed = False
    
    async def read_message(self) -> Optional[dict]:
        """Read a complete JSON-RPC message."""
        try:
            while True:
                # Look for newline in buffer
                newline_pos = self._buffer.find(b'\n')
                if newline_pos != -1:
                    # Extract complete message
                    message_bytes = self._buffer[:newline_pos]
                    self._buffer = self._buffer[newline_pos + 1:]
                    
                    if message_bytes:
                        message_str = message_bytes.decode('utf-8')
                        return json.loads(message_str)
                
                # Read more data
                chunk = await self.reader.read(4096)
                if not chunk:
                    # Connection closed
                    self._closed = True
                    return None
                
                self._buffer += chunk
                
        except Exception as e:
            logger.error(f"Error reading message: {e}")
            return None
    
    async def write_message(self, message: dict) -> None:
        """Write a JSON-RPC message."""
        try:
            message_str = json.dumps(message)
            message_bytes = (message_str + '\n').encode('utf-8')
            self.writer.write(message_bytes)
            await self.writer.drain()
        except Exception as e:
            logger.error(f"Error writing message: {e}")
            raise
    
    def is_closed(self) -> bool:
        """Check if transport is closed."""
        return self._closed
    
    async def close(self) -> None:
        """Close the transport."""
        self._closed = True
        self.writer.close()
        await self.writer.wait_closed()


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """Handle a single client connection."""
    addr = writer.get_extra_info('peername')
    logger.info(f"New client connected from {addr}")
    
    transport = TCPTransport(reader, writer)
    
    try:
        # Create a bridge between TCP transport and MCP server
        # We'll need to handle the JSON-RPC protocol directly
        
        while not transport.is_closed():
            # Read incoming message
            request = await transport.read_message()
            if request is None:
                break
            
            logger.debug(f"Received request: {request}")
            
            # Process the request through MCP
            # For now, we'll handle basic protocol messages
            if request.get('method') == 'initialize':
                # Handle initialization
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get('id'),
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {"listChanged": True},
                            "resources": {"subscribe": True, "listChanged": True},
                            "prompts": {"listChanged": True}
                        },
                        "serverInfo": {
                            "name": "mcp-log-analyzer",
                            "version": "0.1.0"
                        }
                    }
                }
                await transport.write_message(response)
                
            elif request.get('method') == 'tools/list':
                # List available tools
                # This is a simplified response - in production you'd query the MCP server
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get('id'),
                    "result": {
                        "tools": [
                            {
                                "name": "register_log_source",
                                "description": "Register a new log source for analysis"
                            },
                            {
                                "name": "query_logs",
                                "description": "Query logs with filters"
                            }
                        ]
                    }
                }
                await transport.write_message(response)
                
            elif request.get('method') == 'shutdown':
                # Handle shutdown
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get('id'),
                    "result": {}
                }
                await transport.write_message(response)
                break
                
            else:
                # Unknown method
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get('id'),
                    "error": {
                        "code": -32601,
                        "message": "Method not found"
                    }
                }
                await transport.write_message(response)
                
    except Exception as e:
        logger.error(f"Error handling client {addr}: {e}", exc_info=True)
    finally:
        logger.info(f"Client {addr} disconnected")
        await transport.close()


async def run_mcp_stdio_server():
    """Run the MCP server in stdio mode with async support."""
    # This is a placeholder - we need to integrate with FastMCP's async capabilities
    # For now, we'll use the synchronous run method
    await asyncio.get_event_loop().run_in_executor(None, mcp.run)


async def main_tcp(host="0.0.0.0", port=8080):
    """Run the MCP server on a TCP port."""
    logger.info(f"Starting MCP Log Analyzer TCP server on {host}:{port}")
    
    server = await asyncio.start_server(
        handle_client, 
        host, 
        port
    )
    
    addr = server.sockets[0].getsockname()
    logger.info(f"MCP server listening on {addr[0]}:{addr[1]}")
    
    async with server:
        await server.serve_forever()


def main():
    """Parse arguments and run the appropriate server."""
    parser = argparse.ArgumentParser(description='MCP Log Analyzer Server')
    parser.add_argument('--tcp', action='store_true', 
                       help='Run server on TCP port instead of stdio')
    parser.add_argument('--host', default='0.0.0.0', 
                       help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8080, 
                       help='Port to bind to (default: 8080)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.tcp:
        try:
            asyncio.run(main_tcp(args.host, args.port))
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
    else:
        # Run in stdio mode (original behavior)
        mcp.run()


if __name__ == "__main__":
    main()