"""Tests for the MCP server."""

import platform

import pytest
from mcp.server import FastMCP

from mcp_log_analyzer.mcp_server.server import (
    log_sources,
    mcp,
)
from mcp_log_analyzer.mcp_server.test_tool_utils import (
    AnalyzeLogsRequest,
    QueryLogsRequest,
    RegisterLogSourceRequest,
    analyze_logs,
    delete_log_source,
    get_log_source,
    list_log_sources,
    query_logs,
    register_log_source,
)


@pytest.mark.asyncio
async def test_server_initialization():
    """Test that the MCP server is properly initialized."""
    assert isinstance(mcp, FastMCP)
    # FastMCP stores name differently
    assert hasattr(mcp, "tool")
    assert hasattr(mcp, "resource")
    assert hasattr(mcp, "prompt")


@pytest.mark.asyncio
async def test_register_log_source():
    """Test registering a log source."""
    # Clear any existing sources
    log_sources.clear()

    request = RegisterLogSourceRequest(
        name="test-source", source_type="json", path="/tmp/test.json"
    )

    result = await register_log_source(request)

    assert "message" in result
    assert "test-source" in result["message"]
    assert "test-source" in log_sources
    assert log_sources["test-source"].type == "json"


@pytest.mark.asyncio
async def test_list_log_sources():
    """Test listing log sources."""
    # Clear and add a test source
    log_sources.clear()

    request = RegisterLogSourceRequest(
        name="test-source", source_type="json", path="/tmp/test.json"
    )
    await register_log_source(request)

    result = await list_log_sources()

    assert "sources" in result
    assert "count" in result
    assert result["count"] == 1
    assert len(result["sources"]) == 1
    assert result["sources"][0]["name"] == "test-source"


@pytest.mark.asyncio
async def test_get_log_source():
    """Test getting a specific log source."""
    # Clear and add a test source
    log_sources.clear()

    request = RegisterLogSourceRequest(
        name="test-source", source_type="json", path="/tmp/test.json"
    )
    await register_log_source(request)

    result = await get_log_source("test-source")

    assert "source" in result
    assert result["source"]["name"] == "test-source"

    # Test non-existent source
    result = await get_log_source("non-existent")
    assert "error" in result


@pytest.mark.asyncio
async def test_delete_log_source():
    """Test deleting a log source."""
    # Clear and add a test source
    log_sources.clear()

    request = RegisterLogSourceRequest(
        name="test-source", source_type="json", path="/tmp/test.json"
    )
    await register_log_source(request)

    result = await delete_log_source("test-source")

    assert "message" in result
    assert "test-source" not in log_sources

    # Test deleting non-existent source
    result = await delete_log_source("non-existent")
    assert "error" in result


@pytest.mark.asyncio
async def test_query_logs():
    """Test querying logs."""
    # Clear and add a test source
    log_sources.clear()

    request = RegisterLogSourceRequest(
        name="test-source", source_type="json", path="/tmp/test.json"
    )
    await register_log_source(request)

    query_request = QueryLogsRequest(source_name="test-source", limit=10)

    result = await query_logs(query_request)

    assert "logs" in result
    assert "count" in result
    assert "source" in result
    assert result["source"] == "test-source"


@pytest.mark.asyncio
async def test_analyze_logs():
    """Test analyzing logs."""
    # Clear and add a test source
    log_sources.clear()

    request = RegisterLogSourceRequest(
        name="test-source", source_type="json", path="/tmp/test.json"
    )
    await register_log_source(request)

    analyze_request = AnalyzeLogsRequest(
        source_name="test-source", analysis_type="summary"
    )

    result = await analyze_logs(analyze_request)

    assert "result" in result
    assert "source" in result
    assert "analysis_type" in result
    assert result["analysis_type"] == "summary"


