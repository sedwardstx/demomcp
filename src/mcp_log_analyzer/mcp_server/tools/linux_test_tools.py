"""
Linux system monitoring and log testing MCP tools.
"""

import platform
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from mcp.server import FastMCP
from pydantic import BaseModel, Field


class LinuxLogTestRequest(BaseModel):
    """Request model for testing Linux log access."""

    log_paths: List[str] = Field(
        default_factory=lambda: ["/var/log/syslog", "/var/log/messages"],
        description="List of log file paths to test",
    )
    check_journalctl: bool = Field(
        True, description="Whether to test systemd journal access"
    )


class LinuxLogQueryRequest(BaseModel):
    """Request model for querying Linux logs."""

    service_name: str = Field(None, description="Specific service to query logs for")
    priority: str = Field(
        None,
        description="Log priority (emerg, alert, crit, err, warning, notice, info, debug)",
    )
    time_duration: str = Field(
        "1h", description="Time duration (e.g., '30m', '2h', '1d')"
    )
    max_lines: int = Field(100, description="Maximum number of log lines to return")


class LinuxServiceAnalysisRequest(BaseModel):
    """Request model for analyzing Linux services."""

    service_pattern: str = Field(
        None, description="Service name pattern to analyze (e.g., 'nginx', 'apache')"
    )
    include_failed: bool = Field(
        True, description="Include failed services in analysis"
    )


