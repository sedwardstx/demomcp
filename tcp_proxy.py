#!/usr/bin/env python3
"""
TCP proxy for MCP servers that bridges TCP connections to stdio-based MCP servers.
Enhanced with automatic process restart, heartbeat, and connection resilience.
"""

import asyncio
import argparse
import json
import logging
import time
from typing import Optional, Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MCPProcess:
    """Manages an MCP server subprocess with automatic restart capability."""
    
    def __init__(self, command: list[str], auto_restart: bool = True):
        self.command = command
        self.process: Optional[asyncio.subprocess.Process] = None
        self._closed = False
        self.auto_restart = auto_restart
        self.restart_count = 0
        self.max_restarts = 5
        self.last_restart_time = 0
        self.restart_cooldown = 5.0  # Minimum seconds between restarts
    
    async def start(self):
        """Start the MCP server process."""
        logger.info(f"Starting MCP server: {' '.join(self.command)}")
        self.process = await asyncio.create_subprocess_exec(
            *self.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            limit=10 * 1024 * 1024  # 10MB limit for large responses
        )
        logger.info(f"MCP server started with PID {self.process.pid}")
        self.last_restart_time = time.time()
    
    async def restart(self) -> bool:
        """Restart the MCP server process if allowed."""
        if not self.auto_restart:
            return False
            
        current_time = time.time()
        # Reduce cooldown for normal restarts (process completed successfully)
        cooldown = self.restart_cooldown if self.restart_count > 0 else 1.0
        if current_time - self.last_restart_time < cooldown:
            wait_time = cooldown - (current_time - self.last_restart_time)
            logger.info(f"Waiting {wait_time:.1f}s before restart (cooldown)")
            await asyncio.sleep(wait_time)
        
        if self.restart_count >= self.max_restarts:
            logger.error(f"Max restarts ({self.max_restarts}) reached, not restarting")
            return False
        
        self.restart_count += 1
        logger.info(f"Restarting MCP server (attempt {self.restart_count}/{self.max_restarts})")
        
        # Close existing process
        if self.process:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Process didn't terminate, killing it")
                self.process.kill()
                await self.process.wait()
        
        self._closed = False
        self.process = None
        
        # Start new process
        try:
            await self.start()
            logger.info("MCP server restarted successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to restart MCP server: {e}")
            return False
    
    def is_alive(self) -> bool:
        """Check if the process is still running."""
        return self.process is not None and self.process.returncode is None
    
    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send a message to the MCP server."""
        if self.process is None or self.process.stdin is None:
            raise RuntimeError("MCP process not started")
        
        message_str = json.dumps(message) + '\n'
        self.process.stdin.write(message_str.encode('utf-8'))
        await self.process.stdin.drain()
    
    async def read_message(self) -> Optional[Dict[str, Any]]:
        """Read a message from the MCP server."""
        if self.process is None or self.process.stdout is None:
            raise RuntimeError("MCP process not started")
        
        try:
            # Increase the limit for readline to handle larger responses
            line = await self.process.stdout.readline()
            if not line:
                return None
            
            message_str = line.decode('utf-8').strip()
            if message_str:
                return json.loads(message_str)
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON: {e}")
            return None
    
    async def read_stderr(self) -> Optional[str]:
        """Read from stderr (non-blocking)."""
        if self.process is None or self.process.stderr is None:
            return None
        
        try:
            # Try to read stderr without blocking
            line = await asyncio.wait_for(
                self.process.stderr.readline(), 
                timeout=0.1
            )
            if line:
                return line.decode('utf-8').strip()
        except asyncio.TimeoutError:
            pass
        return None
    
    async def close(self) -> None:
        """Close the MCP server process."""
        if self.process is not None and not self._closed:
            self._closed = True
            self.auto_restart = False  # Disable auto-restart on explicit close
            if self.process.stdin:
                self.process.stdin.close()
            self.process.terminate()
            await self.process.wait()
            logger.info(f"MCP server process {self.process.pid} terminated")


class TCPToMCPBridge:
    """Bridges TCP connections to MCP server processes with heartbeat support."""
    
    def __init__(self, mcp_command: list[str], heartbeat_interval: float = 30.0):
        self.mcp_command = mcp_command
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_timeout = heartbeat_interval * 2
    
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Handle a TCP client connection with resilience."""
        addr = writer.get_extra_info('peername')
        logger.info(f"New client connected from {addr}")
        
        # Track connection state
        connection_state = {
            'last_heartbeat_sent': time.time(),
            'last_heartbeat_received': time.time(),
            'connected': True,
            'client_supports_heartbeat': False,
            'mcp_initialized': False,
            'pending_requests': {},  # Track pending requests
            'last_request_id': None,
            'writer': writer  # Store writer for use in process monitor
        }
        
        # Start MCP process for this client
        mcp_process = MCPProcess(self.mcp_command, auto_restart=True)
        
        try:
            await mcp_process.start()
            
            # Don't initialize MCP session here - let the client drive it
            # The client will send the initialize request when ready
            logger.info("MCP process started, waiting for client initialization...")
            
            # Create tasks for bidirectional communication
            tcp_to_mcp_task = asyncio.create_task(
                self._tcp_to_mcp(reader, mcp_process, connection_state)
            )
            mcp_to_tcp_task = asyncio.create_task(
                self._mcp_to_tcp(mcp_process, writer, connection_state)
            )
            stderr_monitor_task = asyncio.create_task(
                self._monitor_stderr(mcp_process)
            )
            heartbeat_task = asyncio.create_task(
                self._heartbeat_loop(writer, mcp_process, connection_state)
            )
            process_monitor_task = asyncio.create_task(
                self._monitor_process(mcp_process, connection_state)
            )
            
            # Wait for any task to complete
            done, pending = await asyncio.wait(
                [tcp_to_mcp_task, mcp_to_tcp_task, heartbeat_task, process_monitor_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel remaining tasks
            for task in pending:
                task.cancel()
            stderr_monitor_task.cancel()
            
            # Wait for cancellation
            await asyncio.gather(*pending, stderr_monitor_task, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Error handling client {addr}: {e}", exc_info=True)
        finally:
            logger.info(f"Client {addr} disconnected")
            connection_state['connected'] = False
            await mcp_process.close()
            writer.close()
            await writer.wait_closed()
    
    async def _tcp_to_mcp(self, reader: asyncio.StreamReader, mcp_process: MCPProcess, connection_state: dict) -> None:
        """Forward messages from TCP client to MCP process, handling heartbeats."""
        buffer = b""
        
        while connection_state['connected']:
            try:
                # Read data from TCP
                chunk = await reader.read(4096)
                if not chunk:
                    logger.info("TCP connection closed by client")
                    break
                
                buffer += chunk
                
                # Process complete messages
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    if line:
                        try:
                            message = json.loads(line.decode('utf-8'))
                            
                            # Handle heartbeat messages
                            if message.get('type') == 'heartbeat':
                                connection_state['last_heartbeat_received'] = time.time()
                                connection_state['client_supports_heartbeat'] = True
                                # Don't forward heartbeats to MCP server
                                continue
                            elif message.get('type') == 'handshake':
                                connection_state['client_supports_heartbeat'] = True
                                # Don't forward handshake to MCP server
                                continue
                                
                            logger.debug(f"TCP -> MCP: {message}")
                            
                            # Track request if it has an ID (for potential replay)
                            request_id = message.get('id')
                            if request_id:
                                connection_state['pending_requests'][request_id] = message
                                connection_state['last_request_id'] = request_id
                            
                            # Check if MCP process is alive before sending
                            if not mcp_process.is_alive():
                                logger.warning("MCP process is dead, waiting for monitor to restart...")
                                # Don't manually restart here, let the monitor handle it
                                # This prevents race conditions
                                await asyncio.sleep(0.5)
                                continue
                            
                            # Always forward messages - let MCP server handle initialization state
                            await mcp_process.send_message(message)
                            
                            # Mark as initialized if this was an initialize request
                            if message.get('method') == 'initialize':
                                connection_state['mcp_initialized'] = True
                            
                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid JSON from TCP client: {e}")
                        except Exception as e:
                            logger.error(f"Error forwarding to MCP: {e}")
                            
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"Error reading from TCP: {e}")
                break
    
    async def _mcp_to_tcp(self, mcp_process: MCPProcess, writer: asyncio.StreamWriter, connection_state: dict) -> None:
        """Forward messages from MCP process to TCP client."""
        while connection_state['connected']:
            try:
                message = await mcp_process.read_message()
                if message is None:
                    logger.info("MCP process closed - letting monitor handle restart")
                    # Don't restart here, let the monitor handle it
                    # Just wait briefly and check again
                    await asyncio.sleep(0.5)
                    continue
                
                logger.debug(f"MCP -> TCP: {message}")
                
                # Clear pending request if this is a response
                response_id = message.get('id')
                if response_id and response_id in connection_state.get('pending_requests', {}):
                    del connection_state['pending_requests'][response_id]
                    logger.debug(f"Cleared pending request {response_id}")
                
                # Send to TCP client
                message_str = json.dumps(message) + '\n'
                writer.write(message_str.encode('utf-8'))
                await writer.drain()
                
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"Error forwarding to TCP: {e}")
                # Check if the error is due to closed connection
                if writer.is_closing():
                    logger.info("TCP connection is closed")
                    break
                # Otherwise, might be MCP process issue - let monitor handle it
                if not mcp_process.is_alive():
                    logger.debug("MCP process not alive, waiting for monitor to restart")
                    await asyncio.sleep(0.5)
                    continue
                break
    
    async def _monitor_stderr(self, mcp_process: MCPProcess) -> None:
        """Monitor MCP process stderr for debugging."""
        while True:
            try:
                stderr_line = await mcp_process.read_stderr()
                if stderr_line:
                    logger.warning(f"MCP stderr: {stderr_line}")
                else:
                    await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error reading stderr: {e}")
                await asyncio.sleep(1)
    
    async def _heartbeat_loop(self, writer: asyncio.StreamWriter, mcp_process: MCPProcess, connection_state: dict) -> None:
        """Send periodic heartbeat messages to the client."""
        while connection_state['connected']:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                # Only send heartbeats if client supports them
                if connection_state['client_supports_heartbeat']:
                    heartbeat_msg = {
                        'type': 'heartbeat_response',
                        'timestamp': time.time(),
                        'mcp_alive': mcp_process.is_alive()
                    }
                    
                    message_str = json.dumps(heartbeat_msg) + '\n'
                    writer.write(message_str.encode('utf-8'))
                    await writer.drain()
                    
                    connection_state['last_heartbeat_sent'] = time.time()
                    
                    # Check if we've received a heartbeat recently
                    if time.time() - connection_state['last_heartbeat_received'] > self.heartbeat_timeout:
                        logger.warning("Client heartbeat timeout")
                        # Client might be disconnected, but let TCP detect it
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                if writer.is_closing():
                    break
    
    async def _initialize_mcp_session(self, mcp_process: MCPProcess, writer: asyncio.StreamWriter, connection_state: dict) -> None:
        """Initialize MCP session after process start/restart."""
        try:
            logger.info("Initializing MCP session...")
            
            # Send MCP initialization message
            init_msg = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "capabilities": {
                        "tools": True,
                        "resources": True,
                        "prompts": True
                    }
                },
                "id": "init-" + str(time.time())
            }
            
            await mcp_process.send_message(init_msg)
            logger.debug(f"Sent MCP initialize request: {init_msg}")
            
            # Wait for initialization response
            start_time = time.time()
            while time.time() - start_time < 10:  # 10 second timeout
                response = await mcp_process.read_message()
                if response:
                    logger.debug(f"MCP initialization response: {response}")
                    if response.get("id") == init_msg["id"]:
                        if "result" in response:
                            connection_state['mcp_initialized'] = True
                            logger.info("MCP session initialized successfully")
                            
                            # Send initialized notification
                            initialized_msg = {
                                "jsonrpc": "2.0",
                                "method": "initialized",
                                "params": {}
                            }
                            await mcp_process.send_message(initialized_msg)
                            logger.debug("Sent MCP initialized notification")
                            
                            # Forward the initialization response to the client
                            if writer and not writer.is_closing():
                                response_str = json.dumps(response) + '\n'
                                writer.write(response_str.encode('utf-8'))
                                await writer.drain()
                            
                            return
                        elif "error" in response:
                            logger.error(f"MCP initialization failed: {response['error']}")
                            return
                    else:
                        # Handle other messages during initialization
                        if writer and not writer.is_closing():
                            response_str = json.dumps(response) + '\n'
                            writer.write(response_str.encode('utf-8'))
                            await writer.drain()
                
                await asyncio.sleep(0.1)
            
            logger.error("MCP initialization timed out")
            
        except Exception as e:
            logger.error(f"Error initializing MCP session: {e}")
            connection_state['mcp_initialized'] = False
    
    async def _monitor_process(self, mcp_process: MCPProcess, connection_state: dict) -> None:
        """Monitor the MCP process health and restart if needed."""
        while connection_state['connected']:
            try:
                await asyncio.sleep(2)  # Check every 2 seconds for faster response
                
                if not mcp_process.is_alive() and mcp_process.auto_restart:
                    logger.info("MCP process terminated, restarting to maintain session...")
                    
                    # Store pending requests that might need to be replayed
                    pending_requests = connection_state.get('pending_requests', {}).copy()
                    
                    if await mcp_process.restart():
                        logger.info("MCP process restarted successfully")
                        
                        # Reset initialization state
                        connection_state['mcp_initialized'] = False
                        
                        # Wait a moment for the process to stabilize
                        await asyncio.sleep(0.5)
                        
                        # Check if we have a valid writer
                        writer = connection_state.get('writer')
                        if writer and not writer.is_closing():
                            # Send a notification to the client about the restart
                            restart_notification = {
                                "jsonrpc": "2.0",
                                "method": "$/mcp/serverRestarted",
                                "params": {
                                    "timestamp": time.time(),
                                    "reason": "process_terminated"
                                }
                            }
                            try:
                                notification_str = json.dumps(restart_notification) + '\n'
                                writer.write(notification_str.encode('utf-8'))
                                await writer.drain()
                                logger.info("Notified client of server restart")
                            except Exception as e:
                                logger.error(f"Failed to notify client of restart: {e}")
                            
                            # The client should reinitialize when it receives this notification
                            logger.info("Waiting for client to reinitialize MCP session...")
                        else:
                            logger.warning("No valid writer available for client notification")
                        
                        # Reset restart count on successful restart to be more forgiving
                        if mcp_process.restart_count > 0:
                            mcp_process.restart_count = max(0, mcp_process.restart_count - 1)
                        
                        # Clear old pending requests as they're likely stale after restart
                        if pending_requests:
                            logger.info(f"Clearing {len(pending_requests)} stale pending requests after restart")
                            connection_state['pending_requests'].clear()
                    else:
                        logger.error("Failed to restart MCP process")
                        # If we can't restart, terminate the connection
                        connection_state['connected'] = False
                        break
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in process monitor: {e}")
                await asyncio.sleep(2)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='TCP proxy for MCP servers')
    parser.add_argument('--host', default='0.0.0.0', 
                       help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8080, 
                       help='Port to bind to (default: 8080)')
    parser.add_argument('--heartbeat-interval', type=float, default=30.0,
                       help='Heartbeat interval in seconds (default: 30)')
    parser.add_argument('--auto-restart', action='store_true', default=True,
                       help='Enable automatic MCP process restart (default: enabled)')
    parser.add_argument('--no-auto-restart', dest='auto_restart', action='store_false',
                       help='Disable automatic MCP process restart')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    parser.add_argument('mcp_command', nargs='+',
                       help='Command to run the MCP server (e.g., python main.py)')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create bridge
    bridge = TCPToMCPBridge(args.mcp_command, heartbeat_interval=args.heartbeat_interval)
    
    # Start TCP server
    logger.info(f"Starting TCP proxy on {args.host}:{args.port}")
    logger.info(f"MCP command: {' '.join(args.mcp_command)}")
    logger.info(f"Heartbeat interval: {args.heartbeat_interval}s")
    logger.info(f"Auto-restart: {'enabled' if args.auto_restart else 'disabled'}")
    
    server = await asyncio.start_server(
        bridge.handle_client,
        args.host,
        args.port,
        limit=10 * 1024 * 1024  # 10MB limit for large messages
    )
    
    addr = server.sockets[0].getsockname()
    logger.info(f"TCP proxy listening on {addr[0]}:{addr[1]}")
    
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("TCP proxy stopped by user")