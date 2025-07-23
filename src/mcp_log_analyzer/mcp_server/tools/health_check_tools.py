"""
Health check and diagnostic tools for MCP server.
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any

from mcp.server import FastMCP


def register_health_check_tools(mcp: FastMCP):
    """Register health check tools with the MCP server."""
    
    # Server start time for uptime calculation
    server_start_time = time.time()
    
    @mcp.tool()
    async def debug_params(**kwargs) -> Dict[str, Any]:
        """
        Debug tool to see exactly what parameters are being passed.
        
        This tool accepts any parameters and returns them for inspection.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info("=== DEBUG_PARAMS TOOL CALLED ===")
        logger.info(f"Received kwargs: {kwargs}")
        logger.info(f"Kwargs type: {type(kwargs)}")
        logger.info(f"Kwargs keys: {list(kwargs.keys()) if kwargs else 'None'}")
        
        return {
            "received_kwargs": kwargs,
            "kwargs_type": str(type(kwargs)),
            "kwargs_keys": list(kwargs.keys()) if kwargs else [],
            "timestamp": datetime.now().isoformat()
        }
    
    @mcp.tool()
    async def server_diagnostics() -> Dict[str, Any]:
        """
        Get detailed server diagnostics including internal state.
        
        This tool provides deep insights into the server's current state
        and can help diagnose issues like parameter errors.
        """
        import inspect
        from ..server import mcp as server_mcp
        
        diagnostics = {
            "timestamp": datetime.now().isoformat(),
            "server_type": type(server_mcp).__name__,
            "server_info": {
                "name": getattr(server_mcp, 'name', 'unknown'),
                "version": getattr(server_mcp, 'version', 'unknown')
            },
            "request_stats": {},
            "registered_tools": [],
            "internal_state": {}
        }
        
        # Get request statistics if available
        if hasattr(server_mcp, '_request_count'):
            diagnostics["request_stats"] = {
                "total_requests": server_mcp._request_count,
                "total_errors": getattr(server_mcp, '_error_count', 0),
                "consecutive_param_errors": getattr(server_mcp, '_consecutive_param_errors', 0)
            }
        
        # List registered tools
        if hasattr(server_mcp, '_tools'):
            diagnostics["registered_tools"] = list(server_mcp._tools.keys())
        elif hasattr(server_mcp, 'tools'):
            diagnostics["registered_tools"] = list(server_mcp.tools.keys())
        
        # Check for common issues
        diagnostics["health_checks"] = {
            "has_tools": len(diagnostics["registered_tools"]) > 0,
            "server_responsive": True  # We're responding, so this is true
        }
        
        return diagnostics

    @mcp.tool()
    async def health_check() -> Dict[str, Any]:
        """
        Perform a health check on the MCP server.
        
        Returns server status, uptime, and basic diagnostic information.
        This can be used by clients to verify the server is responsive.
        """
        from ..server import log_sources, parsers
        
        current_time = time.time()
        uptime_seconds = current_time - server_start_time
        
        # Check ETL parser status
        etl_parser_info = {}
        if "etl" in parsers:
            parser = parsers["etl"]
            etl_parser_info = {
                "available": parser.is_available() if hasattr(parser, "is_available") else False,
                "type": type(parser).__name__
            }
            
            # Check for cached parser
            try:
                from mcp_log_analyzer.parsers.etl_cached_parser import EtlCachedParser
                EtlCachedParser._init_cache_dir()
                etl_parser_info["cache_dir"] = EtlCachedParser._cache_dir
                etl_parser_info["cached_files"] = len(EtlCachedParser._cache_registry)
            except:
                pass
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": uptime_seconds,
            "uptime_human": f"{uptime_seconds/3600:.1f} hours",
            "registered_sources": len(log_sources),
            "available_parsers": list(parsers.keys()),
            "etl_parser": etl_parser_info,
            "server_info": {
                "name": "mcp-log-analyzer",
                "version": "0.1.0"
            }
        }

    @mcp.tool()
    async def ping() -> Dict[str, Any]:
        """
        Simple ping endpoint for connection testing.
        
        Returns immediately with a timestamp. Useful for testing
        if the MCP connection is alive and responsive.
        """
        return {
            "pong": True,
            "timestamp": datetime.now().isoformat(),
            "server_time_ms": int(time.time() * 1000)
        }

    @mcp.tool()
    async def echo(message: str) -> Dict[str, Any]:
        """
        Echo back a message for connection testing.
        
        Args:
            message: The message to echo back
            
        Returns the message with a timestamp. Useful for testing
        round-trip communication with the server.
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Echo tool called with message: {message}")
        
        return {
            "echo": message,
            "timestamp": datetime.now().isoformat(),
            "received_at": time.time()
        }

    @mcp.tool()
    async def long_running_test(duration_seconds: int = 60) -> Dict[str, Any]:
        """
        Test long-running operations with periodic updates.
        
        Args:
            duration_seconds: How long to run the test (max 300 seconds)
            
        This simulates a long-running operation and can be used to test
        timeout handling and connection stability.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Cap duration at 5 minutes
        duration_seconds = min(duration_seconds, 300)
        
        start_time = time.time()
        logger.info(f"Starting long-running test for {duration_seconds} seconds")
        
        # Log progress every 10 seconds
        for i in range(0, duration_seconds, 10):
            await asyncio.sleep(10)
            elapsed = time.time() - start_time
            logger.info(f"Long-running test progress: {elapsed:.0f}/{duration_seconds} seconds")
        
        # Handle remaining time
        remaining = duration_seconds % 10
        if remaining > 0:
            await asyncio.sleep(remaining)
        
        total_elapsed = time.time() - start_time
        logger.info(f"Long-running test completed after {total_elapsed:.1f} seconds")
        
        return {
            "status": "completed",
            "requested_duration": duration_seconds,
            "actual_duration": total_elapsed,
            "timestamp": datetime.now().isoformat()
        }