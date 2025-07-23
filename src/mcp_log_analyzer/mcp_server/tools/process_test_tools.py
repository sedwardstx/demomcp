"""
Process monitoring and system resource testing MCP tools.
"""

from typing import Any, Dict, List

import psutil
from mcp.server import FastMCP
from pydantic import BaseModel, Field


class ProcessAnalysisRequest(BaseModel):
    """Request model for process analysis."""

    process_name: str = Field(None, description="Specific process name to analyze")
    min_cpu_percent: float = Field(0.0, description="Minimum CPU usage threshold")
    min_memory_percent: float = Field(0.0, description="Minimum memory usage threshold")
    max_results: int = Field(20, description="Maximum number of processes to return")
    sort_by: str = Field("cpu", description="Sort by 'cpu', 'memory', or 'pid'")


class SystemResourceRequest(BaseModel):
    """Request model for system resource monitoring."""

    include_network: bool = Field(True, description="Include network statistics")
    include_disk: bool = Field(True, description="Include disk I/O statistics")
    sample_interval: float = Field(1.0, description="Sampling interval in seconds")


class ProcessMonitoringRequest(BaseModel):
    """Request model for process monitoring over time."""

    process_name: str = Field(..., description="Process name to monitor")
    duration_seconds: int = Field(60, description="Monitoring duration in seconds")
    sample_interval: float = Field(5.0, description="Sampling interval in seconds")


