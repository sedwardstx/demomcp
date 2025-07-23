"""
Linux system monitoring MCP resources.
"""

import platform
import subprocess
from pathlib import Path

from mcp.server import FastMCP


def register_linux_resources(mcp: FastMCP):
    """Register all Linux-related resources with the MCP server."""

    from ..server import parse_time_param

    @mcp.resource("system://linux-logs")
    async def get_linux_system_logs() -> str:
        """
        Get Linux system logs with default parameters.

        Use parameterized versions for more control:
        - system://linux-logs/last/50 - Last 50 lines
        - system://linux-logs/time/30m - Last 30 minutes
        - system://linux-logs/range/2025-01-07 13:00/2025-01-07 14:00 - Time range
        """
        # Default to last 50 lines
        return await get_linux_logs_with_count("50")

    @mcp.resource("system://linux-logs/last/{count}")
    async def get_linux_logs_with_count(count: str) -> str:
        """
        Get recent Linux system logs by line count.

        Args:
            count: Number of lines to retrieve (e.g., "100")
        """
        if platform.system() != "Linux":
            return "This resource is only available on Linux systems."

        try:
            line_count = int(count)
            result = []
            result.append(f"=== Linux System Logs (Last {line_count} lines) ===\n")

            # Try to get systemd journal logs
            try:
                result.append(f"\n--- Systemd Journal ---")
                journal_output = subprocess.run(
                    ["journalctl", "-n", str(line_count), "--no-pager"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if journal_output.returncode == 0:
                    result.append(journal_output.stdout)
                else:
                    result.append(
                        "Unable to read systemd journal (may require permissions)"
                    )
            except Exception as e:
                result.append(f"Systemd journal not available: {str(e)}")

            # Try to read syslog
            syslog_paths = [
                "/var/log/syslog",  # Debian/Ubuntu
                "/var/log/messages",  # RHEL/CentOS
            ]

            for syslog_path in syslog_paths:
                if Path(syslog_path).exists():
                    try:
                        result.append(f"\n--- {syslog_path} ---")
                        with open(syslog_path, "r") as f:
                            lines = f.readlines()
                            result.extend(lines[-line_count:])
                        break
                    except PermissionError:
                        result.append(f"Permission denied reading {syslog_path}")
                    except Exception as e:
                        result.append(f"Error reading {syslog_path}: {str(e)}")

            # Common application logs
            app_logs = {
                "Apache": ["/var/log/apache2/error.log", "/var/log/httpd/error_log"],
                "Nginx": ["/var/log/nginx/error.log"],
                "MySQL": ["/var/log/mysql/error.log", "/var/log/mysqld.log"],
                "PostgreSQL": ["/var/log/postgresql/postgresql.log"],
            }

            result.append("\n--- Application Logs ---")
            for app_name, log_paths in app_logs.items():
                for log_path in log_paths:
                    if Path(log_path).exists():
                        try:
                            result.append(f"\n{app_name} ({log_path}):")
                            with open(log_path, "r") as f:
                                lines = f.readlines()
                                result.extend(
                                    lines[-(line_count // 5) :]
                                )  # Show fewer lines for app logs
                            break
                        except:
                            pass

            return "\n".join(result)

        except ValueError:
            return f"Invalid count parameter: {count}"
        except Exception as e:
            return f"Error accessing Linux logs: {str(e)}"

    @mcp.resource("system://linux-logs/time/{duration}")
    async def get_linux_logs_by_time(duration: str) -> str:
        """
        Get Linux logs from the last N minutes/hours/days.

        Args:
            duration: Time duration (e.g., "30m", "2h", "1d")
        """
        if platform.system() != "Linux":
            return "This resource is only available on Linux systems."

        try:
            start_time = parse_time_param(duration)
            if not start_time:
                return "Invalid duration format. Use format like '30m', '2h', or '1d'."

            result = []
            result.append(
                f"=== Linux System Logs (Since {start_time.strftime('%Y-%m-%d %H:%M:%S')}) ===\n"
            )

            # Try to get systemd journal logs with time filter
            try:
                result.append(f"\n--- Systemd Journal ---")
                since_arg = f"--since={start_time.strftime('%Y-%m-%d %H:%M:%S')}"
                journal_output = subprocess.run(
                    ["journalctl", since_arg, "--no-pager"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if journal_output.returncode == 0:
                    result.append(journal_output.stdout)
                else:
                    result.append(
                        "Unable to read systemd journal (may require permissions)"
                    )
            except Exception as e:
                result.append(f"Systemd journal not available: {str(e)}")

            # For syslog, we need to parse timestamps
            syslog_paths = [
                "/var/log/syslog",  # Debian/Ubuntu
                "/var/log/messages",  # RHEL/CentOS
            ]

            for syslog_path in syslog_paths:
                if Path(syslog_path).exists():
                    try:
                        result.append(f"\n--- {syslog_path} ---")
                        matching_lines = []
                        with open(syslog_path, "r") as f:
                            for line in f:
                                # Simple check if line contains a recent timestamp
                                # This is a simplified approach
                                if start_time.strftime("%b %d") in line:
                                    matching_lines.append(line)

                        if matching_lines:
                            result.extend(matching_lines)
                        else:
                            result.append(f"No entries found since {start_time}")
                        break
                    except PermissionError:
                        result.append(f"Permission denied reading {syslog_path}")
                    except Exception as e:
                        result.append(f"Error reading {syslog_path}: {str(e)}")

            return "\n".join(result)

        except ValueError as e:
            return f"Invalid time parameter: {str(e)}"
        except Exception as e:
            return f"Error accessing Linux logs: {str(e)}"

    @mcp.resource("system://linux-logs/range/{start}/{end}")
    async def get_linux_logs_by_range(start: str, end: str) -> str:
        """
        Get Linux logs within a specific time range.

        Args:
            start: Start time (e.g., "2025-01-07 13:00")
            end: End time (e.g., "2025-01-07 14:00")
        """
        if platform.system() != "Linux":
            return "This resource is only available on Linux systems."

        try:
            start_time = parse_time_param(start)
            end_time = parse_time_param(end)

            if not start_time or not end_time:
                return "Invalid time format. Use format like '2025-01-07 13:00'."

            result = []
            result.append(
                f"=== Linux System Logs ({start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}) ===\n"
            )

            # Try to get systemd journal logs with time range
            try:
                result.append(f"\n--- Systemd Journal ---")
                since_arg = f"--since={start_time.strftime('%Y-%m-%d %H:%M:%S')}"
                until_arg = f"--until={end_time.strftime('%Y-%m-%d %H:%M:%S')}"
                journal_output = subprocess.run(
                    ["journalctl", since_arg, until_arg, "--no-pager"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if journal_output.returncode == 0:
                    result.append(journal_output.stdout)
                else:
                    result.append(
                        "Unable to read systemd journal (may require permissions)"
                    )
            except Exception as e:
                result.append(f"Systemd journal not available: {str(e)}")

            return "\n".join(result)

        except ValueError as e:
            return f"Invalid time parameter: {str(e)}"
        except Exception as e:
            return f"Error accessing Linux logs: {str(e)}"
