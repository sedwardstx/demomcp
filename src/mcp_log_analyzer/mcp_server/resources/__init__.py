"""
MCP Resources module.

This module contains all the MCP resources organized by category.
"""

from .linux_resources import register_linux_resources
from .logs_resources import register_logs_resources
from .network_resources import register_network_resources
from .process_resources import register_process_resources
from .windows_resources import register_windows_resources


def register_all_resources(mcp):
    """Register all resources with the MCP server."""
    register_logs_resources(mcp)
    register_windows_resources(mcp)
    register_linux_resources(mcp)
    register_process_resources(mcp)
    register_network_resources(mcp)


__all__ = [
    "register_all_resources",
    "register_logs_resources",
    "register_windows_resources",
    "register_linux_resources",
    "register_process_resources",
    "register_network_resources",
]
