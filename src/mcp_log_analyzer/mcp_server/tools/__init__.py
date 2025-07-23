"""
MCP Tools module.

This module contains all the MCP tools organized by category.
"""

from .linux_test_tools import register_linux_test_tools
from .log_management_tools import register_log_management_tools
from .network_test_tools import register_network_test_tools
from .process_test_tools import register_process_test_tools
from .windows_test_tools import register_windows_test_tools
from .health_check_tools import register_health_check_tools


def register_all_tools(mcp):
    """Register all tools with the MCP server."""
    register_log_management_tools(mcp)
    register_windows_test_tools(mcp)
    register_linux_test_tools(mcp)
    register_process_test_tools(mcp)
    register_network_test_tools(mcp)
    register_health_check_tools(mcp)


__all__ = [
    "register_all_tools",
    "register_log_management_tools",
    "register_windows_test_tools",
    "register_linux_test_tools",
    "register_process_test_tools",
    "register_network_test_tools",
    "register_health_check_tools",
]
