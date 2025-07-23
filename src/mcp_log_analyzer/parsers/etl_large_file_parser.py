"""Enhanced ETL parser for large files with streaming support."""

import asyncio
import os
import platform
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union
from uuid import uuid4
import csv
import logging

from ..core.models import LogRecord, LogSource, LogType
from .base import BaseParser

logger = logging.getLogger(__name__)


class EtlLargeFileParser(BaseParser):
    """Enhanced ETL parser with support for large files using streaming."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize ETL large file parser.

        Args:
            config: Parser configuration.
        """
        super().__init__(config)
        self.chunk_size = self.config.get("chunk_size", 1000)  # Records per chunk
        self.tracerpt_path = self._find_tracerpt()
        self.temp_dir = None

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
        """Check if ETL parsing is available."""
        return self.tracerpt_path is not None

    def parse_file_streaming(
        self, source: LogSource, file_path: Union[str, Path], 
        limit: int = 1000, offset: int = 0
    ) -> Iterator[LogRecord]:
        """Parse ETL file with streaming to handle large files.

        Args:
            source: The log source information.
            file_path: Path to the ETL file.
            limit: Maximum number of records to return.
            offset: Number of records to skip.

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

        # Get file size for logging
        file_size_mb = path.stat().st_size / (1024 * 1024)
        logger.info(f"Processing ETL file: {file_size_mb:.1f} MB")

        # Create a persistent temp directory if not exists
        if self.temp_dir is None:
            self.temp_dir = tempfile.mkdtemp(prefix="etl_parser_")
        
        output_file = os.path.join(self.temp_dir, f"etl_{uuid4()}.csv")
        
        try:
            # Use tracerpt with specific parameters for large files
            cmd = [
                self.tracerpt_path,
                str(path),
                "-o", output_file,
                "-of", "CSV",
                "-y",  # Overwrite without prompting
                "-lr",  # Less restrictive; attempt to process badly-formed events
            ]
            
            # For very large files, we might want to limit the time range
            if file_size_mb > 500:  # If file is over 500MB
                logger.warning(f"Large ETL file ({file_size_mb:.1f} MB), processing may take time")
            
            # Run tracerpt as a subprocess
            logger.info("Starting tracerpt conversion...")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Monitor tracerpt process
            import time
            start_time = time.time()
            max_wait_time = 600  # 10 minutes maximum
            check_interval = 5   # Check every 5 seconds
            
            logger.info(f"Waiting for tracerpt.exe to process {file_size_mb:.1f} MB file...")
            
            # Wait for initial processing
            time.sleep(2)
            
            # Check if process failed immediately
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                if process.returncode != 0:
                    raise RuntimeError(
                        f"tracerpt failed immediately with code {process.returncode}: {stderr}"
                    )
            
            # Start reading the CSV file as it's being written
            records_yielded = 0
            records_skipped = 0
            last_pos = 0
            
            # Wait for CSV file to be created with progress monitoring
            wait_time = 0
            last_log_time = start_time
            
            while not os.path.exists(output_file):
                current_time = time.time()
                elapsed = current_time - start_time
                
                # Log progress every 30 seconds
                if current_time - last_log_time >= 30:
                    logger.info(f"tracerpt.exe still running... ({elapsed:.0f}s elapsed)")
                    last_log_time = current_time
                
                # Check if we've exceeded max wait time
                if elapsed > max_wait_time:
                    process.terminate()
                    raise RuntimeError(f"tracerpt timed out after {max_wait_time} seconds")
                
                # Check if process ended
                if process.poll() is not None:
                    stdout, stderr = process.communicate()
                    if process.returncode != 0:
                        raise RuntimeError(f"tracerpt failed with code {process.returncode}: {stderr}")
                    # Process completed but no output file
                    if not os.path.exists(output_file):
                        raise RuntimeError("tracerpt completed but produced no output file")
                    break
                
                time.sleep(check_interval)
            
            if os.path.exists(output_file):
                logger.info(f"CSV file created, starting to read records...")
                file_size = 0
                last_size_check = time.time()
                
                # Wait for file to have some content
                while os.path.getsize(output_file) == 0 and process.poll() is None:
                    time.sleep(0.5)
                
                # Stream the CSV file as it's being written
                with open(output_file, 'r', encoding='utf-8', errors='ignore') as f:
                    # Try to read header
                    header_line = f.readline()
                    if not header_line:
                        # Wait a bit for header to be written
                        time.sleep(1)
                        f.seek(0)
                        header_line = f.readline()
                    
                    if header_line:
                        # Read file incrementally instead of all at once
                        csv_reader = csv.DictReader(f, fieldnames=None)
                        csv_reader.fieldnames = next(csv.reader([header_line]))
                        
                        for row_num, row in enumerate(csv_reader):
                            # Log progress periodically
                            if row_num > 0 and row_num % 1000 == 0:
                                logger.info(f"Processed {row_num} records from CSV...")
                            
                            # Handle offset
                            if records_skipped < offset:
                                records_skipped += 1
                                continue
                            
                            # Convert and yield record
                            log_record = self._convert_csv_row(source, row)
                            if log_record:
                                yield log_record
                                records_yielded += 1
                                
                                # Check limit
                                if records_yielded >= limit:
                                    logger.info(f"Reached limit of {limit} records")
                                    # Terminate tracerpt if still running
                                    if process.poll() is None:
                                        logger.info("Terminating tracerpt as we have enough records")
                                        process.terminate()
                                    break
                            
                            # Check if process is still running periodically
                            if row_num % 100 == 0 and process.poll() is not None:
                                # Process ended, check if there was an error
                                if process.returncode != 0:
                                    logger.warning(f"tracerpt ended with code {process.returncode}")
            
            # Wait for process to complete if still running
            if process.poll() is None:
                remaining_time = max_wait_time - (time.time() - start_time)
                if remaining_time > 0:
                    logger.info(f"Waiting for tracerpt to complete (up to {remaining_time:.0f}s remaining)...")
                    try:
                        process.wait(timeout=remaining_time)
                        logger.info(f"tracerpt completed successfully after {time.time() - start_time:.0f}s")
                    except subprocess.TimeoutExpired:
                        logger.warning(f"tracerpt timed out after {max_wait_time}s, terminating...")
                        process.terminate()
                        process.wait(timeout=5)  # Give it 5 seconds to terminate
                else:
                    logger.warning("Maximum wait time exceeded, terminating tracerpt...")
                    process.terminate()
                    process.wait(timeout=5)
                    
        finally:
            # Clean up temp file
            if os.path.exists(output_file):
                try:
                    os.remove(output_file)
                except:
                    pass

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
            if "Clock-Time" in row and row["Clock-Time"]:
                try:
                    # Handle different timestamp formats
                    for fmt in ["%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M:%S.%f"]:
                        try:
                            timestamp = datetime.strptime(row["Clock-Time"], fmt)
                            break
                        except:
                            continue
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
                raw_content=None
            )
            
        except Exception as e:
            if self.config.get("verbose", False):
                logger.error(f"Failed to convert CSV row: {e}")
            return None

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
        # Use streaming parser for all files
        yield from self.parse_file_streaming(source, file_path, limit=10000)

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
        
        # Use streaming parser
        for record in self.parse_file_streaming(temp_source, path, limit=limit + offset):
            # Apply time filters
            if start_time and record.timestamp and record.timestamp < start_time:
                continue
            if end_time and record.timestamp and record.timestamp > end_time:
                continue
                
            # Apply custom filters
            if filters:
                if not self._match_filters(record, filters):
                    continue
            
            records.append(record)
            
            if len(records) >= limit + offset:
                break
        
        # Apply offset by slicing
        if offset > 0:
            return records[offset:offset + limit]
        else:
            return records[:limit]

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

    def __del__(self):
        """Cleanup temp directory on deletion."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
            except:
                pass