def register_linux_test_tools(mcp: FastMCP):
    """Register all Linux testing tools with the MCP server."""

    @mcp.tool()
    async def test_linux_log_access() -> Dict[str, Any]:
        """
        Test Linux log file and systemd journal access.

        This tool checks if the system can access various Linux log sources
        and provides diagnostic information about available logs.
        """
        if platform.system() != "Linux":
            return {
                "status": "unavailable",
                "message": "Linux log tools are only available on Linux systems",
                "platform": platform.system(),
            }

        test_results = {
            "log_files": {},
            "systemd_journal": {"available": False, "accessible": False},
            "commands": {},
        }

        # Test common log file access
        common_logs = {
            "/var/log/syslog": "System log (Debian/Ubuntu)",
            "/var/log/messages": "System log (RHEL/CentOS)",
            "/var/log/auth.log": "Authentication log",
            "/var/log/kern.log": "Kernel log",
            "/var/log/dmesg": "Boot messages",
        }

        for log_path, description in common_logs.items():
            path_obj = Path(log_path)
            if path_obj.exists():
                try:
                    # Test read access
                    with open(log_path, "r") as f:
                        f.read(100)  # Read first 100 chars
                    test_results["log_files"][log_path] = {
                        "exists": True,
                        "readable": True,
                        "description": description,
                        "size_mb": round(path_obj.stat().st_size / (1024 * 1024), 2),
                    }
                except PermissionError:
                    test_results["log_files"][log_path] = {
                        "exists": True,
                        "readable": False,
                        "description": description,
                        "error": "Permission denied",
                    }
                except Exception as e:
                    test_results["log_files"][log_path] = {
                        "exists": True,
                        "readable": False,
                        "description": description,
                        "error": str(e),
                    }
            else:
                test_results["log_files"][log_path] = {
                    "exists": False,
                    "readable": False,
                    "description": description,
                }

        # Test systemd journal access
        try:
            result = subprocess.run(
                ["journalctl", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                test_results["systemd_journal"]["available"] = True

                # Test actual journal access
                try:
                    result = subprocess.run(
                        ["journalctl", "-n", "1", "--no-pager"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    test_results["systemd_journal"]["accessible"] = (
                        result.returncode == 0
                    )
                    if result.returncode != 0:
                        test_results["systemd_journal"]["error"] = result.stderr
                except Exception as e:
                    test_results["systemd_journal"]["error"] = str(e)
        except FileNotFoundError:
            test_results["systemd_journal"]["available"] = False
        except Exception as e:
            test_results["systemd_journal"]["error"] = str(e)

        # Test common system commands
        commands_to_test = ["ss", "netstat", "ps", "top", "systemctl"]
        for cmd in commands_to_test:
            try:
                result = subprocess.run(
                    [cmd, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                test_results["commands"][cmd] = {"available": True}
            except FileNotFoundError:
                test_results["commands"][cmd] = {"available": False}
            except Exception:
                # Some commands might not support --version but still exist
                test_results["commands"][cmd] = {
                    "available": True,
                    "version_check_failed": True,
                }

        return {
            "status": "completed",
            "platform": platform.system(),
            "distribution": platform.platform(),
            "test_results": test_results,
        }

    @mcp.tool()
    async def query_systemd_journal(request: LinuxLogQueryRequest) -> Dict[str, Any]:
        """
        Query systemd journal with specific criteria.

        This tool allows filtering systemd journal entries by service,
        priority, and time range for targeted analysis.
        """
        if platform.system() != "Linux":
            return {"error": "This tool is only available on Linux systems"}

        try:
            from ..server import parse_time_param

            # Build journalctl command
            cmd = ["journalctl", "--no-pager", "-o", "short"]

            # Add time filter
            if request.time_duration:
                try:
                    start_time = parse_time_param(request.time_duration)
                    since_arg = f"--since={start_time.strftime('%Y-%m-%d %H:%M:%S')}"
                    cmd.append(since_arg)
                except Exception as e:
                    return {"error": f"Invalid time duration: {str(e)}"}

            # Add service filter
            if request.service_name:
                cmd.extend(["-u", request.service_name])

            # Add priority filter
            if request.priority:
                cmd.extend(["-p", request.priority])

            # Add line limit
            cmd.extend(["-n", str(request.max_lines)])

            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                return {
                    "query_criteria": {
                        "service_name": request.service_name,
                        "priority": request.priority,
                        "time_duration": request.time_duration,
                        "max_lines": request.max_lines,
                    },
                    "log_entries": lines,
                    "total_entries": len(lines),
                    "command_used": " ".join(cmd),
                }
            else:
                return {
                    "error": f"journalctl command failed: {result.stderr}",
                    "command_used": " ".join(cmd),
                }

        except Exception as e:
            return {"error": f"Error querying systemd journal: {str(e)}"}

    @mcp.tool()
    async def analyze_linux_services(
        request: LinuxServiceAnalysisRequest,
    ) -> Dict[str, Any]:
        """
        Analyze Linux services status and recent activity.

        This tool provides an overview of systemd services, their status,
        and recent log activity for system health assessment.
        """
        if platform.system() != "Linux":
            return {"error": "This tool is only available on Linux systems"}

        try:
            # Get service status
            cmd = ["systemctl", "list-units", "--type=service", "--no-pager"]
            if request.include_failed:
                cmd.append("--failed")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            services_info = {"active": [], "failed": [], "summary": {}}

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")

                for line in lines[1:]:  # Skip header
                    if not line.strip() or "LOAD" in line:
                        continue

                    parts = line.split()
                    if len(parts) >= 4:
                        service_name = parts[0]
                        load_state = parts[1]
                        active_state = parts[2]
                        sub_state = parts[3]

                        # Filter by pattern if specified
                        if (
                            request.service_pattern
                            and request.service_pattern.lower()
                            not in service_name.lower()
                        ):
                            continue

                        service_info = {
                            "name": service_name,
                            "load": load_state,
                            "active": active_state,
                            "sub": sub_state,
                        }

                        if active_state == "active":
                            services_info["active"].append(service_info)
                        elif active_state == "failed":
                            services_info["failed"].append(service_info)

            # Get recent journal entries for failed services
            if services_info["failed"]:
                for service in services_info["failed"][
                    :5
                ]:  # Limit to first 5 failed services
                    try:
                        journal_cmd = [
                            "journalctl",
                            "-u",
                            service["name"],
                            "-n",
                            "10",
                            "--no-pager",
                            "--since",
                            "1 hour ago",
                        ]
                        journal_result = subprocess.run(
                            journal_cmd, capture_output=True, text=True, timeout=5
                        )
                        if journal_result.returncode == 0:
                            service["recent_logs"] = (
                                journal_result.stdout.strip().split("\n")[-5:]
                            )
                    except Exception:
                        service["recent_logs"] = ["Unable to fetch recent logs"]

            services_info["summary"] = {
                "total_active": len(services_info["active"]),
                "total_failed": len(services_info["failed"]),
                "pattern_filter": request.service_pattern,
            }

            # Overall system health assessment
            if len(services_info["failed"]) == 0:
                health_status = "healthy"
            elif len(services_info["failed"]) < 3:
                health_status = "fair"
            else:
                health_status = "concerning"

            return {
                "health_status": health_status,
                "services": services_info,
                "analysis_criteria": {
                    "service_pattern": request.service_pattern,
                    "include_failed": request.include_failed,
                },
                "timestamp": subprocess.run(
                    ["date", "+%Y-%m-%d %H:%M:%S"], capture_output=True, text=True
                ).stdout.strip(),
            }

        except Exception as e:
            return {"error": f"Error analyzing Linux services: {str(e)}"}

    @mcp.tool()
    async def get_linux_system_overview() -> Dict[str, Any]:
        """
        Get comprehensive Linux system overview.

        This tool provides system information, resource usage,
        and health indicators for Linux systems.
        """
        if platform.system() != "Linux":
            return {"error": "This tool is only available on Linux systems"}

        try:
            system_info = {}

            # Basic system information
            system_info["system"] = {
                "hostname": subprocess.run(
                    ["hostname"], capture_output=True, text=True
                ).stdout.strip(),
                "uptime": subprocess.run(
                    ["uptime"], capture_output=True, text=True
                ).stdout.strip(),
                "kernel": subprocess.run(
                    ["uname", "-r"], capture_output=True, text=True
                ).stdout.strip(),
                "distribution": platform.platform(),
            }

            # Memory information
            try:
                with open("/proc/meminfo", "r") as f:
                    meminfo = f.read()
                    mem_lines = meminfo.split("\n")
                    mem_total = next(
                        (line for line in mem_lines if line.startswith("MemTotal:")), ""
                    )
                    mem_available = next(
                        (
                            line
                            for line in mem_lines
                            if line.startswith("MemAvailable:")
                        ),
                        "",
                    )

                system_info["memory"] = {
                    "total": mem_total.split()[1] + " kB" if mem_total else "Unknown",
                    "available": (
                        mem_available.split()[1] + " kB" if mem_available else "Unknown"
                    ),
                }
            except Exception:
                system_info["memory"] = {"error": "Unable to read memory information"}

            # CPU information
            try:
                with open("/proc/loadavg", "r") as f:
                    loadavg = f.read().strip()
                system_info["cpu"] = {"load_average": loadavg}
            except Exception:
                system_info["cpu"] = {"error": "Unable to read CPU information"}

            # Disk usage for root filesystem
            try:
                df_result = subprocess.run(
                    ["df", "-h", "/"], capture_output=True, text=True
                )
                if df_result.returncode == 0:
                    df_lines = df_result.stdout.strip().split("\n")
                    if len(df_lines) > 1:
                        root_disk = df_lines[1].split()
                        system_info["disk"] = {
                            "filesystem": root_disk[0],
                            "size": root_disk[1],
                            "used": root_disk[2],
                            "available": root_disk[3],
                            "use_percent": root_disk[4],
                        }
            except Exception:
                system_info["disk"] = {"error": "Unable to read disk information"}

            # Recent critical logs
            try:
                journal_result = subprocess.run(
                    [
                        "journalctl",
                        "-p",
                        "err",
                        "-n",
                        "5",
                        "--no-pager",
                        "--since",
                        "1 hour ago",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if journal_result.returncode == 0:
                    recent_errors = journal_result.stdout.strip().split("\n")
                    system_info["recent_errors"] = (
                        recent_errors if recent_errors != [""] else []
                    )
                else:
                    system_info["recent_errors"] = ["Unable to fetch recent error logs"]
            except Exception:
                system_info["recent_errors"] = ["Error accessing systemd journal"]

            return {
                "status": "success",
                "system_overview": system_info,
                "timestamp": subprocess.run(
                    ["date", "+%Y-%m-%d %H:%M:%S"], capture_output=True, text=True
                ).stdout.strip(),
            }

        except Exception as e:
            return {"error": f"Error getting Linux system overview: {str(e)}"}
