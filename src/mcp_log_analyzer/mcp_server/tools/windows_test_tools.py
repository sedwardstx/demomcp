"""
Windows Event Log testing and diagnostic MCP tools.
"""

from typing import Any, Dict

from mcp.server import FastMCP
from pydantic import BaseModel, Field


class WindowsEventLogTestRequest(BaseModel):
    """Request model for testing Windows Event Log access."""

    log_name: str = Field(
        "System", description="Event log name to test (System, Application, Security)"
    )
    max_entries: int = Field(10, description="Maximum number of entries to fetch")


class WindowsEventLogQueryRequest(BaseModel):
    """Request model for querying Windows Event Logs."""

    log_name: str = Field("System", description="Event log name to query")
    event_id: int = Field(None, description="Specific Event ID to filter by")
    level: str = Field(None, description="Event level (Error, Warning, Information)")
    time_duration: str = Field(
        "1h", description="Time duration (e.g., '30m', '2h', '1d')"
    )
    max_entries: int = Field(50, description="Maximum number of entries to return")


def register_windows_test_tools(mcp: FastMCP):
    """Register all Windows testing tools with the MCP server."""

    @mcp.tool()
    async def test_windows_event_log_access() -> Dict[str, Any]:
        """
        Test Windows Event Log access and permissions.

        This tool checks if the system can access Windows Event Logs
        and provides diagnostic information about available logs.
        """
        import platform

        if platform.system() != "Windows":
            return {
                "status": "unavailable",
                "message": "Windows Event Logs are only available on Windows systems",
                "platform": platform.system(),
            }

        try:
            import win32evtlog

            # Test access to common event logs
            test_results = {}
            common_logs = ["System", "Application", "Security"]

            for log_name in common_logs:
                try:
                    hand = win32evtlog.OpenEventLog(None, log_name)
                    win32evtlog.CloseEventLog(hand)
                    test_results[log_name] = {"accessible": True, "error": None}
                except Exception as e:
                    test_results[log_name] = {"accessible": False, "error": str(e)}

            return {
                "status": "available",
                "message": "Windows Event Log access test completed",
                "log_access": test_results,
                "pywin32_available": True,
            }

        except ImportError:
            return {
                "status": "missing_dependencies",
                "message": "pywin32 package is required for Windows Event Log access",
                "pywin32_available": False,
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error testing Windows Event Log access: {str(e)}",
            }

    @mcp.tool()
    async def get_windows_event_log_info(
        request: WindowsEventLogTestRequest,
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific Windows Event Log.

        This tool provides metadata and recent entries from the specified
        Windows Event Log for diagnostic purposes.
        """
        import platform

        if platform.system() != "Windows":
            return {"error": "This tool is only available on Windows systems"}

        try:
            import win32evtlog
            import win32evtlogutil
            from win32con import EVENTLOG_BACKWARDS_READ, EVENTLOG_SEQUENTIAL_READ

            hand = win32evtlog.OpenEventLog(None, request.log_name)

            # Get log information
            try:
                num_records = win32evtlog.GetNumberOfEventLogRecords(hand)
                oldest_record = win32evtlog.GetOldestEventLogRecord(hand)
                info = (oldest_record, num_records)
            except:
                info = None

            # Get recent entries
            flags = EVENTLOG_BACKWARDS_READ | EVENTLOG_SEQUENTIAL_READ

            entries = []
            count = 0

            while count < request.max_entries:
                events = win32evtlog.ReadEventLog(hand, flags, 0)
                if not events:
                    break  # No more events to read

                for event in events:
                    if count >= request.max_entries:
                        break

                    try:
                        message = win32evtlogutil.SafeFormatMessage(
                            event, request.log_name
                        )
                    except:
                        message = "(Unable to format message)"

                    entries.append(
                        {
                            "event_id": event.EventID
                            & 0xFFFFFFFF,  # Convert to unsigned
                            "time_generated": str(event.TimeGenerated),
                            "source_name": event.SourceName,
                            "event_type": event.EventType,
                            "message_preview": message[:200] if message else "",
                        }
                    )
                    count += 1

            win32evtlog.CloseEventLog(hand)

            return {
                "log_name": request.log_name,
                "log_info": {
                    "oldest_record_number": info[0] if info else "Unknown",
                    "total_records": info[1] if info else "Unknown",
                },
                "recent_entries": entries,
                "entries_retrieved": len(entries),
                "max_requested": request.max_entries,
            }

        except ImportError:
            return {"error": "pywin32 package is required for Windows Event Log access"}
        except Exception as e:
            return {"error": f"Error accessing Windows Event Log: {str(e)}"}

    @mcp.tool()
    async def query_windows_events_by_criteria(
        request: WindowsEventLogQueryRequest,
    ) -> Dict[str, Any]:
        """
        Query Windows Event Logs with specific criteria.

        This tool allows filtering Windows Event Logs by Event ID,
        level, and time range for targeted analysis.
        """
        import platform

        if platform.system() != "Windows":
            return {"error": "This tool is only available on Windows systems"}

        try:
            import win32evtlog
            import win32evtlogutil
            from win32con import EVENTLOG_BACKWARDS_READ, EVENTLOG_SEQUENTIAL_READ
            import xml.etree.ElementTree as ET
            from datetime import datetime

            from ..server import parse_time_param

            # Parse time duration
            if request.time_duration:
                start_time = parse_time_param(request.time_duration)
            else:
                start_time = None

            matching_events = []
            count = 0
            total_checked = 0
            level_map = {1: "Error", 2: "Warning", 4: "Information"}

            # Check if this is a custom Application and Services log
            if "/" in request.log_name or "\\" in request.log_name:
                # Use newer EvtQuery API for custom logs
                try:
                    query_flags = (
                        win32evtlog.EvtQueryChannelPath
                        | win32evtlog.EvtQueryReverseDirection
                    )

                    # Build XPath query
                    conditions = []
                    if start_time:
                        start_ms = int(start_time.timestamp() * 1000)
                        conditions.append(f"TimeCreated[@SystemTime >= '{start_ms}']")
                    if request.event_id:
                        conditions.append(f"EventID={request.event_id}")
                    if request.level:
                        level_num = {"error": 2, "warning": 3, "information": 4}.get(
                            request.level.lower(), 0
                        )
                        if level_num:
                            conditions.append(f"Level={level_num}")

                    xpath_query = "*"
                    if conditions:
                        xpath_query = f"*[System[{' and '.join(conditions)}]]"

                    query_handle = win32evtlog.EvtQuery(
                        request.log_name, query_flags, xpath_query
                    )

                    while count < request.max_entries:
                        events = win32evtlog.EvtNext(query_handle, 10)
                        if not events:
                            break

                        for event in events:
                            total_checked += 1

                            # Render event as XML
                            xml_content = win32evtlog.EvtRender(
                                event, win32evtlog.EvtRenderEventXml
                            )

                            # Parse XML to extract event data
                            root = ET.fromstring(xml_content)
                            system = root.find(".//System")

                            event_id = (
                                int(system.find("EventID").text)
                                if system.find("EventID") is not None
                                else 0
                            )
                            event_id = event_id & 0xFFFFFFFF

                            provider = system.find("Provider")
                            source_name = (
                                provider.get("Name", "Unknown")
                                if provider is not None
                                else "Unknown"
                            )

                            time_created = system.find("TimeCreated")
                            if time_created is not None:
                                time_str = time_created.get(
                                    "SystemTime", str(datetime.now())
                                )
                            else:
                                time_str = str(datetime.now())

                            level = system.find("Level")
                            event_type = int(level.text) if level is not None else 4

                            # Extract message
                            message = ""
                            event_data = root.find(".//EventData")
                            if event_data is not None:
                                data_items = []
                                for data in event_data:
                                    name = data.get("Name", "")
                                    value = data.text or ""
                                    if name:
                                        data_items.append(f"{name}: {value}")
                                message = "; ".join(data_items)

                            matching_events.append(
                                {
                                    "event_id": event_id,
                                    "time_generated": time_str,
                                    "source_name": source_name,
                                    "event_type": event_type,
                                    "level": level_map.get(event_type, "Unknown"),
                                    "message": message[:500] if message else "",
                                }
                            )

                            count += 1
                            win32evtlog.EvtClose(event)

                            if count >= request.max_entries:
                                break

                    win32evtlog.EvtClose(query_handle)

                except Exception as e:
                    return {"error": f"Error querying custom event log: {str(e)}"}
            else:
                # Use legacy API for standard logs
                hand = win32evtlog.OpenEventLog(None, request.log_name)
                flags = EVENTLOG_BACKWARDS_READ | EVENTLOG_SEQUENTIAL_READ

                # Continue reading until we have enough matching events or no more events
                while count < request.max_entries:
                    events = win32evtlog.ReadEventLog(hand, flags, 0)
                    if not events:
                        break  # No more events to read

                    for event in events:
                        total_checked += 1

                        # Check time filter
                        if start_time and event.TimeGenerated < start_time:
                            continue

                        # Check Event ID filter
                        # Handle both signed and unsigned Event ID comparisons
                        if request.event_id:
                            # Convert to unsigned 32-bit for comparison
                            event_id_unsigned = event.EventID & 0xFFFFFFFF
                            if (
                                event_id_unsigned != request.event_id
                                and event.EventID != request.event_id
                            ):
                                continue

                        # Check level filter (simplified mapping)
                        if request.level:
                            event_level = level_map.get(event.EventType, "Unknown")
                            if event_level.lower() != request.level.lower():
                                continue

                        # Event matches all criteria
                        try:
                            message = win32evtlogutil.SafeFormatMessage(
                                event, request.log_name
                            )
                        except:
                            message = "(Unable to format message)"

                        matching_events.append(
                            {
                                "event_id": event.EventID
                                & 0xFFFFFFFF,  # Convert to unsigned
                                "time_generated": str(event.TimeGenerated),
                                "source_name": event.SourceName,
                                "event_type": event.EventType,
                                "level": level_map.get(event.EventType, "Unknown"),
                                "message": message[:500] if message else "",
                            }
                        )

                        count += 1
                        if count >= request.max_entries:
                            break

                win32evtlog.CloseEventLog(hand)

            return {
                "log_name": request.log_name,
                "query_criteria": {
                    "event_id": request.event_id,
                    "level": request.level,
                    "time_duration": request.time_duration,
                    "start_time": str(start_time) if start_time else None,
                },
                "matching_events": matching_events,
                "total_matches": len(matching_events),
                "total_events_checked": total_checked,
                "max_requested": request.max_entries,
            }

        except ImportError:
            return {"error": "pywin32 package is required for Windows Event Log access"}
        except Exception as e:
            return {"error": f"Error querying Windows Event Logs: {str(e)}"}

    @mcp.tool()
    async def get_windows_system_health() -> Dict[str, Any]:
        """
        Get Windows system health overview from Event Logs.

        This tool analyzes recent System and Application event logs
        to provide a quick health assessment of the Windows system.
        """
        import platform

        if platform.system() != "Windows":
            return {"error": "This tool is only available on Windows systems"}

        try:
            from datetime import datetime, timedelta

            import win32evtlog
            import win32evtlogutil
            from win32con import EVENTLOG_BACKWARDS_READ, EVENTLOG_SEQUENTIAL_READ

            # Check last 24 hours
            start_time = datetime.now() - timedelta(hours=24)

            health_summary = {"errors": 0, "warnings": 0, "critical_events": []}

            for log_name in ["System", "Application"]:
                try:
                    hand = win32evtlog.OpenEventLog(None, log_name)
                    flags = EVENTLOG_BACKWARDS_READ | EVENTLOG_SEQUENTIAL_READ

                    log_errors = 0
                    log_warnings = 0
                    done_reading = False

                    while not done_reading:
                        events = win32evtlog.ReadEventLog(hand, flags, 0)
                        if not events:
                            break  # No more events to read

                        for event in events:
                            if event.TimeGenerated < start_time:
                                done_reading = True
                                break

                            if event.EventType == 1:  # Error
                                log_errors += 1
                                if log_errors <= 5:  # Capture first 5 errors
                                    try:
                                        message = win32evtlogutil.SafeFormatMessage(
                                            event, log_name
                                        )
                                    except:
                                        message = "Unable to format message"

                                    health_summary["critical_events"].append(
                                        {
                                            "log": log_name,
                                            "type": "Error",
                                            "event_id": event.EventID
                                            & 0xFFFFFFFF,  # Convert to unsigned
                                            "source": event.SourceName,
                                            "time": str(event.TimeGenerated),
                                            "message": message[:200],
                                        }
                                    )

                            elif event.EventType == 2:  # Warning
                                log_warnings += 1

                    health_summary["errors"] += log_errors
                    health_summary["warnings"] += log_warnings

                    win32evtlog.CloseEventLog(hand)

                except Exception as e:
                    health_summary[f"{log_name}_error"] = str(e)

            # Determine overall health status
            if health_summary["errors"] == 0 and health_summary["warnings"] < 5:
                status = "healthy"
            elif health_summary["errors"] < 3 and health_summary["warnings"] < 20:
                status = "fair"
            else:
                status = "concerning"

            return {
                "time_period": "Last 24 hours",
                "overall_status": status,
                "summary": {
                    "total_errors": health_summary["errors"],
                    "total_warnings": health_summary["warnings"],
                },
                "critical_events": health_summary["critical_events"],
                "timestamp": str(datetime.now()),
            }

        except ImportError:
            return {"error": "pywin32 package is required for Windows Event Log access"}
        except Exception as e:
            return {"error": f"Error analyzing Windows system health: {str(e)}"}
