# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Build and Install
```bash
# Install the package in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"

# On Windows, ensure pywin32 is properly installed for Event Log access
# If you encounter issues, try:
pip install pywin32>=300
python -c "import win32api"  # Test Windows API access
```

### Code Quality
```bash
# Format code
black .
isort .

# Type checking
mypy src

# Linting
flake8

# Run all quality checks
black . && isort . && mypy src && flake8
```

### Testing
```bash
# Run all tests with proper PYTHONPATH
PYTHONPATH=src python3 -m pytest tests/ -v

# Run tests with coverage
PYTHONPATH=src python3 -m pytest --cov=mcp_log_analyzer tests/

# Run specific test file
PYTHONPATH=src python3 -m pytest tests/test_base_parser.py -v

# Test server import
PYTHONPATH=src python3 -c "from mcp_log_analyzer.mcp_server.server import mcp; print('Server import successful')"
```

### Running the MCP Server

**Important**: MCP servers don't show output when started - they communicate via stdin/stdout with MCP clients.

```bash
# Start the MCP server (runs silently)
python main.py

# Test the server is working
python check_server.py

# Add to Claude Code
claude mcp add mcp-log-analyzer python main.py

# List MCP servers
claude mcp list

# Remove MCP server
claude mcp remove mcp-log-analyzer
```

**No Output is Normal**: When you run `python main.py`, you won't see any console output. The server is running and waiting for MCP protocol messages from clients like Claude Code.

## Architecture Overview

### MCP Server Structure
This project follows the FastMCP framework pattern, refactored from the quick-data-mcp architecture:

- **Entry Point** (`main.py`): Simple script that imports and runs the MCP server
- **MCP Server** (`src/mcp_log_analyzer/mcp_server/server.py`): FastMCP server coordinator
- **Tools** (`src/mcp_log_analyzer/mcp_server/tools/`): Organized MCP tools by category
- **Resources** (`src/mcp_log_analyzer/mcp_server/resources/`): System monitoring resources
- **Prompts** (`src/mcp_log_analyzer/mcp_server/prompts/`): Comprehensive user guides
- **Core Logic** (`src/mcp_log_analyzer/core/`): Models and configuration
- **Parsers** (`src/mcp_log_analyzer/parsers/`): Log format-specific parsers

### Organized Tool Structure

**1. Core Log Management Tools** (`tools/log_management_tools.py`):
- `register_log_source`: Register new log sources (Windows Event Logs, JSON, XML, CSV, text)
- `list_log_sources`: List all registered log sources
- `get_log_source`: Get details about specific log source
- `delete_log_source`: Remove log source
- `query_logs`: Query logs with filters and time ranges
- `analyze_logs`: Perform pattern detection and anomaly analysis

**2. Windows System Tools** (`tools/windows_test_tools.py`):
- `test_windows_event_log_access`: Test Windows Event Log access and permissions
- `get_windows_event_log_info`: Get detailed Windows Event Log information
- `query_windows_events_by_criteria`: Query Windows Events with specific filters
- `get_windows_system_health`: Windows system health overview from Event Logs

**3. Linux System Tools** (`tools/linux_test_tools.py`):
- `test_linux_log_access`: Test Linux log file and systemd journal access
- `query_systemd_journal`: Query systemd journal with specific criteria
- `analyze_linux_services`: Analyze Linux services status and recent activity
- `get_linux_system_overview`: Comprehensive Linux system overview

**4. Process Monitoring Tools** (`tools/process_test_tools.py`):
- `test_system_resources_access`: Test system resource monitoring capabilities
- `analyze_system_performance`: Analyze current system performance and resource usage
- `find_resource_intensive_processes`: Find processes consuming significant resources
- `monitor_process_health`: Monitor health and status of specific processes
- `get_system_health_summary`: Overall system health summary

**5. Network Diagnostic Tools** (`tools/network_test_tools.py`):
- `test_network_tools_availability`: Test availability of network diagnostic tools
- `test_port_connectivity`: Test connectivity to specific ports
- `test_network_connectivity`: Test network connectivity to various hosts
- `analyze_network_connections`: Analyze current network connections and listening ports
- `diagnose_network_issues`: Comprehensive network diagnostics

### Organized Resource Structure

**1. Log Management Resources** (`resources/logs_resources.py`):
- `logs/sources`: List of registered log sources
- `logs/source/{name}`: Details about specific log source

**2. Windows Resources** (`resources/windows_resources.py`):
- `windows/system-events/{param}`: Windows System Event logs with configurable parameters
- `windows/application-events/{param}`: Windows Application Event logs with configurable parameters

**3. Linux Resources** (`resources/linux_resources.py`):
- `linux/systemd-logs/{param}`: Linux systemd journal logs with configurable parameters
- `linux/system-logs/{param}`: Linux system logs with configurable parameters

**4. Process Resources** (`resources/process_resources.py`):
- `processes/list`: Current running processes with PID, CPU, and memory usage
- `processes/summary`: Process summary statistics

**5. Network Resources** (`resources/network_resources.py`):
- `network/listening-ports`: Currently listening network ports
- `network/established-connections`: Active network connections
- `network/all-connections`: All network connections and statistics
- `network/statistics`: Network interface statistics
- `network/routing-table`: Network routing table
- `network/port/{port}`: Specific port information

