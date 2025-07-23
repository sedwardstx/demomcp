# Getting Started with MCP Log Analyzer

This guide will help you get started with the MCP Log Analyzer server.

## Prerequisites

- Python 3.8 or higher
- Windows OS (for Windows Event Log functionality)
- pywin32 package

## Installation

1. Clone the repository:

```bash
git clone https://github.com/your-username/mcp-log-analyzer.git
cd mcp-log-analyzer
```

2. Install the package and dependencies:

```bash
pip install -e .  # Install the package in development mode
pip install -e ".[dev]"  # Install development dependencies (optional)
```

## Configuration

The MCP Log Analyzer can be configured using a YAML file or environment variables.

### Configuration File

The default configuration file is `config/default.yml`. You can create a custom configuration file and specify its path when running the server.

### Environment Variables

Configuration can also be provided using environment variables:

- `MCP_CONFIG`: Path to the configuration file
- `MCP_SERVER_HOST`: Server host
- `MCP_SERVER_PORT`: Server port
- `MCP_DEBUG`: Enable debug mode (`true` or `false`)

## Running the Server

To run the server with the default configuration:

```bash
python -m mcp_log_analyzer.api.server
```

To run the server with a custom configuration file:

```bash
python -m mcp_log_analyzer.api.server --config path/to/config.yml
```

To specify host and port directly:

```bash
python -m mcp_log_analyzer.api.server --host 0.0.0.0 --port 8000
```

To enable auto-reload during development:

```bash
python -m mcp_log_analyzer.api.server --reload
```

## Testing the Server

You can use the provided test script to test the server:

```bash
python scripts/test_server.py --url http://localhost:5000
```

The test script will register a Windows Event Log source, query logs, and analyze logs.

## Accessing the API

Once the server is running, you can access the API at `http://localhost:5000/api`.

The API documentation is available at [API Reference](api_reference.md).

## Using with Windows Event Logs

The MCP Log Analyzer can analyze Windows Event Logs using the Windows Event Log API. To register a Windows Event Log source:

```
POST /api/sources
```

```json
{
  "request_id": "e77e5d1e-8a7e-4e2f-9ea2-3b9ac5f5c161",
  "timestamp": "2023-05-02T12:00:00Z",
  "client_id": "test-client",
  "name": "System Event Log",
  "type": "event",
  "path": "System",
  "metadata": {
    "description": "Windows System Event Log"
  }
}
```

The `path` can be one of the standard Windows Event Log names:
- `Application`
- `System`
- `Security`
- Other event log names

## Example Workflow

1. Start the server:

```bash
python -m mcp_log_analyzer.api.server
```

2. Register a log source:

```bash
curl -X POST http://localhost:5000/api/sources \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "e77e5d1e-8a7e-4e2f-9ea2-3b9ac5f5c161",
    "timestamp": "2023-05-02T12:00:00Z",
    "client_id": "test-client",
    "name": "System Event Log",
    "type": "event",
    "path": "System",
    "metadata": {
      "description": "Windows System Event Log"
    }
  }'
```

3. Get the source ID from the response.

4. Query logs:

```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "f88e6d2e-9b8f-5f3g-0fb3-4c0bd6g6d272",
    "timestamp": "2023-05-02T12:01:00Z",
    "client_id": "test-client",
    "query": {
      "source_ids": ["source-id-from-previous-response"],
      "limit": 10,
      "offset": 0
    }
  }'
```

5. Analyze logs:

```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "g99f7e3f-0c9g-6g4h-1gc4-5d1ce7h7e383",
    "timestamp": "2023-05-02T12:02:00Z",
    "client_id": "test-client",
    "query": {
      "source_ids": ["source-id-from-previous-response"],
      "limit": 100,
      "offset": 0
    },
    "analysis_type": "summary",
    "parameters": {
      "include_statistics": true
    }
  }'
``` 