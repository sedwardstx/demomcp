# MCP Log Analyzer - Quick Start Guide

**Version**: 1.0  
**Date**: July 16, 2025

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Local Usage (Single Machine)](#local-usage-single-machine)
4. [Network Usage (Multi-Machine)](#network-usage-multi-machine)
5. [AI Agent Client Integration](#ai-agent-client-integration)
6. [Security Considerations](#security-considerations)
7. [Production Deployment](#production-deployment)
8. [Troubleshooting](#troubleshooting)

## Overview

The MCP Log Analyzer Server provides comprehensive log analysis and system monitoring capabilities through the Model Context Protocol (MCP). It offers:

- **18 Tools** across 5 categories (log management, Windows, Linux, process monitoring, network diagnostics)
- **15+ Resources** for real-time system information
- **12 Prompts** for comprehensive user guidance
- **Cross-platform support** (Windows and Linux)
- **Multiple transport options** (stdio, TCP, HTTP, SSE)

## Installation

### Prerequisites

- **Python 3.12+**
- **Platform-specific dependencies**:
  - Windows: `pywin32>=300` for Event Log access
  - Linux: Standard system tools (journalctl, netstat, etc.)

### Install Package

```bash
# Navigate to project directory
cd /path/to/MCPsvr

# Install in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"

# On Windows, ensure pywin32 is properly installed
pip install pywin32>=300
python -c "import win32api"  # Test Windows API access
```

### Verify Installation

```bash
# Test server import
PYTHONPATH=src python3 -c "from mcp_log_analyzer.mcp_server.server import mcp; print('Server import successful')"

# Test server functionality
python check_server.py
```

## Local Usage (Single Machine)

### Standard MCP Mode (Recommended)

Use this mode for connecting with Claude Code or other MCP clients:

```bash
# Start MCP server (stdio mode)
python main.py

# Add to Claude Code
claude mcp add mcp-log-analyzer python main.py

# List MCP servers
claude mcp list

# Remove MCP server
claude mcp remove mcp-log-analyzer
```

**Important**: MCP servers don't show output when started - they communicate via stdin/stdout with MCP clients.

### TCP Mode (For Testing/Development)

```bash
# Start server in TCP mode for local testing
python main_tcp.py --tcp --host 127.0.0.1 --port 8080

# Start with verbose logging
python main_tcp.py --tcp --host 127.0.0.1 --port 8080 --verbose

# Start in stdio mode (default)
python main_tcp.py

# Add to Claude
claude mcp add remote-log-analyzer python3 /home/steve/git/MCPsvr/src/mcp_log_analyzer/tcp_proxy.py 192.168.2.202 8088
```

## Network Usage (Multi-Machine)

### Single Command for Network Access

```bash
# Start MCP server accessible across network
python main_tcp.py --tcp --host 0.0.0.0 --port 8080
```

### Multi-Machine Deployment

#### Windows Machines (Example: 5 servers)

```cmd
# Machine 1 (Windows Server 1)
cd C:\path\to\MCPsvr
python main_tcp.py --tcp --host 0.0.0.0 --port 8080

# Machine 2 (Windows Server 2)
cd C:\path\to\MCPsvr
python main_tcp.py --tcp --host 0.0.0.0 --port 8081

# Machine 3 (Windows Server 3)
cd C:\path\to\MCPsvr
python main_tcp.py --tcp --host 0.0.0.0 --port 8082

# Machine 4 (Windows Server 4)
cd C:\path\to\MCPsvr
python main_tcp.py --tcp --host 0.0.0.0 --port 8083

# Machine 5 (Windows Server 5)
cd C:\path\to\MCPsvr
python main_tcp.py --tcp --host 0.0.0.0 --port 8084
```

#### Linux Machines (Example: 5 servers)

```bash
# Machine 1 (Linux Server 1)
cd /path/to/MCPsvr
python main_tcp.py --tcp --host 0.0.0.0 --port 8080

# Machine 2 (Linux Server 2)
cd /path/to/MCPsvr
python main_tcp.py --tcp --host 0.0.0.0 --port 8081

# Machine 3 (Linux Server 3)
cd /path/to/MCPsvr
python main_tcp.py --tcp --host 0.0.0.0 --port 8082

# Machine 4 (Linux Server 4)
cd /path/to/MCPsvr
python main_tcp.py --tcp --host 0.0.0.0 --port 8083

# Machine 5 (Linux Server 5)
cd /path/to/MCPsvr
python main_tcp.py --tcp --host 0.0.0.0 --port 8084
```

### Command Line Options

```bash
python main_tcp.py [OPTIONS]

OPTIONS:
  --tcp                 Enable TCP server mode (default: stdio)
  --host HOST          Host to bind to (default: 0.0.0.0)
  --port PORT          Port to bind to (default: 8080)
  --verbose            Enable verbose logging
  --help               Show help message
```

## AI Agent Client Integration

### Connection Configuration

Your AI Agent client can connect to multiple servers simultaneously:

```python
# Example server configuration for AI Agent
servers = [
    # Windows machines
    {"host": "192.168.1.100", "port": 8080, "name": "Windows-Server-1"},
    {"host": "192.168.1.101", "port": 8081, "name": "Windows-Server-2"},
    {"host": "192.168.1.102", "port": 8082, "name": "Windows-Server-3"},
    {"host": "192.168.1.103", "port": 8083, "name": "Windows-Server-4"},
    {"host": "192.168.1.104", "port": 8084, "name": "Windows-Server-5"},
    
    # Linux machines
    {"host": "192.168.1.200", "port": 8080, "name": "Linux-Server-1"},
    {"host": "192.168.1.201", "port": 8081, "name": "Linux-Server-2"},
    {"host": "192.168.1.202", "port": 8082, "name": "Linux-Server-3"},
    {"host": "192.168.1.203", "port": 8083, "name": "Linux-Server-4"},
    {"host": "192.168.1.204", "port": 8084, "name": "Linux-Server-5"},
]
```

### Available Capabilities

Each server provides:

#### Tools (18 total)
- **Log Management**: register_log_source, list_log_sources, query_logs, analyze_logs
- **Windows System**: test_windows_event_log_access, get_windows_event_log_info, query_windows_events_by_criteria, get_windows_system_health
- **Linux System**: test_linux_log_access, query_systemd_journal, analyze_linux_services, get_linux_system_overview
- **Process Monitoring**: analyze_system_performance, find_resource_intensive_processes, monitor_process_health, get_system_health_summary
- **Network Diagnostics**: test_network_connectivity, test_port_connectivity, analyze_network_connections, diagnose_network_issues

#### Resources (15+)
- **Log Resources**: `logs/sources`, `logs/types`, `logs/analysis-types`
- **Windows Resources**: `windows/system-events/{param}`, `windows/application-events/{param}`
- **Linux Resources**: `linux/systemd-logs/{param}`, `linux/system-logs/{param}`
- **Process Resources**: `processes/list`, `processes/summary`
- **Network Resources**: `network/listening-ports`, `network/established-connections`, `network/all-connections`

#### Prompts (12 total)
- Comprehensive guides for log management, Windows diagnostics, Linux diagnostics, process monitoring, and network troubleshooting

## Security Considerations

### Network Security

```bash
# Bind to specific interface instead of 0.0.0.0 for security
python main_tcp.py --tcp --host 192.168.1.100 --port 8080

# Use non-default port
python main_tcp.py --tcp --host 0.0.0.0 --port 9999
```

### Firewall Configuration

#### Windows
```cmd
# Allow through Windows Firewall
netsh advfirewall firewall add rule name="MCP Log Analyzer" dir=in action=allow protocol=TCP localport=8080
```

#### Linux
```bash
# UFW (Ubuntu/Debian)
sudo ufw allow 8080/tcp

# iptables (CentOS/RHEL)
sudo iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
```

### Access Control

- **Read-only operations**: Server performs only read operations on system data
- **No system modification**: No capability to modify system configuration
- **Input validation**: Comprehensive Pydantic model validation
- **Error sanitization**: Safe error messages without sensitive data exposure

## Production Deployment

### Windows Service

```cmd
# Install as Windows service (requires additional setup)
sc create MCPLogAnalyzer binPath="python C:\path\to\MCPsvr\main_tcp.py --tcp --host 0.0.0.0 --port 8080"
sc start MCPLogAnalyzer
```

### Linux Systemd Service

```bash
# Create service file: /etc/systemd/system/mcp-log-analyzer.service
[Unit]
Description=MCP Log Analyzer Server
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/MCPsvr
ExecStart=/usr/bin/python3 main_tcp.py --tcp --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# Enable and start service
sudo systemctl enable mcp-log-analyzer
sudo systemctl start mcp-log-analyzer
sudo systemctl status mcp-log-analyzer
```

### Docker Deployment

```bash
# Build Docker image
docker build -t mcp-log-analyzer .

# Run container
docker run -d -p 8080:8080 --name mcp-log-analyzer mcp-log-analyzer

# Run with custom configuration
docker run -d -p 9999:8080 --name mcp-log-analyzer mcp-log-analyzer
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-log-analyzer
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-log-analyzer
  template:
    metadata:
      labels:
        app: mcp-log-analyzer
    spec:
      containers:
      - name: mcp-log-analyzer
        image: mcp-log-analyzer:latest
        ports:
        - containerPort: 8080
        command: ["python", "main_tcp.py", "--tcp", "--host", "0.0.0.0", "--port", "8080"]
        resources:
          limits:
            memory: "1Gi"
            cpu: "500m"
          requests:
            memory: "512Mi"
            cpu: "250m"
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-log-analyzer-service
spec:
  selector:
    app: mcp-log-analyzer
  ports:
  - port: 8080
    targetPort: 8080
  type: LoadBalancer
```

## Troubleshooting

### Common Issues

#### Server Not Starting
```bash
# Check Python version
python --version  # Should be 3.12+

# Test dependencies
pip install -e .

# Check server import
PYTHONPATH=src python3 -c "from mcp_log_analyzer.mcp_server.server import mcp; print('OK')"
```

#### Network Connection Issues
```bash
# Check if server is running
netstat -tuln | grep 8080

# Test connection
telnet your-server-ip 8080

# Check firewall
# Windows: Check Windows Firewall settings
# Linux: Check iptables/ufw rules
```

#### Windows Event Log Access
```bash
# Test Windows API access
python -c "import win32api; print('Windows API available')"

# Install pywin32 if missing
pip install pywin32>=300
```

#### Linux System Access
```bash
# Test systemd access
journalctl --version

# Test network tools
which netstat ss ping
```

### Debug Mode

```bash
# Start with verbose logging
python main_tcp.py --tcp --host 0.0.0.0 --port 8080 --verbose

# Check server functionality
python check_server.py

# Test specific tools
python -c "
from mcp_log_analyzer.mcp_server.server import mcp
# Test server capabilities
"
```

### Performance Monitoring

```bash
# Monitor server resource usage
htop  # Linux
taskmgr  # Windows

# Check network connections
netstat -an | grep 8080

# Monitor logs
tail -f /var/log/syslog  # Linux
# Check Event Viewer on Windows
```

## Development and Testing

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
```

### Build and Install

```bash
# Install the package in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"

# Build distribution
python -m build
```

## Support and Documentation

- **Architecture Documentation**: `/docs/planning/Agent/MCP_Server_Architecture.md`
- **Development Guide**: `/CLAUDE.md`
- **API Documentation**: Auto-generated from code
- **Issues**: Report issues via your project's issue tracker

## Quick Reference

| Command | Purpose |
|---------|---------|
| `python main.py` | Start stdio MCP server (standard mode) |
| `python main_tcp.py --tcp --host 0.0.0.0 --port 8080` | Start network-accessible TCP server |
| `python check_server.py` | Test server functionality |
| `claude mcp add mcp-log-analyzer python main.py` | Add to Claude Code |
| `PYTHONPATH=src python3 -m pytest tests/ -v` | Run tests |
| `black . && isort . && mypy src && flake8` | Code quality checks |

This guide provides everything you need to get started with the MCP Log Analyzer Server in both local and network configurations.