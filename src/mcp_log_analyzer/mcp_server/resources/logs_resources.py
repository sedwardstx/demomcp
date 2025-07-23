"""
Log-related MCP resources.
"""

from mcp.server import FastMCP


# This will be imported by the main server
def register_logs_resources(mcp: FastMCP):
    """Register all log-related resources with the MCP server."""

    @mcp.resource("logs://sources")
    async def get_log_sources_resource() -> str:
        """
        Get information about all registered log sources.

        This resource provides a comprehensive view of all log sources
        currently registered in the system.
        """
        from ..server import log_sources

        sources_info = []
        for name, source in log_sources.items():
            sources_info.append(f"- {name}: {source.type} at {source.path}")

        if not sources_info:
            return "No log sources registered."

        return "Registered Log Sources:\n" + "\n".join(sources_info)

    @mcp.resource("logs://types")
    async def get_supported_log_types() -> str:
        """
        Get information about supported log types.

        This resource lists all the log types that can be analyzed
        by the MCP Log Analyzer.
        """
        return """Supported Log Types:

1. Windows Event Logs (evt/evtx)
   - System, Application, Security logs
   - Custom Windows event logs
   
2. Structured Logs
   - JSON format
   - XML format
   
3. CSV Logs
   - Comma-separated values with headers
   
4. Unstructured Text Logs
   - Plain text logs with customizable parsing

Each log type has specific parsers optimized for that format."""

    @mcp.resource("logs://analysis-types")
    async def get_analysis_types() -> str:
        """
        Get information about available analysis types.

        This resource describes the different types of analysis
        that can be performed on logs.
        """
        return """Available Analysis Types:

1. Summary Analysis
   - Log count and time range
   - Event type distribution
   - Severity levels
   - Source statistics

2. Pattern Analysis
   - Common patterns detection
   - Frequency analysis
   - Recurring events
   - Pattern timeline

3. Anomaly Detection
   - Unusual event patterns
   - Spike detection
   - Rare events
   - Deviation from baseline"""
