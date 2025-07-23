"""CSV log parser implementation."""

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

from ..core.models import LogRecord, LogSource, LogType
from .base import BaseParser


class CsvLogParser(BaseParser):
    """Parser for CSV log files."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize CSV parser.

        Args:
            config: Parser configuration with optional CSV-specific settings.
        """
        super().__init__(config)
        self.delimiter = self.config.get("delimiter", ",")
        self.header_row = self.config.get("header_row", 0)
        self.has_header = self.config.get("has_header", True)
        self.field_names = self.config.get("field_names", [])

    def parse_file(
        self, source: LogSource, file_path: Union[str, Path]
    ) -> Iterator[LogRecord]:
        """Parse CSV log records from a file.

        Args:
            source: The log source information.
            file_path: Path to the CSV file.

        Yields:
            LogRecord objects parsed from the CSV file.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Log file not found: {file_path}")

        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
            yield from self.parse_content(source, content)

    def parse_content(self, source: LogSource, content: str) -> Iterator[LogRecord]:
        """Parse CSV log records from content string.

        Args:
            source: The log source information.
            content: CSV content string.

        Yields:
            LogRecord objects parsed from the CSV content.
        """
        lines = content.strip().split("\n")
        reader = csv.reader(lines, delimiter=self.delimiter)

        # Handle header row
        if self.has_header:
            try:
                header = next(reader)
                field_names = header
            except StopIteration:
                return
        else:
            field_names = self.field_names or [
                f"field_{i}" for i in range(len(lines[0].split(self.delimiter)))
            ]

        # Parse data rows
        for row_num, row in enumerate(reader, start=1):
            if len(row) == 0:
                continue

            # Create record data dictionary
            record_data = {}
            for i, value in enumerate(row):
                field_name = field_names[i] if i < len(field_names) else f"field_{i}"
                record_data[field_name] = (
                    value.strip() if isinstance(value, str) else value
                )

            # Try to parse timestamp
            timestamp = self._parse_timestamp(record_data)

            # Create log record
            yield LogRecord(
                source_id=source.id,
                timestamp=timestamp,
                data=record_data,
                raw_data=self.delimiter.join(row),
            )

    def _parse_timestamp(self, record_data: Dict[str, Any]) -> Optional[datetime]:
        """Parse timestamp from record data.

        Args:
            record_data: Record data dictionary.

        Returns:
            Parsed datetime object or None.
        """
        # Try common timestamp field names
        timestamp_fields = [
            "timestamp",
            "time",
            "date",
            "datetime",
            "@timestamp",
            "created_at",
            "field_0",
        ]

        for field in timestamp_fields:
            if field in record_data:
                timestamp_str = str(record_data[field])

                # Try common timestamp formats
                formats = [
                    "%Y-%m-%d %H:%M:%S.%f",
                    "%Y-%m-%d %H:%M:%S",
                    "%Y/%m/%d %H:%M:%S",
                    "%m/%d/%Y %H:%M:%S",
                    "%d/%m/%Y %H:%M:%S",
                    "%Y-%m-%d",
                    "%m/%d/%Y",
                    "%d/%m/%Y",
                ]

                for fmt in formats:
                    try:
                        return datetime.strptime(timestamp_str, fmt)
                    except ValueError:
                        continue

        return None

    def analyze(
        self, records: List[LogRecord], analysis_type: str = "summary"
    ) -> Dict[str, Any]:
        """Analyze CSV log records.

        Args:
            records: List of log records to analyze.
            analysis_type: Type of analysis to perform.

        Returns:
            Analysis results dictionary.
        """
        if not records:
            return {
                "analysis_type": analysis_type,
                "summary": {"total_records": 0, "message": "No records to analyze"},
            }

        # Basic statistics
        total_records = len(records)
        records_with_timestamps = sum(1 for r in records if r.timestamp is not None)

        # Time range analysis
        timestamps = [r.timestamp for r in records if r.timestamp is not None]
        time_range = {}
        if timestamps:
            time_range = {
                "earliest": min(timestamps).isoformat(),
                "latest": max(timestamps).isoformat(),
                "span_hours": (max(timestamps) - min(timestamps)).total_seconds()
                / 3600,
            }

        # Field analysis
        all_fields = set()
        field_counts = {}
        for record in records:
            for field in record.data.keys():
                all_fields.add(field)
                field_counts[field] = field_counts.get(field, 0) + 1

        # Value analysis for key fields
        value_analysis = {}
        for field in list(all_fields)[:10]:  # Analyze top 10 fields
            values = [
                str(record.data.get(field, ""))
                for record in records
                if field in record.data
            ]
            unique_values = set(values)
            value_analysis[field] = {
                "total_values": len(values),
                "unique_values": len(unique_values),
                "top_values": list(
                    sorted(unique_values, key=lambda x: values.count(x), reverse=True)[
                        :5
                    ]
                ),
            }

        summary = {
            "total_records": total_records,
            "records_with_timestamps": records_with_timestamps,
            "time_range": time_range,
            "total_fields": len(all_fields),
            "field_names": list(all_fields),
            "field_coverage": field_counts,
            "value_analysis": value_analysis,
        }

        result = {"analysis_type": analysis_type, "summary": summary}

        if analysis_type == "pattern":
            result["patterns"] = self._analyze_patterns(records)
        elif analysis_type == "anomaly":
            result["anomalies"] = self._analyze_anomalies(records)

        return result

    def _analyze_patterns(self, records: List[LogRecord]) -> List[Dict[str, Any]]:
        """Analyze patterns in the log records."""
        patterns = []

        # Pattern analysis for fabric traces
        component_counts = {}
        level_counts = {}

        for record in records:
            # Analyze component patterns (assuming fabric traces format)
            if "field_4" in record.data:  # Component field
                component = record.data["field_4"]
                component_counts[component] = component_counts.get(component, 0) + 1

            if "field_1" in record.data:  # Level field
                level = record.data["field_1"]
                level_counts[level] = level_counts.get(level, 0) + 1

        if component_counts:
            patterns.append(
                {
                    "type": "component_frequency",
                    "description": "Most active components",
                    "data": dict(
                        sorted(
                            component_counts.items(), key=lambda x: x[1], reverse=True
                        )[:10]
                    ),
                }
            )

        if level_counts:
            patterns.append(
                {
                    "type": "log_level_distribution",
                    "description": "Log level distribution",
                    "data": level_counts,
                }
            )

        return patterns

    def _analyze_anomalies(self, records: List[LogRecord]) -> List[Dict[str, Any]]:
        """Analyze anomalies in the log records."""
        anomalies = []

        # Simple anomaly detection based on unusual patterns
        if len(records) > 100:
            # Check for unusual time gaps
            timestamps = [r.timestamp for r in records if r.timestamp is not None]
            if len(timestamps) > 1:
                time_diffs = [
                    (timestamps[i + 1] - timestamps[i]).total_seconds()
                    for i in range(len(timestamps) - 1)
                ]
                avg_diff = sum(time_diffs) / len(time_diffs)
                large_gaps = [diff for diff in time_diffs if diff > avg_diff * 10]

                if large_gaps:
                    anomalies.append(
                        {
                            "type": "time_gap_anomaly",
                            "description": f"Found {len(large_gaps)} unusually large time gaps",
                            "details": f"Average gap: {avg_diff:.2f}s, Max gap: {max(large_gaps):.2f}s",
                        }
                    )

        return anomalies
