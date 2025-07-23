"""
MCP Log Analyzer Server using FastMCP framework.
"""

import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional
from uuid import UUID

from mcp.server import FastMCP

from mcp_log_analyzer.core.config import Settings
from mcp_log_analyzer.core.models import AnalysisResult, LogRecord, LogSource
from mcp_log_analyzer.parsers.base import BaseParser

# Initialize settings
settings = Settings()

# Initialize MCP server with custom error handler
import functools
import json

# Track request/response for debugging
request_response_log = []

# Custom error handler to log details
def log_mcp_errors(func):
    """Decorator to log MCP errors with full request details."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Function: {func.__name__}")
            logger.error(f"Args: {args}")
            logger.error(f"Kwargs: {kwargs}")
            raise
    return wrapper

# Tool wrapper to log all tool calls
def debug_tool(tool_func):
    """Wrapper to debug tool function calls."""
    @functools.wraps(tool_func)
    async def wrapper(*args, **kwargs):
        logger.info(f"Tool '{tool_func.__name__}' called")
        logger.info(f"  Args: {args}")
        logger.info(f"  Kwargs: {kwargs}")
        
        try:
            result = await tool_func(*args, **kwargs)
            logger.info(f"Tool '{tool_func.__name__}' returned successfully")
            return result
        except Exception as e:
            logger.error(f"Tool '{tool_func.__name__}' failed: {e}")
            logger.error(f"  Exception type: {type(e).__name__}")
            logger.error(f"  Exception args: {e.args}")
            raise
    
    return wrapper

# For now, we'll use the standard FastMCP and add logging via decorators
# The "Invalid request parameters" error is likely coming from the MCP protocol layer
# when tool arguments don't match expected signatures

# Initialize MCP server
mcp = FastMCP(
    name="mcp-log-analyzer",
    version="0.1.0",
    dependencies=["pandas>=1.3.0", "psutil>=5.9.0"],
)

# Storage with persistence
from mcp_log_analyzer.core.state_manager import get_state_manager

state_manager = get_state_manager()
_log_sources: Optional[Dict[str, LogSource]] = None  # Lazy loaded
parsers: Dict[str, BaseParser] = {}

# Log loaded sources
import logging
logger = logging.getLogger(__name__)

# Lazy loading wrapper for log sources
def get_log_sources() -> Dict[str, LogSource]:
    """Get log sources with lazy loading."""
    global _log_sources
    if _log_sources is None:
        logger.info("Lazy loading persisted log sources...")
        _log_sources = state_manager.load_log_sources()
        logger.info(f"Loaded {len(_log_sources)} persisted log sources")
    return _log_sources

# Create a proxy object that acts like a dict but lazy loads
class LazyLogSources:
    """Proxy for log sources dictionary with lazy loading."""
    
    def __getitem__(self, key):
        return get_log_sources()[key]
    
    def __setitem__(self, key, value):
        sources = get_log_sources()
        sources[key] = value
        # Also update the global reference
        global _log_sources
        _log_sources = sources
    
    def __delitem__(self, key):
        sources = get_log_sources()
        del sources[key]
        # Also update the global reference
        global _log_sources
        _log_sources = sources
    
    def __contains__(self, key):
        return key in get_log_sources()
    
    def __len__(self):
        return len(get_log_sources())
    
    def __iter__(self):
        return iter(get_log_sources())
    
    def values(self):
        return get_log_sources().values()
    
    def keys(self):
        return get_log_sources().keys()
    
    def items(self):
        return get_log_sources().items()
    
    def get(self, key, default=None):
        return get_log_sources().get(key, default)
    
    def clear(self):
        get_log_sources().clear()

# Use the lazy loader
log_sources = LazyLogSources()


# Add a mock parser for testing on non-Windows systems
class MockParser(BaseParser):
    """Mock parser for testing."""

    def parse_file(self, source: LogSource, file_path: Path) -> Iterator[LogRecord]:
        yield LogRecord(source_id=source.id, data={"test": "data"})

    def parse_content(self, source: LogSource, content: str) -> Iterator[LogRecord]:
        yield LogRecord(source_id=source.id, data={"test": "data"})

    def parse(self, path: str, **kwargs) -> List[LogRecord]:
        return [
            LogRecord(
                source_id=UUID("00000000-0000-0000-0000-000000000000"),
                data={"test": "data"},
            )
        ]

    def analyze(
        self, logs: List[LogRecord], analysis_type: str = "summary"
    ) -> AnalysisResult:
        return AnalysisResult(analysis_type=analysis_type, summary={"total": len(logs)})


# Only initialize Windows Event Log parser on Windows
import platform

if platform.system() == "Windows":
    try:
        from mcp_log_analyzer.parsers.evt_parser import EventLogParser

        parsers["evt"] = EventLogParser()
    except ImportError:
        # pywin32 not available, use mock parser
        parsers["evt"] = MockParser()
else:
    # Use mock parser on non-Windows systems
    parsers["evt"] = MockParser()

# Add real CSV parser and mock parsers for others
try:
    from mcp_log_analyzer.parsers.csv_parser import CsvLogParser

    parsers["csv"] = CsvLogParser()
except ImportError:
    parsers["csv"] = MockParser()

# Add ETL parser for Windows Event Trace Logs
try:
    from mcp_log_analyzer.parsers.etl_parser import EtlParser

    etl_parser = EtlParser()
    if etl_parser.is_available():
        parsers["etl"] = etl_parser
    else:
        parsers["etl"] = MockParser()
except ImportError:
    parsers["etl"] = MockParser()

# Add mock parsers for other types not yet implemented
parsers["json"] = MockParser()
parsers["xml"] = MockParser()
parsers["text"] = MockParser()

# Add alias for backward compatibility
# Allow "event" to map to "evt" for users who were using the old name
parser_aliases = {
    "event": "evt"  # Map old name to new name
}


# Utility Functions
def parse_time_param(time_str: str) -> Optional[datetime]:
    """Parse time parameter in various formats."""
    if not time_str or time_str == "none":
        return None

    # Try parsing as relative time (e.g., "30m", "1h", "2d")
    relative_pattern = r"^(\d+)([mhd])$"
    match = re.match(relative_pattern, time_str)
    if match:
        value, unit = match.groups()
        value = int(value)
        if unit == "m":
            return datetime.now() - timedelta(minutes=value)
        elif unit == "h":
            return datetime.now() - timedelta(hours=value)
        elif unit == "d":
            return datetime.now() - timedelta(days=value)

    # Try parsing as absolute datetime
    datetime_formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
    ]

    for fmt in datetime_formats:
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue

    raise ValueError(f"Cannot parse time: {time_str}")


# Prompts
@mcp.prompt()
async def log_analysis_quickstart() -> str:
    """
    A guide to get started with log analysis.

    This prompt provides step-by-step instructions for
    beginning log analysis with the MCP Log Analyzer.
    """
    return """Welcome to MCP Log Analyzer! Here's how to get started:

