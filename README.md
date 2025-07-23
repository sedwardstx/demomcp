# MCP Log Analyzer

A Model Context Protocol (MCP) server for analyzing different types of logs on Windows systems, built with the FastMCP framework.

## Features

- **Multiple Log Format Support**
  - Windows Event Logs (EVT/EVTX)
  - Windows Event Trace Logs (ETL)
  - Structured Logs (JSON, XML)
  - CSV Logs
  - Unstructured Text Logs

- **MCP Tools**
  - `register_log_source`: Register new log sources
  - `list_log_sources`: View all registered sources
  - `get_log_source`: Get details about a specific source
  - `delete_log_source`: Remove a log source
  - `query_logs`: Query logs with filters and pagination
  - `analyze_logs`: Perform analysis (summary, pattern, anomaly)

- **MCP Resources**
  - `logs://sources`: View registered log sources
  - `logs://types`: Learn about supported log types
  - `logs://analysis-types`: Understand analysis options
  - `system://windows-event-logs`: Recent Windows System and Application event logs
  - `system://linux-logs`: Linux systemd journal and application logs
  - `system://process-list`: Current processes with PID, CPU, and memory usage
  - `system://netstat`: Network connections and statistics for troubleshooting

- **MCP Prompts**
  - Log analysis quickstart guide
  - Troubleshooting guide
  - Windows Event Log specific guide

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/mcp-log-analyzer.git
cd mcp-log-analyzer

# Install the package
pip install -e .

# For ETL file support (optional)
pip install -e ".[etl]"

# For development dependencies
pip install -e ".[dev]"
```

### Windows Setup

On Windows, the package includes Windows Event Log support via `pywin32`. If you encounter import errors:

```powershell
# Ensure Windows dependencies are installed
pip install pywin32>=300

# Test the setup
python test_windows_setup.py

# If successful, start the server
python main.py
```

**Note**: On first install of `pywin32`, you may need to run the post-install script:
```powershell
python Scripts/pywin32_postinstall.py -install
```

## Usage

### Understanding MCP Servers

MCP (Model Context Protocol) servers don't have traditional web endpoints. They communicate via stdin/stdout with MCP clients (like Claude Code). When you run `python main.py`, the server starts silently and waits for MCP protocol messages.

### Testing the Server

```bash
# Test that the server is working
python check_server.py

# See usage instructions
python check_server.py --usage
```

### Starting the MCP Server

```bash
# Run directly
python main.py

# Or use Claude Code's MCP integration
claude mcp add mcp-log-analyzer python main.py
```

### Using with Claude Code

1. **Add the server to Claude Code:**
   ```bash
   claude mcp add mcp-log-analyzer python /path/to/main.py
   ```

2. **Use the tools in Claude Code:**
   - Register a log source: Use the `register_log_source` tool
   - Query logs: Use the `query_logs` tool
   - Analyze logs: Use the `analyze_logs` tool

3. **Access resources:**
   - Reference resources using `@mcp-log-analyzer:logs://sources`
   - Get help with prompts like `/mcp__mcp-log-analyzer__log_analysis_quickstart`

## System Monitoring Resources

These resources provide real-time system information without needing to register log sources:

1. **Check System Processes:**
   - Access via `@mcp-log-analyzer:system://process-list`
   - Shows top processes by CPU usage with memory information

2. **Windows Event Logs** (Windows only):
   - Default: `@mcp-log-analyzer:system://windows-event-logs` (last 10 entries)
   - By count: `@mcp-log-analyzer:system://windows-event-logs/last/50` (last 50 entries)
   - By time: `@mcp-log-analyzer:system://windows-event-logs/time/30m` (last 30 minutes)
   - By range: `@mcp-log-analyzer:system://windows-event-logs/range/2025-01-07 13:00/2025-01-07 14:00`
   - Shows System and Application event log entries

3. **Linux System Logs** (Linux only):
   - Default: `@mcp-log-analyzer:system://linux-logs` (last 50 lines)
   - By count: `@mcp-log-analyzer:system://linux-logs/last/100` (last 100 lines)
   - By time: `@mcp-log-analyzer:system://linux-logs/time/1h` (last hour)
   - By range: `@mcp-log-analyzer:system://linux-logs/range/2025-01-07 13:00/2025-01-07 14:00`
   - Shows systemd journal, syslog, and common application logs

4. **Network Monitoring** (Cross-platform):
   - Default: `@mcp-log-analyzer:system://netstat` (listening ports)
   - Listening ports: `@mcp-log-analyzer:system://netstat/listening`
   - Established connections: `@mcp-log-analyzer:system://netstat/established`
   - All connections: `@mcp-log-analyzer:system://netstat/all`
   - Network statistics: `@mcp-log-analyzer:system://netstat/stats`
   - Routing table: `@mcp-log-analyzer:system://netstat/routing`
   - Port-specific: `@mcp-log-analyzer:system://netstat/port/80`
   - Uses netstat on Windows, ss (preferred) or netstat on Linux

### Time Format Examples:
- **Relative time**: `30m` (30 minutes), `2h` (2 hours), `1d` (1 day)
- **Absolute time**: `2025-01-07 13:00`, `2025-01-07 13:30:15`, `07/01/2025 13:00`

## Example Workflow

1. **Register a Windows System Log:**
   ```
   Use register_log_source tool with:
   - name: "system-logs"
   - source_type: "evt"
   - path: "System"
   ```

2. **Query Recent Errors:**
   ```
   Use query_logs tool with:
   - source_name: "system-logs"
   - filters: {"level": "Error"}
   - limit: 10
   ```

3. **Analyze Patterns:**
   ```
   Use analyze_logs tool with:
   - source_name: "system-logs"
   - analysis_type: "pattern"
   ```

4. **Register an ETL File:**
   ```
   Use register_log_source tool with:
   - name: "network-trace"
   - source_type: "etl"
   - path: "C:\\Traces\\network.etl"
   ```

## Development

```bash
# Run tests
pytest

# Code formatting
black .
isort .

# Type checking
mypy src

# Run all quality checks
black . && isort . && mypy src && flake8
```

## Project Structure

- `src/mcp_log_analyzer/`: Main package
  - `mcp_server/`: MCP server implementation using FastMCP
  - `core/`: Core functionality and models
  - `parsers/`: Log parsers for different formats
- `main.py`: Server entry point
- `.mcp.json`: MCP configuration
- `tests/`: Test files

## Requirements

- Python 3.12+
- Windows OS (for Event Log support)
- See `pyproject.toml` for full dependencies

## License

MIT