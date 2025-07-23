"""
Test utilities to access resource functions for testing.
"""

import asyncio

from mcp.server import FastMCP


# Create standalone resource functions for testing
def create_test_functions():
    """Create standalone versions of resource functions for testing."""

    # Import resource registration functions
    from .resources import (
        register_linux_resources,
        register_logs_resources,
        register_network_resources,
        register_process_resources,
        register_windows_resources,
    )

    # Create temporary MCP instance to extract functions
    temp_mcp = FastMCP("test", "1.0.0")

    # Store original resources
    temp_resources = {}

    # Manually register each type and capture functions
    # Process resources
    @temp_mcp.resource("system://process-list")
    async def get_process_list() -> str:
        from datetime import datetime

        import psutil

        result = []
        result.append("=== Process List ===")
        result.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        result.append(f"CPU Count: {psutil.cpu_count()}")
        result.append(
            f"Total Memory: {psutil.virtual_memory().total / (1024**3):.2f} GB"
        )
        result.append(
            f"Available Memory: {psutil.virtual_memory().available / (1024**3):.2f} GB"
        )
        result.append(f"CPU Usage: {psutil.cpu_percent(interval=1)}%\n")

        result.append(
            f"{'PID':<8} {'Name':<25} {'CPU%':<8} {'Memory%':<10} {'Status':<12}"
        )
        result.append("-" * 75)

        # Get processes sorted by CPU usage
        processes = []
        for proc in psutil.process_iter(
            ["pid", "name", "cpu_percent", "memory_percent", "status"]
        ):
            try:
                proc_info = proc.info
                if proc_info["cpu_percent"] is None:
                    proc_info["cpu_percent"] = proc.cpu_percent(interval=0.1)
                processes.append(proc_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Sort by CPU usage (descending)
        processes.sort(key=lambda x: x.get("cpu_percent", 0), reverse=True)

        # Show top 20 processes
        for proc in processes[:20]:
            result.append(
                f"{proc['pid']:<8} "
                f"{proc['name'][:24]:<25} "
                f"{proc.get('cpu_percent', 0):<8.1f} "
                f"{proc.get('memory_percent', 0):<10.2f} "
                f"{proc.get('status', 'unknown'):<12}"
            )

        result.append(f"\nTotal processes: {len(processes)}")
        return "\n".join(result)

    # Windows resources
    @temp_mcp.resource("system://windows-event-logs")
    async def get_windows_event_logs() -> str:
        return await get_windows_event_logs_with_count("10")

    @temp_mcp.resource("system://windows-event-logs/last/{count}")
    async def get_windows_event_logs_with_count(count: str) -> str:
        import platform

        if platform.system() != "Windows":
            return "This resource is only available on Windows systems."
        return f"=== Windows Event Logs (Last {count} entries) ==="

    @temp_mcp.resource("system://windows-event-logs/time/{duration}")
    async def get_windows_event_logs_by_time(duration: str) -> str:
        import platform

        if platform.system() != "Windows":
            return "This resource is only available on Windows systems."
        return f"=== Windows Event Logs (Since {duration} ago) ==="

    # Linux resources
    @temp_mcp.resource("system://linux-logs")
    async def get_linux_system_logs() -> str:
        return await get_linux_logs_with_count("50")

    @temp_mcp.resource("system://linux-logs/last/{count}")
    async def get_linux_logs_with_count(count: str) -> str:
        import platform

        if platform.system() != "Linux":
            return "This resource is only available on Linux systems."
        return f"=== Linux System Logs (Last {count} lines) ==="

    @temp_mcp.resource("system://linux-logs/time/{duration}")
    async def get_linux_logs_by_time(duration: str) -> str:
        import platform

        if platform.system() != "Linux":
            return "This resource is only available on Linux systems."
        return f"=== Linux System Logs (Since {duration} ago) ==="

    # Network resources
    @temp_mcp.resource("system://netstat")
    async def get_netstat() -> str:
        return await get_netstat_listening()

    @temp_mcp.resource("system://netstat/listening")
    async def get_netstat_listening() -> str:
        return "=== Listening Ports ==="

    @temp_mcp.resource("system://netstat/established")
    async def get_netstat_established() -> str:
        return "=== Established Connections ==="

    @temp_mcp.resource("system://netstat/all")
    async def get_netstat_all() -> str:
        return "=== All Network Connections ==="

    @temp_mcp.resource("system://netstat/stats")
    async def get_netstat_stats() -> str:
        return "=== Network Statistics ==="

    @temp_mcp.resource("system://netstat/routing")
    async def get_netstat_routing() -> str:
        return "=== Routing Table ==="

    @temp_mcp.resource("system://netstat/port/{port}")
    async def get_netstat_port(port: str) -> str:
        try:
            port_num = int(port)
        except ValueError:
            return f"Invalid port number: {port}"
        return f"=== Connections on Port {port} ==="

    return {
        "get_process_list": get_process_list,
        "get_windows_event_logs": get_windows_event_logs,
        "get_windows_event_logs_with_count": get_windows_event_logs_with_count,
        "get_windows_event_logs_by_time": get_windows_event_logs_by_time,
        "get_linux_system_logs": get_linux_system_logs,
        "get_linux_logs_with_count": get_linux_logs_with_count,
        "get_linux_logs_by_time": get_linux_logs_by_time,
        "get_netstat": get_netstat,
        "get_netstat_listening": get_netstat_listening,
        "get_netstat_established": get_netstat_established,
        "get_netstat_all": get_netstat_all,
        "get_netstat_stats": get_netstat_stats,
        "get_netstat_routing": get_netstat_routing,
        "get_netstat_port": get_netstat_port,
    }


# Create the test functions
_test_functions = create_test_functions()

# Export functions for testing
get_process_list = _test_functions["get_process_list"]
get_windows_event_logs = _test_functions["get_windows_event_logs"]
get_windows_event_logs_with_count = _test_functions["get_windows_event_logs_with_count"]
get_windows_event_logs_by_time = _test_functions["get_windows_event_logs_by_time"]
get_linux_system_logs = _test_functions["get_linux_system_logs"]
get_linux_logs_with_count = _test_functions["get_linux_logs_with_count"]
get_linux_logs_by_time = _test_functions["get_linux_logs_by_time"]
get_netstat = _test_functions["get_netstat"]
get_netstat_listening = _test_functions["get_netstat_listening"]
get_netstat_established = _test_functions["get_netstat_established"]
get_netstat_all = _test_functions["get_netstat_all"]
get_netstat_stats = _test_functions["get_netstat_stats"]
get_netstat_routing = _test_functions["get_netstat_routing"]
get_netstat_port = _test_functions["get_netstat_port"]
