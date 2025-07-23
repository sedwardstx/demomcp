"""ETL parser with CSV caching to avoid repeated conversions."""

import csv
import hashlib
import json
import logging
import os
import platform
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

from ..core.models import LogRecord, LogSource, LogType
from .base import BaseParser

logger = logging.getLogger(__name__)


class EtlCachedParser(BaseParser):
    """ETL parser that caches CSV conversions for performance."""

    # Class-level cache directory
    _cache_dir: Optional[str] = None
    _cache_registry: Dict[str, Dict[str, Any]] = {}  # Maps ETL file paths to cached CSV paths
    _conversion_locks: Dict[str, Any] = {}  # Prevents concurrent conversions of same file

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize ETL cached parser.

        Args:
            config: Parser configuration.
        """
        super().__init__(config)
        self.tracerpt_path = self._find_tracerpt()
        self._init_cache_dir()

    @classmethod
    def _init_cache_dir(cls) -> None:
        """Initialize the cache directory if not already done."""
        if cls._cache_dir is None:
            # Create cache directory in temp
            cls._cache_dir = os.path.join(tempfile.gettempdir(), "mcp_etl_cache")
            os.makedirs(cls._cache_dir, exist_ok=True)

            # Load cache registry if it exists
            registry_file = os.path.join(cls._cache_dir, "cache_registry.json")
            if os.path.exists(registry_file):
                try:
                    with open(registry_file, "r") as f:
                        cls._cache_registry = json.load(f)
                    # Clean up stale entries
                    cls._cleanup_stale_cache()
                except Exception:
                    cls._cache_registry = {}

    @classmethod
    def _save_cache_registry(cls) -> None:
        """Save the cache registry to disk."""
        if cls._cache_dir is None:
            return
        registry_file = os.path.join(cls._cache_dir, "cache_registry.json")
        try:
            with open(registry_file, "w") as f:
                json.dump(cls._cache_registry, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache registry: {e}")

    @classmethod
    def _cleanup_stale_cache(cls) -> None:
        """Remove cache entries for files that no longer exist."""
        stale_entries = []
        for etl_path, cache_info in cls._cache_registry.items():
            if not os.path.exists(etl_path) or not os.path.exists(
                cache_info["csv_path"]
            ):
                stale_entries.append(etl_path)
                # Remove CSV file if it exists
                if os.path.exists(cache_info["csv_path"]):
                    try:
                        os.remove(cache_info["csv_path"])
                    except Exception:
                        pass

        for entry in stale_entries:
            del cls._cache_registry[entry]

        if stale_entries:
            cls._save_cache_registry()

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
                ["where", "tracerpt.exe"], capture_output=True, text=True, check=False
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split("\n")[0]
        except Exception:
            pass

        return None

    def is_available(self) -> bool:
        """Check if ETL parsing is available."""
        return self.tracerpt_path is not None

    def _get_cache_key(self, file_path: str) -> str:
        """Generate a cache key for an ETL file based on path and modification time."""
        path = Path(file_path)
        stat = path.stat()
        # Include file path, size, and modification time in key
        key_data = f"{file_path}|{stat.st_size}|{stat.st_mtime}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_cached_csv(self, file_path: str) -> Optional[str]:
        """Get cached CSV path if it exists and is valid."""
        if file_path not in self._cache_registry:
            return None

        cache_info = self._cache_registry[file_path]
        cache_key = self._get_cache_key(file_path)

        # Check if cache is still valid
        if cache_info.get("cache_key") != cache_key:
            # File has changed, invalidate cache
            logger.info(f"ETL file has changed, invalidating cache for {file_path}")
            self._remove_cache_entry(file_path)
            return None

        csv_path = cache_info.get("csv_path")
        if csv_path and os.path.exists(csv_path):
            logger.info(f"Using cached CSV for {file_path}: {csv_path}")
            return str(csv_path)

        # CSV file missing, remove entry
        self._remove_cache_entry(file_path)
        return None

    def _remove_cache_entry(self, file_path: str) -> None:
        """Remove a cache entry and its CSV file."""
        if file_path in self._cache_registry:
            cache_info = self._cache_registry[file_path]
            csv_path = cache_info.get("csv_path")
            if csv_path and os.path.exists(csv_path):
                try:
                    os.remove(csv_path)
                    logger.info(f"Removed cached CSV: {csv_path}")
                except Exception as e:
                    logger.error(f"Failed to remove cached CSV: {e}")
            del self._cache_registry[file_path]
            self._save_cache_registry()

    def _convert_etl_to_csv_sync(self, etl_path: str) -> str:
        """Convert ETL to CSV using tracerpt, with locking to prevent concurrent conversions."""
        import threading

        # Use threading lock to prevent concurrent conversions of same file
        if etl_path not in self._conversion_locks:
            self._conversion_locks[etl_path] = threading.Lock()

        with self._conversion_locks[etl_path]:
            # Check again if CSV was created while waiting for lock
            cached_csv = self._get_cached_csv(etl_path)
            if cached_csv:
                return cached_csv

            # Generate output filename
            cache_key = self._get_cache_key(etl_path)
            csv_filename = f"etl_{cache_key}.csv"
            csv_path = os.path.join(self._cache_dir or tempfile.gettempdir(), csv_filename)

            # Check if the CSV file already exists in cache directory (missed by registry)
            if os.path.exists(csv_path):
                logger.info(f"Found existing CSV file (missed by registry): {csv_path}")
                # Update cache registry
                file_size_mb = Path(etl_path).stat().st_size / (1024 * 1024)
                self._cache_registry[etl_path] = {
                    "csv_path": csv_path,
                    "cache_key": cache_key,
                    "converted_at": datetime.now().isoformat(),
                    "file_size_mb": file_size_mb,
                    "conversion_duration_s": 0,  # Unknown
                }
                self._save_cache_registry()
                return csv_path

            logger.info(f"Converting ETL to CSV: {etl_path} -> {csv_path}")

            # Get file size for logging
            file_size_mb = Path(etl_path).stat().st_size / (1024 * 1024)
            logger.info(f"ETL file size: {file_size_mb:.1f} MB")

            # Run tracerpt
            if self.tracerpt_path is None:
                raise RuntimeError("tracerpt.exe not found")
            cmd = [
                self.tracerpt_path,
                etl_path,
                "-o",
                csv_path,
                "-of",
                "CSV",
                "-y",  # Overwrite without prompting
                "-lr",  # Less restrictive; attempt to process badly-formed events
            ]

            start_time = datetime.now()
            logger.info(f"Starting tracerpt conversion at {start_time}")
            logger.info(f"Converting ETL file: {etl_path}")
            logger.info(f"Output CSV: {csv_path}")

            try:
                # Start tracerpt process
                import threading
                import time

                process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )

                # Monitor thread for progress updates
                def monitor_conversion() -> None:
                    elapsed = 0
                    while process.poll() is None:  # While process is running
                        time.sleep(30)  # Check every 30 seconds
                        elapsed += 30
                        if os.path.exists(csv_path):
                            try:
                                csv_size_mb = os.path.getsize(csv_path) / (1024 * 1024)
                                logger.info(
                                    f"ETL conversion in progress... {elapsed}s elapsed, CSV size: {csv_size_mb:.1f} MB"
                                )
                            except Exception:
                                logger.info(
                                    f"ETL conversion in progress... {elapsed}s elapsed"
                                )
                        else:
                            logger.info(
                                f"ETL conversion in progress... {elapsed}s elapsed, waiting for CSV creation..."
                            )

                # Start monitoring in background thread
                monitor_thread = threading.Thread(
                    target=monitor_conversion, daemon=True
                )
                monitor_thread.start()

                try:
                    # Wait for process to complete with timeout
                    stdout, stderr = process.communicate(
                        timeout=600
                    )  # 10 minute timeout

                    if process.returncode != 0:
                        raise RuntimeError(
                            f"tracerpt failed with code {process.returncode}: {stderr}"
                        )

                except subprocess.TimeoutExpired:
                    # Kill the process if it times out
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    raise RuntimeError("tracerpt conversion timed out after 10 minutes")

                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                logger.info(f"Tracerpt completed in {duration:.1f} seconds")

                if process.returncode != 0:
                    raise RuntimeError(
                        f"tracerpt failed with code {process.returncode}: {stderr}"
                    )

                # Verify CSV was created
                if not os.path.exists(csv_path):
                    raise RuntimeError("tracerpt completed but produced no output file")

                # Update cache registry
                self._cache_registry[etl_path] = {
                    "csv_path": csv_path,
                    "cache_key": cache_key,
                    "converted_at": datetime.now().isoformat(),
                    "file_size_mb": file_size_mb,
                    "conversion_duration_s": duration,
                }
                self._save_cache_registry()

                logger.info(f"Successfully cached ETL conversion: {csv_path}")
                return csv_path

            except subprocess.TimeoutExpired:
                raise RuntimeError("tracerpt conversion timed out after 10 minutes")
            except Exception as e:
                # Clean up partial file if it exists
                if os.path.exists(csv_path):
                    try:
                        os.remove(csv_path)
                    except Exception:
                        pass
                raise

    def parse_file(
        self, source: LogSource, file_path: Union[str, Path]
    ) -> Iterator[LogRecord]:
        """Parse ETL log records from a file using cached CSV.

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

        path = str(Path(file_path))
        if not os.path.exists(path):
            raise FileNotFoundError(f"ETL file not found: {file_path}")

        # Convert to CSV (cached)
        csv_path = self._convert_etl_to_csv_sync(path)

        # Parse CSV file
        yield from self._parse_csv_file(source, csv_path)

    def _parse_csv_file(
        self, source: LogSource, csv_path: str, limit: int = 10000, offset: int = 0
    ) -> Iterator[LogRecord]:
        """Parse records from the cached CSV file.

        Args:
            source: The log source information.
            csv_path: Path to the CSV file.
            limit: Maximum number of records to yield.
            offset: Number of records to skip.

        Yields:
            LogRecord objects.
        """
        records_yielded = 0
        records_skipped = 0

        with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)

            for row_num, row in enumerate(reader):
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
                        break

    def _convert_csv_row(
        self, source: LogSource, row: Dict[str, str]
    ) -> Optional[LogRecord]:
        """Convert a CSV row from tracerpt to a LogRecord.

        Args:
            source: The log source information.
            row: CSV row dictionary.

        Returns:
            LogRecord or None if conversion fails.
        """
        try:
            # Clean up field names (remove alignment underscores)
            clean_data = {}

            for key, value in row.items():
                if key and value:
                    # Remove leading/trailing underscores and spaces
                    clean_key = key.strip().strip("_").lower().replace(" ", "_")
                    clean_value = value.strip()
                    if clean_key and clean_value:
                        clean_data[clean_key] = clean_value

            # Try to parse timestamp from clock_time
            timestamp = None
            if "clock_time" in clean_data:
                # Clock time is in Windows FILETIME format (100-nanosecond intervals since 1601)
                try:
                    filetime = int(clean_data["clock_time"])
                    # Convert to Unix timestamp
                    unix_timestamp = (filetime - 116444736000000000) / 10000000.0
                    timestamp = datetime.fromtimestamp(unix_timestamp)
                except Exception:
                    pass

            return LogRecord(
                source_id=source.id,
                timestamp=timestamp,
                data=clean_data,
            )

        except Exception as e:
            if self.config.get("verbose", False):
                logger.error(f"Failed to convert CSV row: {e}")
            return None

    def parse(
        self,
        path: str,
        filters: Optional[Dict[str, Any]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> List[LogRecord]:
        """Parse ETL file with filtering and pagination using cache.

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
            name="temp_etl", type=LogType.ETL, path=path, metadata={}
        )

        records: List[LogRecord] = []

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

            # We need to handle offset/limit at this level since parse_file
            # doesn't know about filters
            if len(records) < offset:
                continue

            records.append(record)

            if len(records) >= limit + offset:
                break

        # Apply offset by slicing
        if offset > 0 and len(records) > offset:
            return records[offset : offset + limit]
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
        if not str(path).lower().endswith(".etl"):
            return False

        # Check if file exists and is readable
        if not path.exists() or not path.is_file():
            return False

        # Check if we have tracerpt available
        if not self.is_available():
            return False

        return True

    @classmethod
    def cleanup_cache_for_source(cls, source_path: str) -> None:
        """Clean up cached CSV for a specific ETL source.

        Args:
            source_path: Path to the ETL file whose cache should be removed.
        """
        logger.info(f"Cleaning up cache for ETL source: {source_path}")

        # Ensure cache is initialized
        cls._init_cache_dir()

        # Remove cache entry
        if source_path in cls._cache_registry:
            cache_info = cls._cache_registry[source_path]
            csv_path = cache_info.get("csv_path")

            # Remove CSV file
            if csv_path and os.path.exists(csv_path):
                try:
                    os.remove(csv_path)
                    logger.info(f"Removed cached CSV file: {csv_path}")
                except Exception as e:
                    logger.error(f"Failed to remove cached CSV: {e}")

            # Remove from registry
            del cls._cache_registry[source_path]
            cls._save_cache_registry()
            logger.info(f"Removed cache registry entry for: {source_path}")

    @classmethod
    def cleanup_all_cache(cls) -> None:
        """Clean up all cached CSV files."""
        logger.info("Cleaning up all ETL cache")

        # Ensure cache is initialized
        cls._init_cache_dir()

        # Remove all CSV files
        for etl_path, cache_info in list(cls._cache_registry.items()):
            cls.cleanup_cache_for_source(etl_path)

        # Clear registry
        cls._cache_registry = {}
        cls._save_cache_registry()
