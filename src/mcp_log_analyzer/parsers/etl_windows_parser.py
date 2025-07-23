"""Windows ETL parser using native Windows tools as fallback."""

import json
import os
import platform
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union
from uuid import uuid4

from ..core.models import LogRecord, LogSource, LogType
from .base import BaseParser


class EtlWindowsParser(BaseParser):
    """ETL parser using Windows native tools (tracerpt.exe)."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Windows ETL parser.

        Args:
            config: Parser configuration.
        """
        super().__init__(config)
        self.use_tracerpt = self.config.get("use_tracerpt", True)
        self.tracerpt_path = self._find_tracerpt()

    def _find_tracerpt(self) -> Optional[str]:
        """Find tracerpt.exe on the system."""
        if platform.system() != "Windows":
            return None

        # Common locations for tracerpt.exe
        possible_paths = [
            r"C:\Windows\System32\tracerpt.exe",
            r"C:\Windows\SysWOW64\tracerpt.exe",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        # Try to find it in PATH
        try:
            result = subprocess.run(
                ["where", "tracerpt.exe"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split('\n')[0]
        except:
            pass

        return None

    def is_available(self) -> bool:
        """Check if Windows ETL parsing is available."""
        return self.tracerpt_path is not None

    def parse_file(
        self, source: LogSource, file_path: Union[str, Path]
    ) -> Iterator[LogRecord]:
        """Parse ETL log records using Windows tracerpt.

        Args:
            source: The log source information.
            file_path: Path to the ETL file.

        Yields:
            LogRecord objects parsed from the ETL file.
        """
        if not self.is_available():
            raise RuntimeError(
                "Windows ETL parsing is not available. tracerpt.exe not found."
            )

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"ETL file not found: {file_path}")

        if not str(path).lower().endswith('.etl'):
            raise ValueError(f"File does not appear to be an ETL file: {file_path}")

        # Create temporary directory for output
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "output.csv")
            
            try:
                # Run tracerpt to convert ETL to CSV
                cmd = [
                    self.tracerpt_path,
                    str(path),
                    "-o", output_file,
                    "-of", "CSV",
                    "-y"  # Overwrite without prompting
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                if result.returncode != 0:
                    raise RuntimeError(
                        f"tracerpt failed with code {result.returncode}: {result.stderr}"
                    )
                
                # Parse the CSV output
                if os.path.exists(output_file):
                    with open(output_file, 'r', encoding='utf-8', errors='ignore') as f:
                        import csv
                        reader = csv.DictReader(f)
                        
                        for row in reader:
                            log_record = self._convert_csv_row(source, row)
                            if log_record:
                                yield log_record
                                
            except subprocess.TimeoutExpired:
                raise RuntimeError("tracerpt timed out after 5 minutes")
            except Exception as e:
                raise RuntimeError(f"Failed to parse ETL file: {e}")

    def _convert_csv_row(self, source: LogSource, row: Dict[str, str]) -> Optional[LogRecord]:
        """Convert a CSV row from tracerpt to a LogRecord.

        Args:
            source: The log source information.
            row: CSV row dictionary.

        Returns:
            LogRecord or None if conversion fails.
        """
        try:
            # Common tracerpt CSV columns
            record_data = {}
            
            # Map known columns
            field_mappings = {
                "Event Name": "event_name",
                "Type": "event_type",
                "Event ID": "event_id",
                "Version": "version",
                "Channel": "channel",
                "Level": "level",
                "Task": "task",
                "Opcode": "opcode",
                "Keyword": "keywords",
                "PID": "process_id",
                "TID": "thread_id",
                "Processor Number": "processor",
                "Instance ID": "instance_id",
                "Parent Instance ID": "parent_instance_id",
                "Activity ID": "activity_id",
                "Related Activity ID": "related_activity_id",
                "Provider Name": "provider_name",
                "Provider ID": "provider_id",
                "Message": "message",
                "Process Name": "process_name",
            }
            
            for csv_field, record_field in field_mappings.items():
                if csv_field in row and row[csv_field]:
                    record_data[record_field] = row[csv_field]
            
            # Try to parse timestamp
            timestamp = None
            if "Clock-Time" in row:
                try:
                    timestamp = datetime.strptime(
                        row["Clock-Time"], 
                        "%Y-%m-%d %H:%M:%S.%f"
                    )
                except:
                    pass
            
            # Include any additional fields
            for key, value in row.items():
                if key not in field_mappings and value:
                    # Clean up field name
                    clean_key = key.lower().replace(' ', '_').replace('-', '_')
                    record_data[clean_key] = value
            
            return LogRecord(
                source_id=source.id,
                timestamp=timestamp,
                data=record_data,
                raw_content=None  # CSV rows are already processed
            )
            
        except Exception as e:
            if self.config.get("verbose", False):
                print(f"Failed to convert CSV row: {e}")
            return None

    def parse_content(self, source: LogSource, content: str) -> Iterator[LogRecord]:
        """Parse ETL log records from content string.

        Note: ETL files are binary and cannot be parsed from string content.

        Args:
            source: The log source information.
            content: String content (not supported for ETL).

        Raises:
            NotImplementedError: ETL files must be parsed from file.
        """
        raise NotImplementedError(
            "ETL files are binary and must be parsed from file, not string content"
        )

    def validate_file(self, file_path: Union[str, Path]) -> bool:
        """Validate if the file can be parsed by this parser.

        Args:
            file_path: Path to validate.

        Returns:
            True if file appears to be an ETL file.
        """
        path = Path(file_path)
        
        # Check file extension
        if not str(path).lower().endswith('.etl'):
            return False
            
        # Check if file exists and is readable
        if not path.exists() or not path.is_file():
            return False
            
        # Check if we have tracerpt available
        if not self.is_available():
            return False
            
        return True

    def parse(
        self, path: str, filters: Optional[Dict[str, Any]] = None,
        start_time: Optional[datetime] = None, end_time: Optional[datetime] = None,
        limit: int = 1000, offset: int = 0
    ) -> List[LogRecord]:
        """Parse ETL file with filtering and pagination.

        Args:
            path: Path to the ETL file.
            filters: Optional filters to apply.
            start_time: Optional start time filter.
            end_time: Optional end time filter.
            limit: Maximum number of records to return.
            offset: Number of records to skip.

        Returns:
            List of LogRecord objects.
        """
        # Create a temporary log source for parsing
        temp_source = LogSource(
            name="temp_etl",
            type=LogType.ETL,
            path=path,
            metadata={}
        )

        records = []
        skipped = 0
        
        for record in self.parse_file(temp_source, path):
            # Apply time filters
            if start_time and record.timestamp and record.timestamp < start_time:
                continue
            if end_time and record.timestamp and record.timestamp > end_time:
                continue
                
            # Apply custom filters
            if filters:
                if not self._match_filters(record, filters):
                    continue
            
            # Handle pagination
            if skipped < offset:
                skipped += 1
                continue
                
            records.append(record)
            
            if len(records) >= limit:
                break
                
        return records

    def _match_filters(self, record: LogRecord, filters: Dict[str, Any]) -> bool:
        """Check if a record matches the provided filters.

        Args:
            record: The log record to check.
            filters: Dictionary of filters to apply.

        Returns:
            True if record matches all filters.
        """
        for key, value in filters.items():
            record_value = record.data.get(key)
            
            if isinstance(value, list):
                if record_value not in value:
                    return False
            else:
                if record_value != value:
                    return False
                    
        return True