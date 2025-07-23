"""Core models for the SF MCP Log Analyzer."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class LogType(str, Enum):
    """Supported log types."""

    EVENT = "event"
    STRUCTURED = "structured"
    CSV = "csv"
    UNSTRUCTURED = "unstructured"


class LogSource(BaseModel):
    """Log source information."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    type: LogType
    path: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LogRecord(BaseModel):
    """Base log record."""

    id: UUID = Field(default_factory=uuid4)
    source_id: UUID
    timestamp: Optional[datetime] = None
    data: Dict[str, Any]
    raw_data: Optional[str] = None


class LogQuery(BaseModel):
    """Query parameters for log retrieval."""

    source_ids: Optional[List[UUID]] = None
    types: Optional[List[LogType]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    filters: Dict[str, Any] = Field(default_factory=dict)
    limit: int = 100
    offset: int = 0


class MCPRequest(BaseModel):
    """Base MCP request model."""

    request_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.now)
    client_id: Optional[str] = None


class LogSourceRequest(MCPRequest):
    """Request to register a log source."""

    name: str
    type: LogType
    path: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LogQueryRequest(MCPRequest):
    """Request to query logs."""

    query: LogQuery


class LogAnalysisRequest(MCPRequest):
    """Request to analyze logs."""

    query: LogQuery
    analysis_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class MCPResponse(BaseModel):
    """Base MCP response model."""

    request_id: UUID
    timestamp: datetime = Field(default_factory=datetime.now)
    status: str = "success"
    error: Optional[str] = None


class LogSourceResponse(MCPResponse):
    """Response for log source registration."""

    source: LogSource


class LogQueryResponse(MCPResponse):
    """Response for log query."""

    records: List[LogRecord]
    total: int
    limit: int
    offset: int


class LogAnalysisResponse(MCPResponse):
    """Response for log analysis."""

    results: Dict[str, Any]
    query: LogQuery


class MCPContext(BaseModel):
    """Context for processing MCP requests."""

    request_id: UUID
    start_time: datetime = Field(default_factory=datetime.now)
    client_id: Optional[str] = None
    log_sources: Dict[UUID, LogSource] = Field(default_factory=dict)


class MCPError(Exception):
    """Base error for MCP operations."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)
