"""Parser for Windows Event Logs."""

import datetime
import platform
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union
from uuid import UUID

from ..core.models import AnalysisResult, LogRecord, LogSource
from .base import BaseParser

# Only import Windows-specific modules on Windows
if platform.system() == "Windows":
    import win32evtlog
    import win32evtlogutil
    import win32api
    import win32con
    from win32con import EVENTLOG_BACKWARDS_READ, EVENTLOG_SEQUENTIAL_READ
    import pywintypes
    import xml.etree.ElementTree as ET
else:
    # Mock objects for non-Windows platforms
    win32evtlog = None
    win32evtlogutil = None
    win32api = None
    win32con = None
    pywintypes = None
    ET = None
    EVENTLOG_BACKWARDS_READ = None
    EVENTLOG_SEQUENTIAL_READ = None


class EventLogParser(BaseParser):
    """Parser for Windows Event Logs."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Windows Event Log parser.

        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        if platform.system() != "Windows":
            raise RuntimeError("Windows Event Log parser is only available on Windows")

    def parse_file(self, source: LogSource, file_path: Path) -> Iterator[LogRecord]:
        """Parse a Windows Event Log file.

        Args:
            source: The log source
            file_path: Path to the event log file

        Yields:
            LogRecord: Parsed log records
        """
        # Windows Event Logs are typically accessed by name, not file path
        # This method would need special handling for .evt/.evtx files
        raise NotImplementedError(
            "Direct file parsing not implemented for Windows Event Logs"
        )

    def parse_content(self, source: LogSource, content: str) -> Iterator[LogRecord]:
        """Parse Windows Event Log content.

        Args:
            source: The log source
            content: The log content (not used for Windows Event Logs)

        Yields:
            LogRecord: Parsed log records
        """
        # Windows Event Logs are binary and accessed via API, not text content
        raise NotImplementedError(
            "Content parsing not applicable for Windows Event Logs"
        )

    def parse(
        self,
        path: str,
        filters: Optional[Dict[str, Any]] = None,
        start_time: Optional[datetime.datetime] = None,
        end_time: Optional[datetime.datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[LogRecord]:
        """Parse Windows Event Logs.

        Args:
            path: Event log name (e.g., "System", "Application")
            filters: Optional filters
            start_time: Start time filter
            end_time: End time filter
            limit: Maximum number of records
            offset: Number of records to skip

        Returns:
            List of parsed log records
        """
        if platform.system() != "Windows":
            return []

        records = []

        # Handle both standard logs (System, Application) and custom logs
        # Custom logs like "Microsoft-Service Fabric/Admin" need the newer API
        if "/" in path or "\\" in path:
            # This is a custom Application and Services log - use newer EvtQuery API
            records = self._parse_custom_event_log(
                path, filters, start_time, end_time, limit, offset
            )
        else:
            # Standard log - use legacy API
            try:
                hand = win32evtlog.OpenEventLog(None, path)
                flags = EVENTLOG_BACKWARDS_READ | EVENTLOG_SEQUENTIAL_READ

                # Continue reading until we have enough records
                events_read = 0
                while len(records) < limit:
                    events = win32evtlog.ReadEventLog(hand, flags, 0)
                    if not events:
                        break  # No more events to read

                    for event in events:
                        if events_read >= offset:
                            record = self._parse_event(event, path)
                            if self._matches_filters(
                                record, filters, start_time, end_time
                            ):
                                records.append(record)
                                if len(records) >= limit:
                                    break
                        events_read += 1

                win32evtlog.CloseEventLog(hand)

            except Exception as e:
                # Log error or handle appropriately
                print(f"Error parsing Windows Event Log '{path}': {str(e)}")
                pass

        return records

    def analyze(
        self, logs: List[LogRecord], analysis_type: str = "summary"
    ) -> AnalysisResult:
        """Analyze Windows Event Logs.

        Args:
            logs: List of log records to analyze
            analysis_type: Type of analysis to perform

        Returns:
            Analysis result
        """
        if analysis_type == "summary":
            return self._summary_analysis(logs)
        elif analysis_type == "pattern":
            return self._pattern_analysis(logs)
        elif analysis_type == "anomaly":
            return self._anomaly_analysis(logs)
        else:
            raise ValueError(f"Unknown analysis type: {analysis_type}")

    def _parse_custom_event_log(
        self,
        path: str,
        filters: Optional[Dict[str, Any]],
        start_time: Optional[datetime.datetime],
        end_time: Optional[datetime.datetime],
        limit: int,
        offset: int,
    ) -> List[LogRecord]:
        """Parse custom Application and Services logs using the newer Windows Event Log API."""
        records = []

        try:
            # Build query for the custom log
            query_flags = (
                win32evtlog.EvtQueryChannelPath | win32evtlog.EvtQueryReverseDirection
            )

            # Build XPath query if we have filters
            xpath_query = "*"
            if filters or start_time or end_time:
                conditions = []

                if start_time:
                    # Convert to Windows file time format
                    start_ms = int(start_time.timestamp() * 1000)
                    conditions.append(f"TimeCreated[@SystemTime >= '{start_ms}']")

                if end_time:
                    end_ms = int(end_time.timestamp() * 1000)
                    conditions.append(f"TimeCreated[@SystemTime <= '{end_ms}']")

                if filters and "EventID" in filters:
                    conditions.append(f"EventID={filters['EventID']}")

                if conditions:
                    xpath_query = f"*[System[{' and '.join(conditions)}]]"

            # Query the event log
            query_handle = win32evtlog.EvtQuery(path, query_flags, xpath_query)

            # Read events
            events_read = 0
            while len(records) < limit:
                # Get batch of events
                events = win32evtlog.EvtNext(query_handle, 10)  # Read 10 at a time
                if not events:
                    break

                for event in events:
                    if events_read >= offset:
                        # Render event as XML to extract data
                        xml_content = win32evtlog.EvtRender(
                            event, win32evtlog.EvtRenderEventXml
                        )
                        record = self._parse_event_xml(xml_content, path)

                        if self._matches_filters(record, filters, start_time, end_time):
                            records.append(record)
                            if len(records) >= limit:
                                break

                    events_read += 1
                    win32evtlog.EvtClose(event)

            win32evtlog.EvtClose(query_handle)

        except Exception as e:
            print(f"Error parsing custom event log '{path}': {str(e)}")
            # Fall back to empty list if the API is not available or fails
            pass

        return records

    def _parse_event_xml(self, xml_content: str, log_name: str) -> LogRecord:
        """Parse event data from XML format."""
        try:
            root = ET.fromstring(xml_content)

            # Extract system data
            system = root.find(".//System")
            event_id = (
                int(system.find("EventID").text)
                if system.find("EventID") is not None
                else 0
            )

            # Handle unsigned conversion
            event_id = event_id & 0xFFFFFFFF

            provider = system.find("Provider")
            provider_name = (
                provider.get("Name", "Unknown") if provider is not None else "Unknown"
            )

            computer = system.find("Computer")
            computer_name = computer.text if computer is not None else "Unknown"

            time_created = system.find("TimeCreated")
            if time_created is not None:
                system_time = time_created.get("SystemTime", "")
                # Parse ISO format timestamp
                try:
                    timestamp = datetime.datetime.fromisoformat(
                        system_time.replace("Z", "+00:00")
                    )
                except:
                    timestamp = datetime.datetime.now()
            else:
                timestamp = datetime.datetime.now()

            level = system.find("Level")
            event_type = (
                int(level.text) if level is not None else 4
            )  # Default to Information

            # Map levels to event types (1=Error, 2=Warning, 4=Information)
            level_map = {
                1: 2,
                2: 3,
                3: 4,
                4: 4,
                5: 4,
            }  # Critical=1, Error=2, Warning=3, Info=4, Verbose=5
            event_type = level_map.get(event_type, 4)

            # Extract event data
            event_data = {}
            data_elem = root.find(".//EventData")
            if data_elem is not None:
                for data in data_elem:
                    name = data.get("Name", "")
                    if name:
                        event_data[name] = data.text or ""

            # Try to get rendered message
            message = ""
            rendering = root.find(".//RenderingInfo/Message")
            if rendering is not None:
                message = rendering.text or ""
            else:
                # Build message from event data
                if event_data:
                    message = "; ".join(f"{k}: {v}" for k, v in event_data.items())

            return LogRecord(
                source_id=UUID("00000000-0000-0000-0000-000000000000"),
                timestamp=timestamp,
                data={
                    "EventID": event_id,
                    "EventType": event_type,
                    "EventCategory": 0,  # Not available in new API
                    "SourceName": provider_name,
                    "ComputerName": computer_name,
                    "Message": message,
                    "EventData": event_data,
                    "LogName": log_name,
                },
            )

        except Exception as e:
            print(f"Error parsing event XML: {str(e)}")
            # Return a basic record on error
            return LogRecord(
                source_id=UUID("00000000-0000-0000-0000-000000000000"),
                timestamp=datetime.datetime.now(),
                data={
                    "EventID": 0,
                    "EventType": 4,
                    "EventCategory": 0,
                    "SourceName": "Unknown",
                    "ComputerName": "Unknown",
                    "Message": f"Error parsing event: {str(e)}",
                    "LogName": log_name,
                },
            )

    def _parse_event(self, event, log_name: str = None) -> LogRecord:
        """Parse a single Windows event."""
        try:
            message = win32evtlogutil.SafeFormatMessage(event, log_name)
        except:
            message = "(Unable to format message)"

        return LogRecord(
            source_id=UUID("00000000-0000-0000-0000-000000000000"),  # Placeholder
            timestamp=event.TimeGenerated,
            data={
                "EventID": event.EventID & 0xFFFFFFFF,  # Convert to unsigned
                "EventType": event.EventType,
                "EventCategory": event.EventCategory,
                "SourceName": event.SourceName,
                "ComputerName": event.ComputerName,
                "Message": message,
            },
        )

    def _matches_filters(
        self,
        record: LogRecord,
        filters: Optional[Dict[str, Any]],
        start_time: Optional[datetime.datetime],
        end_time: Optional[datetime.datetime],
    ) -> bool:
        """Check if a record matches the given filters."""
        if start_time and record.timestamp and record.timestamp < start_time:
            return False
        if end_time and record.timestamp and record.timestamp > end_time:
            return False

        if filters:
            for key, value in filters.items():
                if key in record.data and record.data[key] != value:
                    return False

        return True

    def _summary_analysis(self, logs: List[LogRecord]) -> AnalysisResult:
        """Perform summary analysis."""
        event_types = {}
        sources = {}

        for log in logs:
            event_type = log.data.get("EventType", "Unknown")
            event_types[event_type] = event_types.get(event_type, 0) + 1

            source = log.data.get("SourceName", "Unknown")
            sources[source] = sources.get(source, 0) + 1

        return AnalysisResult(
            analysis_type="summary",
            summary={
                "total_events": len(logs),
                "event_types": event_types,
                "sources": sources,
            },
        )

    def _pattern_analysis(self, logs: List[LogRecord]) -> AnalysisResult:
        """Perform pattern analysis."""
        # Simplified pattern analysis
        patterns = []

        # Group by EventID
        event_groups = {}
        for log in logs:
            event_id = log.data.get("EventID", "Unknown")
            if event_id not in event_groups:
                event_groups[event_id] = []
            event_groups[event_id].append(log)

        for event_id, events in event_groups.items():
            if len(events) > 1:
                patterns.append(
                    {
                        "pattern": f"EventID {event_id}",
                        "count": len(events),
                        "frequency": len(events) / len(logs),
                    }
                )

        return AnalysisResult(
            analysis_type="pattern",
            summary={"total_patterns": len(patterns)},
            patterns=patterns,
        )

    def _anomaly_analysis(self, logs: List[LogRecord]) -> AnalysisResult:
        """Perform anomaly analysis."""
        # Simplified anomaly detection
        anomalies = []

        # Look for error events
        for log in logs:
            if log.data.get("EventType") == 1:  # Error
                anomalies.append(
                    {
                        "type": "error_event",
                        "event_id": log.data.get("EventID"),
                        "source": log.data.get("SourceName"),
                        "message": log.data.get("Message", "")[:100],
                    }
                )

        return AnalysisResult(
            analysis_type="anomaly",
            summary={"total_anomalies": len(anomalies)},
            anomalies=anomalies,
        )


# For backward compatibility
EvtParser = EventLogParser