def register_process_test_tools(mcp: FastMCP):
    """Register all process testing tools with the MCP server."""

    @mcp.tool()
    async def test_system_resources_access() -> Dict[str, Any]:
        """
        Test system resource monitoring capabilities.

        This tool checks if the system can access various system
        resource information and provides diagnostic data.
        """
        try:
            test_results = {}

            # Test basic system info access
            try:
                test_results["cpu"] = {
                    "accessible": True,
                    "cpu_count": psutil.cpu_count(),
                    "cpu_count_logical": psutil.cpu_count(logical=True),
                    "current_usage": psutil.cpu_percent(interval=0.1),
                }
            except Exception as e:
                test_results["cpu"] = {"accessible": False, "error": str(e)}

            # Test memory access
            try:
                memory = psutil.virtual_memory()
                test_results["memory"] = {
                    "accessible": True,
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "percent_used": memory.percent,
                }
            except Exception as e:
                test_results["memory"] = {"accessible": False, "error": str(e)}

            # Test disk access
            try:
                disk = psutil.disk_usage("/")
                test_results["disk"] = {
                    "accessible": True,
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "percent_used": round((disk.used / disk.total) * 100, 1),
                }
            except Exception as e:
                test_results["disk"] = {"accessible": False, "error": str(e)}

            # Test network access
            try:
                network = psutil.net_io_counters()
                test_results["network"] = {
                    "accessible": True,
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv,
                }
            except Exception as e:
                test_results["network"] = {"accessible": False, "error": str(e)}

            # Test process enumeration
            try:
                processes = list(psutil.process_iter(["pid", "name"]))
                test_results["processes"] = {
                    "accessible": True,
                    "total_count": len(processes),
                    "sample_processes": [p.info for p in processes[:5]],
                }
            except Exception as e:
                test_results["processes"] = {"accessible": False, "error": str(e)}

            return {
                "status": "completed",
                "psutil_version": psutil.__version__,
                "test_results": test_results,
            }

        except Exception as e:
            return {"error": f"Error testing system resources: {str(e)}"}

    @mcp.tool()
    async def analyze_system_performance(
        request: SystemResourceRequest,
    ) -> Dict[str, Any]:
        """
        Analyze current system performance and resource usage.

        This tool provides a comprehensive analysis of system performance
        including CPU, memory, disk, and network usage patterns.
        """
        try:
            performance_data = {}

            # CPU Analysis
            cpu_percent = psutil.cpu_percent(interval=request.sample_interval)
            cpu_freq = psutil.cpu_freq()
            performance_data["cpu"] = {
                "usage_percent": cpu_percent,
                "core_count": psutil.cpu_count(),
                "logical_core_count": psutil.cpu_count(logical=True),
                "frequency": {
                    "current": cpu_freq.current if cpu_freq else None,
                    "min": cpu_freq.min if cpu_freq else None,
                    "max": cpu_freq.max if cpu_freq else None,
                },
                "load_average": (
                    psutil.getloadavg() if hasattr(psutil, "getloadavg") else None
                ),
            }

            # Memory Analysis
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            performance_data["memory"] = {
                "virtual": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "percent_used": memory.percent,
                },
                "swap": {
                    "total_gb": round(swap.total / (1024**3), 2),
                    "used_gb": round(swap.used / (1024**3), 2),
                    "percent_used": swap.percent,
                },
            }

            # Disk Analysis
            if request.include_disk:
                disk_usage = psutil.disk_usage("/")
                disk_io = psutil.disk_io_counters()
                performance_data["disk"] = {
                    "usage": {
                        "total_gb": round(disk_usage.total / (1024**3), 2),
                        "used_gb": round(disk_usage.used / (1024**3), 2),
                        "free_gb": round(disk_usage.free / (1024**3), 2),
                        "percent_used": round(
                            (disk_usage.used / disk_usage.total) * 100, 1
                        ),
                    },
                    "io_counters": (
                        {
                            "read_bytes": disk_io.read_bytes if disk_io else None,
                            "write_bytes": disk_io.write_bytes if disk_io else None,
                            "read_count": disk_io.read_count if disk_io else None,
                            "write_count": disk_io.write_count if disk_io else None,
                        }
                        if disk_io
                        else None
                    ),
                }

            # Network Analysis
            if request.include_network:
                net_io = psutil.net_io_counters()
                net_connections = len(psutil.net_connections())
                performance_data["network"] = {
                    "io_counters": (
                        {
                            "bytes_sent": net_io.bytes_sent if net_io else None,
                            "bytes_recv": net_io.bytes_recv if net_io else None,
                            "packets_sent": net_io.packets_sent if net_io else None,
                            "packets_recv": net_io.packets_recv if net_io else None,
                        }
                        if net_io
                        else None
                    ),
                    "active_connections": net_connections,
                }

            # Performance Assessment
            performance_status = "good"
            issues = []

            if cpu_percent > 80:
                performance_status = "concerning"
                issues.append(f"High CPU usage: {cpu_percent}%")
            elif cpu_percent > 60:
                performance_status = "fair"
                issues.append(f"Moderate CPU usage: {cpu_percent}%")

            if memory.percent > 90:
                performance_status = "concerning"
                issues.append(f"High memory usage: {memory.percent}%")
            elif memory.percent > 75:
                if performance_status == "good":
                    performance_status = "fair"
                issues.append(f"Moderate memory usage: {memory.percent}%")

            return {
                "performance_status": performance_status,
                "issues": issues,
                "performance_data": performance_data,
                "sampling_interval": request.sample_interval,
            }

        except Exception as e:
            return {"error": f"Error analyzing system performance: {str(e)}"}

    @mcp.tool()
    async def find_resource_intensive_processes(
        request: ProcessAnalysisRequest,
    ) -> Dict[str, Any]:
        """
        Find processes that are consuming significant system resources.

        This tool identifies processes with high CPU or memory usage
        and provides detailed information for troubleshooting.
        """
        try:
            processes = []

            # Collect process information
            for proc in psutil.process_iter(
                [
                    "pid",
                    "name",
                    "cpu_percent",
                    "memory_percent",
                    "memory_info",
                    "create_time",
                    "status",
                    "cmdline",
                ]
            ):
                try:
                    proc_info = proc.info

                    # Get CPU percentage with brief interval
                    if proc_info["cpu_percent"] is None:
                        proc_info["cpu_percent"] = proc.cpu_percent(interval=0.1)

                    # Apply filters
                    if (
                        request.process_name
                        and request.process_name.lower()
                        not in proc_info["name"].lower()
                    ):
                        continue

                    if proc_info["cpu_percent"] < request.min_cpu_percent:
                        continue

                    if proc_info["memory_percent"] < request.min_memory_percent:
                        continue

                    # Add additional details
                    proc_info["memory_mb"] = (
                        round(proc_info["memory_info"].rss / (1024 * 1024), 1)
                        if proc_info["memory_info"]
                        else 0
                    )
                    proc_info["command_line"] = (
                        " ".join(proc_info["cmdline"][:3])
                        if proc_info["cmdline"]
                        else ""
                    )

                    processes.append(proc_info)

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Sort processes
            if request.sort_by == "cpu":
                processes.sort(key=lambda x: x.get("cpu_percent", 0), reverse=True)
            elif request.sort_by == "memory":
                processes.sort(key=lambda x: x.get("memory_percent", 0), reverse=True)
            elif request.sort_by == "pid":
                processes.sort(key=lambda x: x.get("pid", 0))

            # Limit results
            limited_processes = processes[: request.max_results]

            # Calculate summary statistics
            if processes:
                total_cpu = sum(p.get("cpu_percent", 0) for p in processes)
                total_memory = sum(p.get("memory_percent", 0) for p in processes)
                avg_cpu = total_cpu / len(processes)
                avg_memory = total_memory / len(processes)
            else:
                total_cpu = avg_cpu = total_memory = avg_memory = 0

            return {
                "search_criteria": {
                    "process_name": request.process_name,
                    "min_cpu_percent": request.min_cpu_percent,
                    "min_memory_percent": request.min_memory_percent,
                    "sort_by": request.sort_by,
                },
                "processes": limited_processes,
                "summary": {
                    "total_matching": len(processes),
                    "returned_count": len(limited_processes),
                    "total_cpu_usage": round(total_cpu, 1),
                    "total_memory_usage": round(total_memory, 1),
                    "average_cpu_usage": round(avg_cpu, 1),
                    "average_memory_usage": round(avg_memory, 1),
                },
            }

        except Exception as e:
            return {"error": f"Error finding resource intensive processes: {str(e)}"}

    @mcp.tool()
    async def monitor_process_health(process_name: str) -> Dict[str, Any]:
        """
        Monitor the health and status of a specific process.

        This tool provides detailed information about a specific process
        including resource usage, status, and potential issues.
        """
        try:
            matching_processes = []

            # Find all processes matching the name
            for proc in psutil.process_iter(
                [
                    "pid",
                    "name",
                    "cpu_percent",
                    "memory_percent",
                    "memory_info",
                    "create_time",
                    "status",
                    "cmdline",
                    "num_threads",
                    "connections",
                ]
            ):
                try:
                    if process_name.lower() in proc.info["name"].lower():
                        proc_info = proc.info.copy()

                        # Get current CPU usage
                        proc_info["current_cpu"] = proc.cpu_percent(interval=0.1)

                        # Add memory in MB
                        proc_info["memory_mb"] = (
                            round(proc_info["memory_info"].rss / (1024 * 1024), 1)
                            if proc_info["memory_info"]
                            else 0
                        )

                        # Get process age
                        from datetime import datetime

                        create_time = datetime.fromtimestamp(proc_info["create_time"])
                        proc_info["age"] = str(datetime.now() - create_time).split(".")[
                            0
                        ]

                        # Count network connections
                        try:
                            connections = proc.connections()
                            proc_info["network_connections"] = len(connections)
                        except (psutil.AccessDenied, psutil.NoSuchProcess):
                            proc_info["network_connections"] = "Access denied"

                        matching_processes.append(proc_info)

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if not matching_processes:
                return {
                    "process_name": process_name,
                    "found": False,
                    "message": f"No processes found matching '{process_name}'",
                }

            # Health assessment
            health_issues = []
            total_cpu = sum(p.get("current_cpu", 0) for p in matching_processes)
            total_memory = sum(p.get("memory_percent", 0) for p in matching_processes)

            if total_cpu > 50:
                health_issues.append(f"High CPU usage: {total_cpu:.1f}%")
            if total_memory > 20:
                health_issues.append(f"High memory usage: {total_memory:.1f}%")

            # Check for multiple instances
            if len(matching_processes) > 1:
                health_issues.append(
                    f"Multiple instances running: {len(matching_processes)}"
                )

            health_status = "healthy" if not health_issues else "issues_detected"

            return {
                "process_name": process_name,
                "found": True,
                "health_status": health_status,
                "health_issues": health_issues,
                "process_count": len(matching_processes),
                "processes": matching_processes,
                "summary": {
                    "total_cpu_usage": round(total_cpu, 1),
                    "total_memory_usage": round(total_memory, 1),
                    "total_memory_mb": sum(
                        p.get("memory_mb", 0) for p in matching_processes
                    ),
                },
            }

        except Exception as e:
            return {"error": f"Error monitoring process health: {str(e)}"}

    @mcp.tool()
    async def get_system_health_summary() -> Dict[str, Any]:
        """
        Get overall system health summary.

        This tool provides a comprehensive overview of system health
        including resource usage, top processes, and potential issues.
        """
        try:
            from datetime import datetime

            # System resource summary
            cpu_percent = psutil.cpu_percent(interval=1.0)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Get top processes by CPU and memory
            processes = []
            for proc in psutil.process_iter(
                ["pid", "name", "cpu_percent", "memory_percent"]
            ):
                try:
                    proc_info = proc.info
                    if proc_info["cpu_percent"] is None:
                        proc_info["cpu_percent"] = proc.cpu_percent(interval=0.1)
                    processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Top CPU consumers
            top_cpu = sorted(
                processes, key=lambda x: x.get("cpu_percent", 0), reverse=True
            )[:5]

            # Top memory consumers
            top_memory = sorted(
                processes, key=lambda x: x.get("memory_percent", 0), reverse=True
            )[:5]

            # Health assessment
            health_score = 100
            issues = []

            if cpu_percent > 80:
                health_score -= 30
                issues.append(f"High CPU usage: {cpu_percent}%")
            elif cpu_percent > 60:
                health_score -= 15
                issues.append(f"Moderate CPU usage: {cpu_percent}%")

            if memory.percent > 90:
                health_score -= 25
                issues.append(f"High memory usage: {memory.percent}%")
            elif memory.percent > 75:
                health_score -= 10
                issues.append(f"Moderate memory usage: {memory.percent}%")

            disk_percent = (disk.used / disk.total) * 100
            if disk_percent > 90:
                health_score -= 20
                issues.append(f"High disk usage: {disk_percent:.1f}%")
            elif disk_percent > 80:
                health_score -= 10
                issues.append(f"Moderate disk usage: {disk_percent:.1f}%")

            # Determine overall health status
            if health_score >= 80:
                health_status = "excellent"
            elif health_score >= 60:
                health_status = "good"
            elif health_score >= 40:
                health_status = "fair"
            else:
                health_status = "poor"

            return {
                "health_status": health_status,
                "health_score": max(0, health_score),
                "issues": issues,
                "system_resources": {
                    "cpu_usage_percent": cpu_percent,
                    "memory_usage_percent": memory.percent,
                    "disk_usage_percent": round(disk_percent, 1),
                    "process_count": len(processes),
                },
                "top_processes": {
                    "cpu_consumers": top_cpu,
                    "memory_consumers": top_memory,
                },
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

        except Exception as e:
            return {"error": f"Error getting system health summary: {str(e)}"}
