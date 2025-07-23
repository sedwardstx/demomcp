"""Log parsers for different log formats."""

from typing import Any, Dict, Optional, Type

from ..core.models import LogType

# Import parser base class for type checking
from .base import BaseParser

# Dictionary to store parser classes by log type
_parsers: Dict[LogType, Type[BaseParser]] = {}


def register_parser(log_type: LogType, parser_class: Type[BaseParser]) -> None:
    """Register a parser for a log type.

    Args:
        log_type: The log type.
        parser_class: The parser class.
    """
    _parsers[log_type] = parser_class


def get_parser_for_type(
    log_type: LogType, config: Optional[Dict[str, Any]] = None
) -> BaseParser:
    """Get a parser for a log type.

    Args:
        log_type: The log type.
        config: Parser configuration.

    Returns:
        An instance of the parser for the log type.

    Raises:
        ValueError: If no parser is registered for the log type.
    """
    if log_type not in _parsers:
        raise ValueError(f"No parser registered for log type: {log_type}")

    # Get parser-specific configuration
    parser_config = None
    if config is not None:
        if log_type == LogType.EVENT and hasattr(config, "evt"):
            parser_config = config.evt
        elif log_type == LogType.STRUCTURED and hasattr(config, "structured"):
            parser_config = config.structured
        elif log_type == LogType.CSV and hasattr(config, "csv"):
            parser_config = config.csv
        elif log_type == LogType.UNSTRUCTURED and hasattr(config, "unstructured"):
            parser_config = config.unstructured

    # Create parser instance
    return _parsers[log_type](parser_config)


# Import parser implementations and register them
try:
    from .evt_parser import EventLogParser

    register_parser(LogType.EVENT, EventLogParser)
except ImportError:
    # Windows Event Log parser might not be available on non-Windows platforms
    pass

# Import and register CSV parser
try:
    from .csv_parser import CsvLogParser

    register_parser(LogType.CSV, CsvLogParser)
except ImportError:
    pass

# TODO: Implement and register parsers for other log types:
# - StructuredLogParser (JSON, XML)
# - UnstructuredLogParser
