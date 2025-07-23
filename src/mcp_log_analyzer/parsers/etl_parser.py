"""Windows ETL (Event Trace Log) file parser implementation."""

import os
import platform
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union
from uuid import uuid4

from ..core.models import LogRecord, LogSource, LogType
from .base import BaseParser


class EtlParser(BaseParser):
    """Parser for Windows ETL (Event Trace Log) files."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize ETL parser.

        Args:
            config: Parser configuration.
        """
        super().__init__(config)
        self.etl_parser = None
        self.windows_parser = None
        self._init_parser()

    def _init_parser(self):
        """Initialize the ETL parser library."""
        try:
            # Try to import etl-parser library
            import etl_parser
            self.etl_parser = etl_parser
        except ImportError:
            self.etl_parser = None
            # Try to use Windows native parser as fallback
            try:
                from .etl_windows_parser import EtlWindowsParser
                self.windows_parser = EtlWindowsParser()
                if not self.windows_parser.is_available():
                    self.windows_parser = None
            except:
                self.windows_parser = None

    def is_available(self) -> bool:
        """Check if ETL parsing is available."""
        return self.etl_parser is not None or self.windows_parser is not None

    def parse_file(
        self, source: LogSource, file_path: Union[str, Path]
    ) -> Iterator[LogRecord]:
        """Parse ETL log records from a file.

        Args:
            source: The log source information.
            file_path: Path to the ETL file.

        Yields:
            LogRecord objects parsed from the ETL file.
        """
        if not self.is_available():
            raise RuntimeError(
                "ETL parsing is not available. Please install etl-parser: pip install etl-parser "
                "or ensure tracerpt.exe is available on Windows."
            )

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"ETL file not found: {file_path}")

        if not str(path).lower().endswith('.etl'):
            raise ValueError(f"File does not appear to be an ETL file: {file_path}")
        
        # Always try cached parser first for better performance
        try:
            from .etl_cached_parser import EtlCachedParser
            cached_parser = EtlCachedParser(self.config)
            if cached_parser.is_available():
                yield from cached_parser.parse_file(source, file_path)
                return
        except Exception as e:
            # Fall back to streaming parser for large files
            file_size_mb = path.stat().st_size / (1024 * 1024)
            if file_size_mb > 50:  # Use streaming parser for files > 50MB
                try:
                    from .etl_large_file_parser import EtlLargeFileParser
                    large_parser = EtlLargeFileParser(self.config)
                    if large_parser.is_available():
                        yield from large_parser.parse_file(source, file_path)
                        return
                except Exception as e:
                    # Fall back to regular parsing
                    pass

        # Try etl-parser first if available
        if self.etl_parser is not None:
            try:
                # Create an ETL parser instance
                from etl_parser import ETL, ETLParser, build_from_stream
                
                # Parse the ETL file
                with open(path, 'rb') as etl_file:
                    parser = ETLParser(etl_file)
                    
                    # Process all records in the ETL file
                    for record in parser:
                        # Convert ETL record to LogRecord
                        log_record = self._convert_etl_record(source, record)
                        if log_record:
                            yield log_record
                return  # Success, exit
            except Exception as e:
                # If etl-parser fails, try Windows parser
                if self.windows_parser is None:
                    raise RuntimeError(f"Failed to parse ETL file: {e}")
        
        # Fall back to Windows native parser
        if self.windows_parser is not None:
            try:
                yield from self.windows_parser.parse_file(source, file_path)
            except Exception as e:
                raise RuntimeError(f"Failed to parse ETL file with Windows parser: {e}")
        else:
            raise RuntimeError("No ETL parser available")

    def _convert_etl_record(self, source: LogSource, etl_record: Any) -> Optional[LogRecord]:
        """Convert an ETL record to a LogRecord.

        Args:
            source: The log source information.
            etl_record: The ETL record from etl-parser.

        Returns:
            LogRecord or None if conversion fails.
        """
        try:
            # Extract common fields from ETL record
            record_data = {
                "provider_name": getattr(etl_record, "provider_name", "Unknown"),
                "event_id": getattr(etl_record, "event_id", 0),
                "level": getattr(etl_record, "level", 0),
                "task": getattr(etl_record, "task", 0),
                "opcode": getattr(etl_record, "opcode", 0),
                "keywords": getattr(etl_record, "keywords", 0),
                "process_id": getattr(etl_record, "process_id", 0),
                "thread_id": getattr(etl_record, "thread_id", 0),
            }

            # Try to get timestamp
            timestamp = None
            if hasattr(etl_record, "system_time"):
                timestamp = etl_record.system_time
            elif hasattr(etl_record, "timestamp"):
                timestamp = etl_record.timestamp

            # Try to get event data
            if hasattr(etl_record, "user_data"):
                record_data["user_data"] = etl_record.user_data
            elif hasattr(etl_record, "event_data"):
                record_data["event_data"] = etl_record.event_data

            # Add any extended data
            if hasattr(etl_record, "extended_data"):
                record_data["extended_data"] = etl_record.extended_data

            # Create LogRecord
            return LogRecord(
                source_id=source.id,
                timestamp=timestamp,
                data=record_data,
                raw_content=str(etl_record) if self.config.get("include_raw", False) else None
            )

        except Exception as e:
            # Log error but continue processing
            if self.config.get("verbose", False):
                print(f"Failed to convert ETL record: {e}")
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
            
        # Check if we have any parser available
        if not self.is_available():
            return False
            
        # Could add binary file signature check here
        # ETL files typically start with specific magic bytes
        
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
            
            # Handle different filter types
            if isinstance(value, list):
                # Match any value in list
                if record_value not in value:
                    return False
            elif isinstance(value, dict):
                # Handle complex filters (e.g., {"$gte": 4} for level >= 4)
                if not self._match_complex_filter(record_value, value):
                    return False
            else:
                # Exact match
                if record_value != value:
                    return False
                    
        return True

    def _match_complex_filter(self, value: Any, filter_spec: Dict[str, Any]) -> bool:
        """Match a value against a complex filter specification.

        Args:
            value: The value to check.
            filter_spec: Dictionary with filter operators.

        Returns:
            True if value matches the filter.
        """
        for op, filter_value in filter_spec.items():
            if op == "$gte" and not (value >= filter_value):
                return False
            elif op == "$gt" and not (value > filter_value):
                return False
            elif op == "$lte" and not (value <= filter_value):
                return False
            elif op == "$lt" and not (value < filter_value):
                return False
            elif op == "$ne" and not (value != filter_value):
                return False
            elif op == "$in" and value not in filter_value:
                return False
            elif op == "$nin" and value in filter_value:
                return False
                
        return True