### Resource Parameters
System monitoring resources support flexible parameters:
- `/last/{n}` - Get last N entries (e.g., `/last/50`)
- `/time/{duration}` - Get entries from time duration (e.g., `/time/30m`, `/time/2h`, `/time/1d`)
- `/range/{start}/{end}` - Get entries from time range (e.g., `/range/2025-01-07 13:00/2025-01-07 14:00`)

**Time Format Support**:
- Relative: `30m`, `2h`, `1d`
- Absolute: `2025-01-07 13:00`, `07/01/2025 13:30`

### Comprehensive Prompt System

**1. MCP Assets Overview** (`prompts/mcp_assets_overview_prompt.py`):
- Complete reference to all 18 tools, 10+ resources, and usage examples
- Platform support information and getting started guide

**2. Log Management Prompts** (`prompts/log_management_prompt.py`):
- `log_management_guide`: Comprehensive log management and analysis guide
- `log_troubleshooting_guide`: Troubleshooting common log analysis issues

**3. Windows Testing Prompts** (`prompts/windows_testing_prompt.py`):
- `windows_diagnostics_guide`: Windows system diagnostics and Event Log analysis
- `windows_event_reference`: Quick reference for Windows Event IDs and meanings

**4. Linux Testing Prompts** (`prompts/linux_testing_prompt.py`):
- `linux_diagnostics_guide`: Linux system diagnostics and systemd troubleshooting
- `linux_systemd_reference`: systemd services and log patterns reference

**5. Process Monitoring Prompts** (`prompts/process_monitoring_prompt.py`):
- `process_monitoring_guide`: System resource monitoring and performance analysis
- `process_troubleshooting_guide`: Troubleshooting process and performance issues

**6. Network Testing Prompts** (`prompts/network_testing_prompt.py`):
- `network_diagnostics_guide`: Network diagnostics and troubleshooting
- `network_troubleshooting_scenarios`: Specific network troubleshooting scenarios

### Cross-Platform Support

**Windows Features**:
- Full Windows Event Log support with pywin32
- System and Application Event Log analysis
- **Custom Application and Services logs support** (e.g., "Microsoft-Service Fabric/Admin")
- Event ID reference and health assessment  
- Configurable time-based filtering
- Automatic API selection (legacy for standard logs, EvtQuery for custom logs)

**Linux Features**:
- systemd journal and traditional log file support
- Service status analysis and troubleshooting
- Cross-distribution compatibility
- Network diagnostic tool integration

**Cross-Platform Features**:
- Process monitoring with psutil
- Network diagnostics with platform-specific tools
- Core log management for various formats
- Comprehensive error handling and permission checking

### Adding New Features

**Adding New Tools**:
1. Choose appropriate category folder under `tools/`
2. Create Pydantic models for requests in the tool file
3. Add async function decorated with `@mcp.tool()`
4. Update the category's `register_*_tools()` function
5. Add comprehensive docstring and error handling

**Adding New Resources**:
1. Choose appropriate category folder under `resources/`
2. Add async function decorated with `@mcp.resource()`
3. Implement parameterization if needed
4. Update the category's `register_*_resources()` function
5. Add to the main assets overview prompt

**Adding New Prompts**:
1. Choose appropriate category folder under `prompts/`
2. Add async function decorated with `@mcp.prompt()`
3. Follow the established format with emojis and markdown
4. Update the category's `register_*_prompts()` function
5. Include practical examples and troubleshooting guidance

### Design Patterns

- **Modular Organization**: Tools, resources, and prompts organized by functional category
- **Async-First**: All MCP functions are async for better performance
- **Type Safety**: Pydantic models for all requests/responses with comprehensive validation
- **Error Handling**: Consistent error format with helpful messages
- **Cross-Platform**: Platform detection and appropriate tool/command selection
- **Parameterized Resources**: Flexible resource access with time-based and count-based parameters
- **Comprehensive Documentation**: Rich prompts with step-by-step guidance and troubleshooting

### Dependencies

**Core Requirements**:
- `mcp[cli]>=1.9.2`: Model Context Protocol framework
- `pydantic>=1.8.0`: Data validation and serialization
- `python-dotenv>=0.19.0`: Environment variable management
- `pandas>=1.3.0`: Data analysis capabilities
- `psutil>=5.9.0`: System and process monitoring

**Platform-Specific**:
- `pywin32>=300`: Windows Event Log access (Windows only)

**Development**:
- `pytest`: Testing framework
- `black`: Code formatting
- `isort`: Import sorting
- `mypy`: Type checking
- `flake8`: Linting

### Testing Notes

- Tests require `PYTHONPATH=src` to properly import modules
- Some tests are platform-specific (Windows Event Logs, Linux systemd)
- Network tests may require internet connectivity
- Process monitoring tests interact with real system resources

### MCP Integration Notes

- Server communicates via stdio with Claude Code
- Tools appear as callable functions in Claude conversations
- Resources can be referenced with URIs like `logs/sources` or `processes/list`
- Prompts provide comprehensive guidance for effective system administration
- Cross-platform compatibility ensures consistent experience across environments