@pytest.mark.asyncio
async def test_system_resources():
    """Test system monitoring resources."""
    # Import the resource functions
    from mcp_log_analyzer.mcp_server.server import parse_time_param
    from mcp_log_analyzer.mcp_server.test_utils import (
        get_linux_logs_by_time,
        get_linux_logs_with_count,
        get_linux_system_logs,
        get_process_list,
        get_windows_event_logs,
        get_windows_event_logs_by_time,
        get_windows_event_logs_with_count,
    )

    # Test process list resource (should work on all platforms)
    process_list = await get_process_list()
    assert isinstance(process_list, str)
    assert "Process List" in process_list
    assert "PID" in process_list
    assert "CPU%" in process_list
    assert "Memory%" in process_list

    # Test Windows event logs (platform-specific)
    windows_logs = await get_windows_event_logs()
    assert isinstance(windows_logs, str)
    if platform.system() == "Windows":
        assert "Windows Event Logs" in windows_logs
    else:
        assert "only available on Windows" in windows_logs

    # Test parameterized Windows event logs
    windows_logs_count = await get_windows_event_logs_with_count("5")
    assert isinstance(windows_logs_count, str)
    if platform.system() == "Windows":
        assert "Last 5 entries" in windows_logs_count
    else:
        assert "only available on Windows" in windows_logs_count

    windows_logs_time = await get_windows_event_logs_by_time("30m")
    assert isinstance(windows_logs_time, str)
    if platform.system() == "Windows":
        assert "Windows Event Logs" in windows_logs_time
    else:
        assert "only available on Windows" in windows_logs_time

    # Test Linux system logs (platform-specific)
    linux_logs = await get_linux_system_logs()
    assert isinstance(linux_logs, str)
    if platform.system() == "Linux":
        assert "Linux System Logs" in linux_logs
    else:
        assert "only available on Linux" in linux_logs

    # Test parameterized Linux logs
    linux_logs_count = await get_linux_logs_with_count("20")
    assert isinstance(linux_logs_count, str)
    if platform.system() == "Linux":
        assert "Last 20 lines" in linux_logs_count
    else:
        assert "only available on Linux" in linux_logs_count

    linux_logs_time = await get_linux_logs_by_time("1h")
    assert isinstance(linux_logs_time, str)
    if platform.system() == "Linux":
        assert "Linux System Logs" in linux_logs_time
    else:
        assert "only available on Linux" in linux_logs_time


@pytest.mark.asyncio
async def test_time_parsing():
    """Test time parameter parsing function."""
    from datetime import datetime, timedelta

    from mcp_log_analyzer.mcp_server.server import parse_time_param

    # Test relative time parsing
    result = parse_time_param("30m")
    assert result is not None
    assert isinstance(result, datetime)
    assert result < datetime.now()

    result = parse_time_param("2h")
    assert result is not None
    assert isinstance(result, datetime)

    result = parse_time_param("1d")
    assert result is not None
    assert isinstance(result, datetime)

    # Test absolute time parsing
    result = parse_time_param("2025-01-07 13:00")
    assert result is not None
    assert isinstance(result, datetime)
    assert result.year == 2025
    assert result.month == 1
    assert result.day == 7
    assert result.hour == 13

    # Test invalid formats
    try:
        parse_time_param("invalid")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    # Test none case
    result = parse_time_param("none")
    assert result is None


@pytest.mark.asyncio
async def test_netstat_resources():
    """Test netstat network monitoring resources."""
    # Import the netstat resource functions
    from mcp_log_analyzer.mcp_server.test_utils import (
        get_netstat,
        get_netstat_all,
        get_netstat_established,
        get_netstat_listening,
        get_netstat_port,
        get_netstat_routing,
        get_netstat_stats,
    )

    # Test default netstat resource
    netstat_output = await get_netstat()
    assert isinstance(netstat_output, str)
    assert "Listening Ports" in netstat_output

    # Test listening ports resource
    listening_output = await get_netstat_listening()
    assert isinstance(listening_output, str)
    assert "Listening Ports" in listening_output

    # Test established connections resource
    established_output = await get_netstat_established()
    assert isinstance(established_output, str)
    assert "Established Connections" in established_output

    # Test all connections resource
    all_output = await get_netstat_all()
    assert isinstance(all_output, str)
    assert "All Network Connections" in all_output

    # Test network statistics resource
    stats_output = await get_netstat_stats()
    assert isinstance(stats_output, str)
    assert "Network Statistics" in stats_output

    # Test routing table resource
    routing_output = await get_netstat_routing()
    assert isinstance(routing_output, str)
    assert "Routing Table" in routing_output

    # Test port-specific resource with a common port
    port_output = await get_netstat_port("80")
    assert isinstance(port_output, str)
    assert "Connections on Port 80" in port_output

    # Test invalid port
    invalid_port_output = await get_netstat_port("invalid")
    assert isinstance(invalid_port_output, str)
    assert "Invalid port number" in invalid_port_output
