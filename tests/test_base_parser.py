"""Tests for the base parser."""

import unittest
from pathlib import Path
from typing import Dict, Iterator
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

from mcp_log_analyzer.core.models import LogRecord, LogSource, LogType
from mcp_log_analyzer.parsers.base import BaseParser


class MockParser(BaseParser):
    """Mock parser implementation for testing."""

    def parse_file(self, source: LogSource, file_path: Path) -> Iterator[LogRecord]:
        """Parse a file."""
        yield LogRecord(
            source_id=source.id,
            data={"test": "value"},
        )

    def parse_content(self, source: LogSource, content: str) -> Iterator[LogRecord]:
        """Parse content."""
        yield LogRecord(
            source_id=source.id,
            data={"test": "value"},
        )


class TestBaseParser(unittest.TestCase):
    """Tests for the base parser."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.parser = MockParser()
        self.source = LogSource(
            id=uuid4(),
            name="Test Source",
            type=LogType.EVENT,
            path="test/path",
        )

    def test_validate_file(self) -> None:
        """Test validate_file method."""
        with patch("pathlib.Path.exists", return_value=True), patch(
            "pathlib.Path.is_file", return_value=True
        ):
            self.assertTrue(self.parser.validate_file("test/path"))

        with patch("pathlib.Path.exists", return_value=False):
            self.assertFalse(self.parser.validate_file("test/path"))

        with patch("pathlib.Path.exists", return_value=True), patch(
            "pathlib.Path.is_file", return_value=False
        ):
            self.assertFalse(self.parser.validate_file("test/path"))

    def test_extract_timestamp(self) -> None:
        """Test extract_timestamp method."""
        # Test with timestamp field
        record_data: Dict[str, str] = {"timestamp": "2023-05-02T12:00:00Z"}
        self.assertEqual(
            self.parser.extract_timestamp(record_data), "2023-05-02T12:00:00Z"
        )

        # Test with time field
        record_data = {"time": "2023-05-02T12:00:00Z"}
        self.assertEqual(
            self.parser.extract_timestamp(record_data), "2023-05-02T12:00:00Z"
        )

        # Test with date field
        record_data = {"date": "2023-05-02"}
        self.assertEqual(self.parser.extract_timestamp(record_data), "2023-05-02")

        # Test with datetime field
        record_data = {"datetime": "2023-05-02T12:00:00Z"}
        self.assertEqual(
            self.parser.extract_timestamp(record_data), "2023-05-02T12:00:00Z"
        )

        # Test with @timestamp field
        record_data = {"@timestamp": "2023-05-02T12:00:00Z"}
        self.assertEqual(
            self.parser.extract_timestamp(record_data), "2023-05-02T12:00:00Z"
        )

        # Test with created_at field
        record_data = {"created_at": "2023-05-02T12:00:00Z"}
        self.assertEqual(
            self.parser.extract_timestamp(record_data), "2023-05-02T12:00:00Z"
        )

        # Test with no timestamp field
        record_data = {"other": "value"}
        self.assertIsNone(self.parser.extract_timestamp(record_data))


if __name__ == "__main__":
    unittest.main()
