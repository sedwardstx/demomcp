"""MCP server API implementation."""

import argparse
import logging
import os
from typing import Dict, List, Optional, Union
from uuid import UUID

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..core.config import Config, load_config
from ..core.models import (
    LogAnalysisRequest,
    LogAnalysisResponse,
    LogQueryRequest,
    LogQueryResponse,
    LogRecord,
    LogSource,
    LogSourceRequest,
    LogSourceResponse,
    LogType,
    MCPContext,
    MCPError,
)
from ..parsers import get_parser_for_type

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mcp_server")

# Create FastAPI app
app = FastAPI(
    title="MCP Log Analyzer",
    description="Model Context Protocol server for analyzing various types of logs",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store for registered log sources
log_sources: Dict[UUID, LogSource] = {}

# In-memory context store (in a real application, this would be a database)
contexts: Dict[UUID, MCPContext] = {}


def get_config() -> Config:
    """Get application configuration.

    Returns:
        The application configuration.
    """
    config_path = os.environ.get("MCP_CONFIG")
    return load_config(config_path)


@app.exception_handler(MCPError)
async def mcp_error_handler(request: Request, exc: MCPError) -> JSONResponse:
    """Handle MCP errors.

    Args:
        request: The request.
        exc: The exception.

    Returns:
        JSON response with error details.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "error": exc.message},
    )


@app.get("/api/health")
async def health() -> Dict[str, str]:
    """Health check endpoint.

    Returns:
        Health status.
    """
    return {"status": "ok"}


@app.post("/api/sources", response_model=LogSourceResponse)
async def register_source(
    request: LogSourceRequest, config: Config = Depends(get_config)
) -> LogSourceResponse:
    """Register a log source.

    Args:
        request: The log source registration request.
        config: The application configuration.

    Returns:
        The registered log source.

    Raises:
        HTTPException: If the log source is invalid.
    """
    logger.info(f"Registering log source: {request.name} ({request.type})")

    # Create log source
    source = LogSource(
        name=request.name,
        type=request.type,
        path=request.path,
        metadata=request.metadata,
    )

    # Validate source with appropriate parser
    try:
        parser = get_parser_for_type(source.type, config.parsers)
        if not parser.validate_file(source.path):
            raise MCPError(f"Invalid log source: {source.path}", status_code=400)
    except Exception as e:
        logger.exception(f"Error validating log source: {e}")
        raise MCPError(f"Error validating log source: {str(e)}", status_code=400)

    # Store log source
    log_sources[source.id] = source

    # Create response
    return LogSourceResponse(request_id=request.request_id, source=source)


@app.get("/api/sources", response_model=List[LogSource])
async def list_sources() -> List[LogSource]:
    """List all registered log sources.

    Returns:
        List of registered log sources.
    """
    return list(log_sources.values())


@app.get("/api/sources/{source_id}", response_model=LogSource)
async def get_source(source_id: UUID = Path(..., description="Source ID")) -> LogSource:
    """Get a log source by ID.

    Args:
        source_id: The source ID.

    Returns:
        The log source.

    Raises:
        HTTPException: If the log source is not found.
    """
    if source_id not in log_sources:
        raise MCPError(f"Log source not found: {source_id}", status_code=404)
    return log_sources[source_id]


@app.delete("/api/sources/{source_id}")
async def delete_source(
    source_id: UUID = Path(..., description="Source ID")
) -> Dict[str, str]:
    """Delete a log source.

    Args:
        source_id: The source ID.

    Returns:
        Success message.

    Raises:
        HTTPException: If the log source is not found.
    """
    if source_id not in log_sources:
        raise MCPError(f"Log source not found: {source_id}", status_code=404)
    del log_sources[source_id]
    return {"status": "success", "message": f"Log source {source_id} deleted"}


@app.post("/api/query", response_model=LogQueryResponse)
async def query_logs(
    request: LogQueryRequest, config: Config = Depends(get_config)
) -> LogQueryResponse:
    """Query logs.

    Args:
        request: The log query request.
        config: The application configuration.

    Returns:
        The query response.
    """
    query = request.query
    logger.info(f"Querying logs: {query}")

    # Collect records from all sources
    records: List[LogRecord] = []
    total_records = 0

    # Create context
    context = MCPContext(request_id=request.request_id, client_id=request.client_id)
    contexts[request.request_id] = context

    # If source_ids is specified, filter by source IDs
    source_filter = {}
    if query.source_ids:
        source_filter = {
            sid: log_sources.get(sid) for sid in query.source_ids if sid in log_sources
        }
    else:
        source_filter = log_sources

    # Filter by log types if specified
    if query.types:
        source_filter = {
            sid: source
            for sid, source in source_filter.items()
            if source.type in query.types
        }

    # Get records from each source
    for source_id, source in source_filter.items():
        try:
            parser = get_parser_for_type(source.type, config.parsers)
            source_records = list(parser.parse_file(source, source.path))
            total_records += len(source_records)

            # Apply time filter
            if query.start_time:
                source_records = [
                    r
                    for r in source_records
                    if r.timestamp and r.timestamp >= query.start_time
                ]
            if query.end_time:
                source_records = [
                    r
                    for r in source_records
                    if r.timestamp and r.timestamp <= query.end_time
                ]

            # Apply custom filters if any
            for field, value in query.filters.items():
                source_records = [
                    r
                    for r in source_records
                    if field in r.data and r.data[field] == value
                ]

            records.extend(source_records)
        except Exception as e:
            logger.exception(f"Error parsing log source {source_id}: {e}")
            # Continue with other sources on error

    # Apply pagination
    start = query.offset
    end = query.offset + query.limit
    paginated_records = records[start:end] if start < len(records) else []

    return LogQueryResponse(
        request_id=request.request_id,
        records=paginated_records,
        total=total_records,
        limit=query.limit,
        offset=query.offset,
    )


@app.post("/api/analyze", response_model=LogAnalysisResponse)
async def analyze_logs(
    request: LogAnalysisRequest, config: Config = Depends(get_config)
) -> LogAnalysisResponse:
    """Analyze logs.

    Args:
        request: The log analysis request.
        config: The application configuration.

    Returns:
        The analysis response.
    """
    # This is a placeholder for the actual analysis logic
    # In a real implementation, this would call different analysis modules
    logger.info(f"Analyzing logs: {request.analysis_type}")

    # Basic implementation - just return a summary of the query
    analysis_results = {
        "analysis_type": request.analysis_type,
        "parameters": request.parameters,
        "summary": "Analysis completed successfully",
        "details": {
            "source_count": (
                len(request.query.source_ids)
                if request.query.source_ids
                else len(log_sources)
            ),
            "type_count": (
                len(request.query.types) if request.query.types else len(LogType)
            ),
            "start_time": (
                str(request.query.start_time)
                if request.query.start_time
                else "Not specified"
            ),
            "end_time": (
                str(request.query.end_time)
                if request.query.end_time
                else "Not specified"
            ),
        },
    }

    return LogAnalysisResponse(
        request_id=request.request_id,
        results=analysis_results,
        query=request.query,
    )


def main() -> None:
    """Run the MCP server."""
    parser = argparse.ArgumentParser(description="MCP Log Analyzer Server")
    parser.add_argument(
        "--config",
        help="Path to configuration file",
        default=os.environ.get("MCP_CONFIG"),
    )
    parser.add_argument("--host", help="Host to bind to", default=None)
    parser.add_argument("--port", help="Port to bind to", type=int, default=None)
    parser.add_argument("--reload", help="Enable auto-reload", action="store_true")
    args = parser.parse_args()

    # Load configuration
    if args.config:
        os.environ["MCP_CONFIG"] = args.config
    config = load_config(args.config)

    # Override with command line arguments
    host = args.host or config.server.host
    port = args.port or config.server.port

    # Configure logging
    log_level = getattr(logging, config.logging.level.upper(), logging.INFO)
    logging.basicConfig(level=log_level, format=config.logging.format)
    if config.logging.file:
        handler = logging.FileHandler(config.logging.file)
        handler.setFormatter(logging.Formatter(config.logging.format))
        logger.addHandler(handler)

    # Start server
    logger.info(f"Starting MCP server at {host}:{port}")
    uvicorn.run(
        "mcp_log_analyzer.api.server:app",
        host=host,
        port=port,
        reload=args.reload,
        log_level="info" if not config.server.debug else "debug",
    )


if __name__ == "__main__":
    main()