1. **Register a Log Source**
   First, register the log file or directory you want to analyze:
   - Use the `register_log_source` tool
   - Specify a unique name, source type, and path
   - Example: Register Windows System logs as "system-logs"

2. **Query Logs**
   Retrieve logs from your registered source:
   - Use the `query_logs` tool
   - Apply filters, time ranges, and pagination
   - Start with a small limit to preview the data

3. **Analyze Logs**
   Perform deeper analysis on your logs:
   - Use the `analyze_logs` tool
   - Choose from summary, pattern, or anomaly analysis
   - Review the results to gain insights

4. **Test System Resources**
   Use diagnostic tools to test system health:
   - `test_system_resources_access` - Check system monitoring capabilities
   - `test_windows_event_log_access` - Test Windows Event Log access
   - `test_linux_log_access` - Test Linux log file access
   - `test_network_tools_availability` - Check network diagnostic tools

5. **Explore Resources**
   Check available resources for more information:
   - logs://sources - View registered sources
   - logs://types - See supported log formats
   - logs://analysis-types - Learn about analysis options

Need help with a specific log type? Just ask!"""


@mcp.prompt()
async def troubleshooting_guide() -> str:
    """
    A guide for troubleshooting common log analysis issues.

    This prompt helps users resolve common problems when
    working with log files.
    """
    return """Log Analysis Troubleshooting Guide:

**Common Issues and Solutions:**

1. **"Access Denied" Errors**
   - Ensure you have read permissions for the log files
   - For Windows Event Logs, run with appropriate privileges
   - Check file paths are correct and accessible
   - Use `test_windows_event_log_access` or `test_linux_log_access` tools

2. **"Parser Not Found" Errors**
   - Verify the source_type matches supported types
   - Use logs://types resource to see available parsers
   - Ensure the log format matches the selected parser

3. **Empty Results**
   - Check your filters aren't too restrictive
   - Verify the time range includes log entries
   - Ensure the log file isn't empty or corrupted

4. **Performance Issues**
   - Use pagination (limit/offset) for large log files
   - Apply filters to reduce data volume
   - Consider analyzing smaller time ranges
   - Use `analyze_system_performance` tool to check system resources

5. **Network Issues**
   - Use `test_network_connectivity` to check internet access
   - Use `test_port_connectivity` to check specific ports
   - Use `diagnose_network_issues` for comprehensive network diagnosis

6. **System Health**
   - Use `get_system_health_summary` for overall system status
   - Use `monitor_process_health` to check specific processes
   - Use `find_resource_intensive_processes` to identify performance issues

Still having issues? Provide the error message and log source details for specific help."""


@mcp.prompt()
async def windows_event_log_guide() -> str:
    """
    A comprehensive guide for analyzing Windows Event Logs.

    This prompt provides detailed information about working
    with Windows Event Logs specifically.
    """
    return """Windows Event Log Analysis Guide:

**Getting Started with Windows Event Logs:**

1. **Common Log Types**
   - System: Hardware, drivers, system components
   - Application: Software events and errors
   - Security: Audit and security events
   - Setup: Installation and update logs

2. **Testing Access**
   Use `test_windows_event_log_access` tool to check if you can access Event Logs
   Use `get_windows_system_health` tool for a quick health overview

3. **Registering Event Logs**
   ```
   register_log_source(
     name="system-events",
     source_type="evt",
     path="System"  # Use log name, not file path
   )
   ```

4. **Diagnostic Tools**
   - `get_windows_event_log_info` - Get detailed info about specific logs
   - `query_windows_events_by_criteria` - Filter events by ID, level, or time
   - `get_windows_system_health` - Overall system health from Event Logs

5. **Useful Filters**
   - Event ID: Filter specific event types
   - Level: Error, Warning, Information
   - Source: Filter by event source
   - Time range: Focus on specific periods

6. **Common Event IDs**
   - 6005/6006: System startup/shutdown
   - 7001/7002: User logon/logoff
   - 41: Unexpected shutdown
   - 1074: System restart/shutdown reason

7. **Analysis Tips**
   - Start with summary analysis for overview
   - Use pattern analysis to find recurring issues
   - Apply anomaly detection for unusual events
   - Correlate events across different logs

**Example Workflow:**
1. Test access with `test_windows_event_log_access`
2. Get system health with `get_windows_system_health`
3. Register System and Application logs
4. Query recent errors and warnings with `query_windows_events_by_criteria`
5. Analyze patterns in error events

Need help with specific event IDs or analysis scenarios? Just ask!"""


from .prompts import register_all_prompts
from .resources import register_all_resources

# Register all tools, resources, and prompts
from .tools import register_all_tools

register_all_tools(mcp)
register_all_resources(mcp)
register_all_prompts(mcp)
