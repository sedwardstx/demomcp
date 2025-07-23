#!/usr/bin/env python3
"""
TCP Proxy for MCP Server
========================

This script creates a local stdio-to-TCP proxy that allows Claude Code to connect
to remote MCP servers running on different machines.

Usage:
    python tcp_proxy.py <remote_host> <remote_port>
    
Example:
    python tcp_proxy.py 192.168.1.100 8088
    
Add to Claude Code:
    claude mcp add remote-mcp-server python /path/to/tcp_proxy.py 192.168.1.100 8088
"""

import socket
import sys
import threading
import logging
import argparse
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # Log to stderr to avoid interfering with stdio protocol
)
logger = logging.getLogger(__name__)


class MCPTCPProxy:
    """Proxy that bridges stdio MCP communication to a remote TCP server."""
    
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.running = False
        
    def connect(self) -> bool:
        """Connect to the remote MCP server."""
        try:
            logger.info(f"Connecting to MCP server at {self.host}:{self.port}")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            logger.info("Successfully connected to remote MCP server")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to {self.host}:{self.port}: {e}")
            return False
    
    def stdin_to_socket(self):
        """Forward stdin to the TCP socket."""
        try:
            while self.running:
                # Read from stdin (binary mode for proper handling)
                data = sys.stdin.buffer.read1(4096)
                if not data:
                    logger.info("stdin closed, stopping stdin->socket forwarding")
                    break
                
                # Send to socket
                self.socket.sendall(data)
                logger.debug(f"Forwarded {len(data)} bytes from stdin to socket")
                
        except Exception as e:
            logger.error(f"Error in stdin->socket forwarding: {e}")
        finally:
            self.running = False
    
    def socket_to_stdout(self):
        """Forward TCP socket data to stdout."""
        try:
            while self.running:
                # Receive from socket
                data = self.socket.recv(4096)
                if not data:
                    logger.info("Socket closed, stopping socket->stdout forwarding")
                    break
                
                # Write to stdout
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()
                logger.debug(f"Forwarded {len(data)} bytes from socket to stdout")
                
        except Exception as e:
            logger.error(f"Error in socket->stdout forwarding: {e}")
        finally:
            self.running = False
    
    def run(self):
        """Run the proxy."""
        if not self.connect():
            sys.exit(1)
        
        self.running = True
        
        # Create forwarding threads
        stdin_thread = threading.Thread(target=self.stdin_to_socket, daemon=True)
        socket_thread = threading.Thread(target=self.socket_to_stdout, daemon=True)
        
        # Start threads
        stdin_thread.start()
        socket_thread.start()
        
        try:
            # Wait for threads to complete
            stdin_thread.join()
            socket_thread.join()
        except KeyboardInterrupt:
            logger.info("Proxy interrupted by user")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
                logger.info("Socket closed")
            except Exception as e:
                logger.error(f"Error closing socket: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="TCP Proxy for connecting Claude Code to remote MCP servers",
        epilog="Example: python tcp_proxy.py 192.168.1.100 8088"
    )
    parser.add_argument(
        "host",
        help="Remote MCP server host (IP address or hostname)"
    )
    parser.add_argument(
        "port",
        type=int,
        help="Remote MCP server port"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and run proxy
    proxy = MCPTCPProxy(args.host, args.port)
    
    try:
        proxy.run()
    except Exception as e:
        logger.error(f"Proxy failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()