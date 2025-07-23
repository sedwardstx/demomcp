"""
Process monitoring MCP resources.
"""

from datetime import datetime

import psutil
from mcp.server import FastMCP


def register_process_resources(mcp: FastMCP):
    """Register all process-related resources with the MCP server."""

    @mcp.resource("system://process-list")
    async def get_process_list() -> str:
        """
        Get current process list with PID, CPU, and memory usage.

        This resource provides a snapshot of running processes
        with their resource utilization for troubleshooting.
        """
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
