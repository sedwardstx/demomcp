"""
MCP Assets Overview prompt for the MCP Log Analyzer server.
"""

from mcp.server import FastMCP


def register_mcp_assets_prompt(mcp: FastMCP):
    """Register the MCP assets overview prompt."""

    @mcp.prompt()
    async def mcp_assets_overview() -> str:
        """
        Comprehensive overview of MCP Log Analyzer server capabilities.

        This prompt provides a complete reference guide to all available
        tools, resources, and prompts in the MCP Log Analyzer system.
        """
        return """
# 🔧 MCP Log Analyzer - Complete Assets Overview

## 📊 **Core Log Management Tools**
- `register_log_source` - Register new log sources (Windows Event Logs, JSON, XML, CSV, text)
- `list_log_sources` - List all registered log sources
- `get_log_source` - Get details about a specific log source
- `delete_log_source` - Remove a registered log source
- `query_logs` - Query and filter logs from registered sources
- `analyze_logs` - Analyze logs with pattern detection and anomaly analysis

## 🪟 **Windows System Tools**
- `test_windows_event_log_access` - Test Windows Event Log access and permissions
- `get_windows_event_log_info` - Get detailed information about Windows Event Logs
- `query_windows_events_by_criteria` - Query Windows Event Logs with specific filters
- `get_windows_system_health` - Get Windows system health overview from Event Logs

## 🐧 **Linux System Tools**
- `test_linux_log_access` - Test Linux log file and systemd journal access
- `query_systemd_journal` - Query systemd journal with specific criteria
- `analyze_linux_services` - Analyze Linux services status and recent activity
- `get_linux_system_overview` - Get comprehensive Linux system overview

## 🖥️ **Process Monitoring Tools**
- `test_system_resources_access` - Test system resource monitoring capabilities
- `analyze_system_performance` - Analyze current system performance and resource usage
- `find_resource_intensive_processes` - Find processes consuming significant resources
- `monitor_process_health` - Monitor health and status of specific processes
- `get_system_health_summary` - Get overall system health summary

## 🌐 **Network Diagnostic Tools**
- `test_network_tools_availability` - Test availability of network diagnostic tools
- `test_port_connectivity` - Test connectivity to specific ports
- `test_network_connectivity` - Test network connectivity to various hosts
- `analyze_network_connections` - Analyze current network connections and listening ports
- `diagnose_network_issues` - Perform comprehensive network diagnostics

## 📋 **System Resources**

### Windows Resources
- `windows/system-events/{param}` - Windows System Event logs with configurable parameters
- `windows/application-events/{param}` - Windows Application Event logs with configurable parameters

### Linux Resources
- `linux/systemd-logs/{param}` - Linux systemd journal logs with configurable parameters
- `linux/system-logs/{param}` - Linux system logs with configurable parameters

### Process Resources
- `processes/list` - Current running processes with PID, CPU, and memory usage
- `processes/summary` - Process summary statistics

### Network Resources
- `network/listening-ports` - Currently listening network ports
- `network/established-connections` - Active network connections
- `network/all-connections` - All network connections and statistics
- `network/statistics` - Network interface statistics
- `network/routing-table` - Network routing table
- `network/port/{port}` - Specific port information

### Log Management Resources
- `logs/sources` - List of registered log sources
- `logs/source/{name}` - Details about a specific log source

## 🎯 **Resource Parameters**

Many resources support flexible parameters:
- `/last/{n}` - Get last N entries (e.g., `/last/50`)
- `/time/{duration}` - Get entries from time duration (e.g., `/time/30m`, `/time/2h`, `/time/1d`)
- `/range/{start}/{end}` - Get entries from time range (e.g., `/range/2025-01-07 13:00/2025-01-07 14:00`)

## 💡 **Usage Examples**

### Windows System Analysis
```
1. Test Windows Event Log access
2. Get Windows system health overview
3. Query specific Event IDs or error levels
4. Access Windows System Events: windows/system-events/last/100
```

### Linux System Analysis
```
1. Test Linux log access capabilities
2. Query systemd journal for specific services
3. Analyze failed services and their logs
4. Access systemd logs: linux/systemd-logs/time/1h
```

### Process Monitoring
```
1. Test system resource access
2. Find resource-intensive processes
3. Monitor specific process health
4. Access process list: processes/list
```

### Network Troubleshooting
```
1. Test network tools availability
2. Diagnose network connectivity issues
3. Analyze listening ports and connections
4. Access listening ports: network/listening-ports
```

### Log Management
```
1. Register various log sources (Event Logs, JSON, CSV, etc.)
2. Query and filter logs with time ranges
3. Analyze patterns and detect anomalies
4. Access log sources: logs/sources
```

## 🚀 **Getting Started**

1. **System Health Check**: Use system-specific health tools
2. **Resource Monitoring**: Check processes and network status
3. **Log Analysis**: Register log sources and analyze patterns
4. **Troubleshooting**: Use diagnostic tools for specific issues

## 🔍 **Platform Support**

- **Windows**: Full Event Log support with pywin32
- **Linux**: systemd journal and traditional log file support
- **Cross-platform**: Process monitoring, network diagnostics, log management

All tools include comprehensive error handling and permission checking for secure operation across different environments.
"""
