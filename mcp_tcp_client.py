#!/usr/bin/env python3
"""
TCP client for connecting to remote MCP servers.
Bridges stdio to TCP connection with automatic reconnection and heartbeat support.
"""

import asyncio
import sys
import json
import argparse
import logging
import time
from typing import Optional, Tuple, Dict, Any
from collections import deque

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class TCPClient:
    """TCP client with automatic reconnection and heartbeat support."""
    
    def __init__(self, host: str, port: int, reconnect_delay: float = 2.0, 
                 max_reconnect_attempts: int = 50, heartbeat_interval: float = 30.0):
        self.host = host
        self.port = port
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_attempts = max_reconnect_attempts
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_timeout = heartbeat_interval * 2
        self.connection_state = {
            'connected': False,
            'last_heartbeat_sent': 0,
            'last_heartbeat_received': 0,
            'server_supports_heartbeat': False,
            'mcp_initialized': False,
            'initialization_in_progress': False,
            'pending_initialize_id': None
        }
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.reconnect_attempts = 0
        self.should_reconnect = True
        self.buffered_requests = deque()
    
    async def connect(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """Connect to TCP server with retry logic."""
        while self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                logger.info(f"Connecting to {self.host}:{self.port} (attempt {self.reconnect_attempts + 1}/{self.max_reconnect_attempts})")
                reader, writer = await asyncio.open_connection(self.host, self.port)
                logger.info(f"Connected to {self.host}:{self.port}")
                
                self.reader = reader
                self.writer = writer
                self.connection_state['connected'] = True
                self.connection_state['mcp_initialized'] = False
                self.connection_state['initialization_in_progress'] = False
                self.connection_state['pending_initialize_id'] = None
                self.buffered_requests.clear()
                self.reconnect_attempts = 0
                
                # Send handshake to indicate we support heartbeat
                await self.send_handshake()
                
                return reader, writer
                
            except Exception as e:
                self.reconnect_attempts += 1
                logger.error(f"Connection failed: {e}")
                
                if self.reconnect_attempts < self.max_reconnect_attempts:
                    logger.info(f"Retrying in {self.reconnect_delay} seconds...")
                    await asyncio.sleep(self.reconnect_delay)
                else:
                    logger.error("Max reconnection attempts reached")
                    raise
        
        raise Exception("Failed to connect after maximum attempts")
    
    async def send_handshake(self):
        """Send handshake message to indicate heartbeat support."""
        if self.writer:
            handshake = {
                'type': 'handshake',
                'client_version': '1.0',
                'supports_heartbeat': True
            }
            message_str = json.dumps(handshake) + '\n'
            self.writer.write(message_str.encode('utf-8'))
            await self.writer.drain()
    
    async def send_heartbeat(self):
        """Send heartbeat message."""
        if self.writer and not self.writer.is_closing():
            heartbeat = {
                'type': 'heartbeat',
                'timestamp': time.time()
            }
            message_str = json.dumps(heartbeat) + '\n'
            self.writer.write(message_str.encode('utf-8'))
            await self.writer.drain()
            self.connection_state['last_heartbeat_sent'] = time.time()
    
    async def handle_heartbeat_response(self, message: dict):
        """Handle heartbeat response from server."""
        self.connection_state['last_heartbeat_received'] = time.time()
        self.connection_state['server_supports_heartbeat'] = True
        
        if not message.get('mcp_alive', True):
            logger.warning("Server reports MCP process is not alive")
    
    async def disconnect(self):
        """Disconnect from server."""
        self.connection_state['connected'] = False
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
    
    async def run(self):
        """Main client loop with automatic reconnection."""
        while self.should_reconnect:
            try:
                # Connect to server
                reader, writer = await self.connect()
                
                # Create tasks for communication and heartbeat
                stdin_to_tcp = asyncio.create_task(self.forward_stdin_to_tcp())
                tcp_to_stdout = asyncio.create_task(self.forward_tcp_to_stdout())
                heartbeat_task = asyncio.create_task(self.heartbeat_loop())
                
                # Wait for any task to complete
                done, pending = await asyncio.wait(
                    [stdin_to_tcp, tcp_to_stdout, heartbeat_task],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Cancel remaining tasks
                for task in pending:
                    task.cancel()
                
                # Wait for cancellation
                await asyncio.gather(*pending, return_exceptions=True)
                
                # Disconnect
                await self.disconnect()
                
                # Check if we should reconnect
                if self.should_reconnect and self.reconnect_attempts < self.max_reconnect_attempts:
                    logger.info(f"Connection lost, reconnecting in {self.reconnect_delay} seconds...")
                    await asyncio.sleep(self.reconnect_delay)
                else:
                    break
                    
            except KeyboardInterrupt:
                logger.info("Interrupted by user")
                self.should_reconnect = False
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                if self.should_reconnect:
                    await asyncio.sleep(self.reconnect_delay)
                else:
                    break
    
    async def forward_stdin_to_tcp(self):
        """Forward stdin to TCP connection with MCP initialization tracking."""
        loop = asyncio.get_event_loop()
        stdin = sys.stdin
        
        while self.connection_state['connected']:
            try:
                # Read line from stdin (blocking in executor)
                line = await loop.run_in_executor(None, stdin.readline)
                if not line:
                    logger.info("Stdin closed")
                    self.should_reconnect = False
                    break
                
                # Parse and check if it's an MCP message
                try:
                    message = json.loads(line.strip())
                    
                    # Handle initialize request
                    if message.get('method') == 'initialize':
                        logger.debug("Detected initialize request")
                        self.connection_state['initialization_in_progress'] = True
                        self.connection_state['pending_initialize_id'] = message.get('id')
                    
                    # Handle initialized notification
                    elif message.get('method') == 'notifications/initialized':
                        logger.debug("Detected initialized notification")
                        self.connection_state['mcp_initialized'] = True
                        self.connection_state['initialization_in_progress'] = False
                        
                        # Process any buffered requests after initialization
                        while self.buffered_requests:
                            buffered_line = self.buffered_requests.popleft()
                            if self.writer and not self.writer.is_closing():
                                self.writer.write(buffered_line.encode('utf-8'))
                                await self.writer.drain()
                                await asyncio.sleep(0.01)
                    
                    # Buffer non-init requests if not initialized
                    elif (not self.connection_state['mcp_initialized'] and 
                          'method' in message and 
                          message['method'] not in ['initialize', 'notifications/initialized']):
                        logger.warning(f"Buffering request '{message.get('method')}' until initialization complete")
                        self.buffered_requests.append(line)
                        
                        # Send temporary error response
                        if 'id' in message:
                            error_response = {
                                'jsonrpc': '2.0',
                                'id': message['id'],
                                'error': {
                                    'code': -32002,
                                    'message': 'Server initialization pending',
                                    'data': 'Waiting for MCP initialization to complete'
                                }
                            }
                            sys.stdout.write(json.dumps(error_response) + '\n')
                            sys.stdout.flush()
                        continue
                        
                except json.JSONDecodeError:
                    # If not JSON, still forward it
                    pass
                
                # Send to TCP
                if self.writer and not self.writer.is_closing():
                    self.writer.write(line.encode('utf-8'))
                    await self.writer.drain()
                else:
                    logger.warning("Connection closed, unable to send")
                    break
                    
            except Exception as e:
                logger.error(f"Error forwarding stdin: {e}")
                break
    
    async def forward_tcp_to_stdout(self):
        """Forward TCP to stdout, handling heartbeats and tracking initialization."""
        while self.connection_state['connected']:
            try:
                # Read from TCP
                if not self.reader:
                    break
                    
                line = await self.reader.readline()
                if not line:
                    logger.info("TCP connection closed")
                    break
                
                # Try to parse as JSON to check for heartbeat or initialization response
                try:
                    message_str = line.decode('utf-8').strip()
                    message = json.loads(message_str)
                    
                    # Handle heartbeat responses
                    if message.get('type') == 'heartbeat_response':
                        await self.handle_heartbeat_response(message)
                        # Don't forward heartbeats to stdout
                        continue
                    
                    # Check if this is a response to initialize request
                    if (self.connection_state['initialization_in_progress'] and
                        'id' in message and 
                        message['id'] == self.connection_state['pending_initialize_id']):
                        logger.debug("Received initialize response")
                        # Initialization response received, waiting for initialized notification
                        
                except json.JSONDecodeError:
                    # Not JSON, just forward as-is
                    pass
                
                # Write to stdout
                sys.stdout.write(line.decode('utf-8'))
                sys.stdout.flush()
                
            except Exception as e:
                logger.error(f"Error forwarding TCP: {e}")
                break
    
    async def heartbeat_loop(self):
        """Send periodic heartbeats to server."""
        await asyncio.sleep(5)  # Initial delay
        
        while self.connection_state['connected']:
            try:
                # Send heartbeat
                await self.send_heartbeat()
                
                # Wait for next interval
                await asyncio.sleep(self.heartbeat_interval)
                
                # Check if server supports heartbeat and we haven't received one recently
                if self.connection_state['server_supports_heartbeat']:
                    time_since_last = time.time() - self.connection_state['last_heartbeat_received']
                    if time_since_last > self.heartbeat_timeout:
                        logger.warning(f"Server heartbeat timeout ({time_since_last:.1f}s since last response)")
                        # Connection might be dead, let TCP detect it
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(self.heartbeat_interval)


async def bridge_stdio_to_tcp(host: str, port: int, **kwargs):
    """Bridge stdio to TCP connection with automatic reconnection."""
    client = TCPClient(host, port, **kwargs)
    await client.run()




def main():
    parser = argparse.ArgumentParser(description='TCP client for MCP servers with reconnection support')
    parser.add_argument('host', help='Remote host to connect to')
    parser.add_argument('port', type=int, help='Remote port to connect to')
    parser.add_argument('--reconnect-delay', type=float, default=2.0,
                       help='Delay between reconnection attempts in seconds (default: 2)')
    parser.add_argument('--max-reconnect-attempts', type=int, default=50,
                       help='Maximum number of reconnection attempts (default: 50)')
    parser.add_argument('--heartbeat-interval', type=float, default=30.0,
                       help='Heartbeat interval in seconds (default: 30)')
    parser.add_argument('--no-reconnect', action='store_true',
                       help='Disable automatic reconnection')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Set up client parameters
    client_kwargs = {
        'reconnect_delay': args.reconnect_delay,
        'max_reconnect_attempts': 1 if args.no_reconnect else args.max_reconnect_attempts,
        'heartbeat_interval': args.heartbeat_interval
    }
    
    asyncio.run(bridge_stdio_to_tcp(args.host, args.port, **client_kwargs))


if __name__ == "__main__":
    main()