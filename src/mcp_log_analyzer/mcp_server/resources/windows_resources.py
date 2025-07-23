"""
Windows system monitoring MCP resources.
"""

import platform
from datetime import datetime

from mcp.server import FastMCP


def register_windows_resources(mcp: FastMCP):
    """Register all Windows-related resources with the MCP server."""

    from ..server import parse_time_param

    @mcp.resource("system://windows-event-logs")
    async def get_windows_event_logs() -> str:
        """
        Get Windows System and Application event logs with default parameters.

        Use parameterized versions for more control:
        - system://windows-event-logs/last/20 - Last 20 entries
        - system://windows-event-logs/time/30m - Last 30 minutes
        - system://windows-event-logs/range/2025-01-07 13:00/2025-01-07 14:00 - Time range
        """
        # Default to last 10 entries
        return await get_windows_event_logs_with_count("10")

    @mcp.resource("system://windows-event-logs/last/{count}")
    async def get_windows_event_logs_with_count(count: str) -> str:
        """
        Get recent Windows System and Application event logs by count.

        Args:
            count: Number of entries to retrieve (e.g., "20")
        """
        if platform.system() != "Windows":
            return "This resource is only available on Windows systems."

        try:
            import win32evtlog
            import win32evtlogutil
            from win32con import EVENTLOG_BACKWARDS_READ, EVENTLOG_SEQUENTIAL_READ

            max_count = int(count)
            result = []
            result.append(f"=== Windows Event Logs (Last {max_count} entries) ===\n")

            for log_type in ["System", "Application"]:
                result.append(f"\n--- {log_type} Log ---")

                try:
                    hand = win32evtlog.OpenEventLog(None, log_type)
                    flags = EVENTLOG_BACKWARDS_READ | EVENTLOG_SEQUENTIAL_READ
                    
                    count = 0
                    while count < max_count:
                        events = win32evtlog.ReadEventLog(hand, flags, 0)
                        if not events:
                            break  # No more events to read
                        
                        for event in events:
                            if count >= max_count:
                                break

                            result.append(f"\nTime: {event.TimeGenerated}")
                            result.append(f"Source: {event.SourceName}")
                            result.append(f"Event ID: {event.EventID & 0xFFFFFFFF}")  # Convert to unsigned
                            result.append(
                                f"Type: {['Info', 'Warning', 'Error'][event.EventType - 1] if event.EventType <= 3 else 'Unknown'}"
                            )

                            try:
                                message = win32evtlogutil.SafeFormatMessage(event, log_type)
                                if message:
                                    result.append(f"Message: {message[:200]}...")
                            except:
                                result.append("Message: (Unable to format message)")

                            count += 1

                    win32evtlog.CloseEventLog(hand)

                except Exception as e:
                    result.append(f"Error reading {log_type} log: {str(e)}")

            return "\n".join(result)

        except ImportError:
            return "Windows Event Log access requires pywin32 package."
        except ValueError:
            return f"Invalid count parameter: {count}"
        except Exception as e:
            return f"Error accessing Windows Event Logs: {str(e)}"

    @mcp.resource("system://windows-event-logs/time/{duration}")
    async def get_windows_event_logs_by_time(duration: str) -> str:
        """
        Get Windows event logs from the last N minutes/hours/days.

        Args:
            duration: Time duration (e.g., "30m", "2h", "1d")
        """
        if platform.system() != "Windows":
            return "This resource is only available on Windows systems."

        try:
            start_time = parse_time_param(duration)
            if not start_time:
                return "Invalid duration format. Use format like '30m', '2h', or '1d'."

            import win32evtlog
            import win32evtlogutil
            from win32con import EVENTLOG_BACKWARDS_READ, EVENTLOG_SEQUENTIAL_READ

            result = []
            result.append(
                f"=== Windows Event Logs (Since {start_time.strftime('%Y-%m-%d %H:%M:%S')}) ===\n"
            )

            for log_type in ["System", "Application"]:
                result.append(f"\n--- {log_type} Log ---")

                try:
                    hand = win32evtlog.OpenEventLog(None, log_type)
                    flags = EVENTLOG_BACKWARDS_READ | EVENTLOG_SEQUENTIAL_READ
                    
                    event_count = 0
                    done_reading = False
                    
                    while not done_reading:
                        events = win32evtlog.ReadEventLog(hand, flags, 0)
                        if not events:
                            break  # No more events to read
                        
                        for event in events:
                            # Check if event is within time range
                            if event.TimeGenerated < start_time:
                                done_reading = True
                                break

                            result.append(f"\nTime: {event.TimeGenerated}")
                            result.append(f"Source: {event.SourceName}")
                            result.append(f"Event ID: {event.EventID & 0xFFFFFFFF}")  # Convert to unsigned
                            result.append(
                                f"Type: {['Info', 'Warning', 'Error'][event.EventType - 1] if event.EventType <= 3 else 'Unknown'}"
                            )

                            try:
                                message = win32evtlogutil.SafeFormatMessage(event, log_type)
                                if message:
                                    result.append(f"Message: {message[:200]}...")
                            except:
                                result.append("Message: (Unable to format message)")

                            event_count += 1

                    win32evtlog.CloseEventLog(hand)
                    result.append(f"\n{log_type}: {event_count} events found")

                except Exception as e:
                    result.append(f"Error reading {log_type} log: {str(e)}")

            return "\n".join(result)

        except ImportError:
            return "Windows Event Log access requires pywin32 package."
        except ValueError as e:
            return f"Invalid time parameter: {str(e)}"
        except Exception as e:
            return f"Error accessing Windows Event Logs: {str(e)}"

    @mcp.resource("system://windows-event-logs/range/{start}/{end}")
    async def get_windows_event_logs_by_range(start: str, end: str) -> str:
        """
        Get Windows event logs within a specific time range.

        Args:
            start: Start time (e.g., "2025-01-07 13:00")
            end: End time (e.g., "2025-01-07 14:00")
        """
        if platform.system() != "Windows":
            return "This resource is only available on Windows systems."

        try:
            start_time = parse_time_param(start)
            end_time = parse_time_param(end)

            if not start_time or not end_time:
                return "Invalid time format. Use format like '2025-01-07 13:00'."

            import win32evtlog
            import win32evtlogutil
            from win32con import EVENTLOG_BACKWARDS_READ, EVENTLOG_SEQUENTIAL_READ

            result = []
            result.append(
                f"=== Windows Event Logs ({start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}) ===\n"
            )

            for log_type in ["System", "Application"]:
                result.append(f"\n--- {log_type} Log ---")

                try:
                    hand = win32evtlog.OpenEventLog(None, log_type)
                    flags = EVENTLOG_BACKWARDS_READ | EVENTLOG_SEQUENTIAL_READ
                    
                    event_count = 0
                    done_reading = False
                    
                    while not done_reading:
                        events = win32evtlog.ReadEventLog(hand, flags, 0)
                        if not events:
                            break  # No more events to read
                        
                        for event in events:
                            # Check if we've gone past the time range
                            if event.TimeGenerated < start_time:
                                done_reading = True
                                break
                            
                            # Check if event is within time range
                            if event.TimeGenerated > end_time:
                                continue

                            result.append(f"\nTime: {event.TimeGenerated}")
                            result.append(f"Source: {event.SourceName}")
                            result.append(f"Event ID: {event.EventID & 0xFFFFFFFF}")  # Convert to unsigned
                            result.append(
                                f"Type: {['Info', 'Warning', 'Error'][event.EventType - 1] if event.EventType <= 3 else 'Unknown'}"
                            )

                            try:
                                message = win32evtlogutil.SafeFormatMessage(event, log_type)
                                if message:
                                    result.append(f"Message: {message[:200]}...")
                            except:
                                result.append("Message: (Unable to format message)")

                            event_count += 1

                    win32evtlog.CloseEventLog(hand)
                    result.append(f"\n{log_type}: {event_count} events found")

                except Exception as e:
                    result.append(f"Error reading {log_type} log: {str(e)}")

            return "\n".join(result)

        except ImportError:
            return "Windows Event Log access requires pywin32 package."
        except ValueError as e:
            return f"Invalid time parameter: {str(e)}"
        except Exception as e:
            return f"Error accessing Windows Event Logs: {str(e)}"
