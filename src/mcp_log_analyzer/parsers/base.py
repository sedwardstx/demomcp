"""Base parser interface for all log types."""

import abc
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

from ..core.models import LogRecord, LogSource


class BaseParser(abc.ABC):
    """Base parser interface for all log types."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize parser with configuration.

        Args:
            config: Parser configuration.
        """
        self.config = config or {}

    @abc.abstractmethod
    def parse_file(
        self, source: LogSource, file_path: Union[str, Path]
    ) -> Iterator[LogRecord]:
        """Parse log records from a file.

        Args:
            source: The log source information.
            file_path: Path to the log file.

        Yields:
            Log records from the file.
        """
        pass

    @abc.abstractmethod
    def parse_content(self, source: LogSource, content: str) -> Iterator[LogRecord]:
        """Parse log records from a string.

        Args:
            source: The log source information.
            content: String content to parse.

        Yields:
            Log records from the content.
        """
        pass

    def validate_file(self, file_path: Union[str, Path]) -> bool:
        """Validate if the file can be parsed by this parser.

        Args:
            file_path: Path to the log file.

        Returns:
            True if the file can be parsed, False otherwise.
        """
        path = Path(file_path)
        return path.exists() and path.is_file()

    def extract_timestamp(self, record_data: Dict[str, Any]) -> Optional[str]:
        """Extract timestamp from record data.

        Args:
            record_data: Record data.

        Returns:
            Timestamp as string if found, None otherwise.
        """
        # Default implementation looks for common timestamp field names
        timestamp_fields = [
            "timestamp",
            "time",
            "date",
            "datetime",
            "@timestamp",
            "created_at",
        ]
        for field in timestamp_fields:
            if field in record_data:
                return str(record_data[field])
        return None
