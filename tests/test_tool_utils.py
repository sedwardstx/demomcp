"""
Test utilities to access tool functions for testing.
"""

import asyncio
from typing import Any, Dict

from mcp_log_analyzer.core.models import LogSource

from .server import log_sources, parsers
from .tools.log_management_tools import (
    AnalyzeLogsRequest,
    QueryLogsRequest,
    RegisterLogSourceRequest,
)


# Create direct tool function wrappers for testing
async def register_log_source(request: RegisterLogSourceRequest) -> Dict[str, Any]:
    """Direct wrapper for register_log_source tool."""
    if request.name in log_sources:
        return {"error": f"Log source '{request.name}' already exists"}

    if request.source_type not in parsers:
        return {"error": f"Unsupported source type: {request.source_type}"}

    log_source = LogSource(
        name=request.name,
        type=request.source_type,
        path=request.path,
        metadata=request.config or {},
    )

    log_sources[request.name] = log_source

    return {
        "message": f"Log source '{request.name}' registered successfully",
        "source": log_source.model_dump(),
    }


async def list_log_sources() -> Dict[str, Any]:
    """Direct wrapper for list_log_sources tool."""
    return {
        "sources": [source.model_dump() for source in log_sources.values()],
        "count": len(log_sources),
    }


async def get_log_source(name: str) -> Dict[str, Any]:
    """Direct wrapper for get_log_source tool."""
    if name not in log_sources:
        return {"error": f"Log source '{name}' not found"}

    return {"source": log_sources[name].model_dump()}


async def delete_log_source(name: str) -> Dict[str, Any]:
    """Direct wrapper for delete_log_source tool."""
    if name not in log_sources:
        return {"error": f"Log source '{name}' not found"}

    del log_sources[name]
    return {"message": f"Log source '{name}' deleted successfully"}


async def query_logs(request: QueryLogsRequest) -> Dict[str, Any]:
    """Direct wrapper for query_logs tool."""
    if request.source_name not in log_sources:
        return {"error": f"Log source '{request.source_name}' not found"}

    source = log_sources[request.source_name]
    parser = parsers[source.type]

    try:
        logs = await asyncio.to_thread(
            parser.parse,
            source.path,
            filters=request.filters,
            start_time=request.start_time,
            end_time=request.end_time,
            limit=request.limit,
            offset=request.offset,
        )

        return {
            "logs": [log.model_dump() for log in logs],
            "count": len(logs),
            "source": request.source_name,
        }
    except Exception as e:
        return {"error": f"Failed to query logs: {str(e)}"}


async def analyze_logs(request: AnalyzeLogsRequest) -> Dict[str, Any]:
    """Direct wrapper for analyze_logs tool."""
    if request.source_name not in log_sources:
        return {"error": f"Log source '{request.source_name}' not found"}

    source = log_sources[request.source_name]
    parser = parsers[source.type]

    try:
        # First, get the logs
        logs = await asyncio.to_thread(
            parser.parse,
            source.path,
            filters=request.filters,
            start_time=request.start_time,
            end_time=request.end_time,
        )

        # Then analyze them
        result = await asyncio.to_thread(
            parser.analyze, logs, analysis_type=request.analysis_type
        )

        return {
            "result": result.model_dump(),
            "source": request.source_name,
            "analysis_type": request.analysis_type,
        }
    except Exception as e:
        return {"error": f"Failed to analyze logs: {str(e)}"}
