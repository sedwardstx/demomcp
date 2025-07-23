"""
Prompts package for the MCP Log Analyzer server.
"""

from mcp.server import FastMCP

from .linux_testing_prompt import register_linux_testing_prompts
from .log_management_prompt import register_log_management_prompts
from .mcp_assets_overview_prompt import register_mcp_assets_prompt
from .network_testing_prompt import register_network_testing_prompts
from .process_monitoring_prompt import register_process_monitoring_prompts
from .windows_testing_prompt import register_windows_testing_prompts


def register_all_prompts(mcp: FastMCP):
    """Register all prompts with the MCP server."""
    register_mcp_assets_prompt(mcp)
    register_log_management_prompts(mcp)
    register_windows_testing_prompts(mcp)
    register_linux_testing_prompts(mcp)
    register_process_monitoring_prompts(mcp)
    register_network_testing_prompts(mcp)
