"""
Core log management MCP tools.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict

from mcp.server import FastMCP
from pydantic import BaseModel, Field


# Tool Models
class RegisterLogSourceRequest(BaseModel):
    """Request model for registering a log source."""

    name: str = Field(..., description="Unique name for the log source")
    source_type: str = Field(
        ..., description="Type of log source (evt, etl, json, xml, csv, text)"
    )
    path: str = Field(..., description="Path to the log file or directory")
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Additional configuration for the parser"
    )


class QueryLogsRequest(BaseModel):
    """Request model for querying logs."""

    source_name: str = Field(..., description="Name of the log source to query")
    filters: Dict[str, Any] = Field(
        default_factory=dict, description="Filters to apply"
    )
    start_time: datetime = Field(None, description="Start time for the query")
    end_time: datetime = Field(None, description="End time for the query")
    limit: int = Field(100, description="Maximum number of logs to return")
    offset: int = Field(0, description="Number of logs to skip")


class AnalyzeLogsRequest(BaseModel):
    """Request model for analyzing logs."""

    source_name: str = Field(..., description="Name of the log source to analyze")
    analysis_type: str = Field(
        "summary", description="Type of analysis (summary, pattern, anomaly)"
    )
    filters: Dict[str, Any] = Field(
        default_factory=dict, description="Filters to apply before analysis"
    )
    start_time: datetime = Field(None, description="Start time for the analysis")
    end_time: datetime = Field(None, description="End time for the analysis")


def register_log_management_tools(mcp: FastMCP):
    """Register all log management tools with the MCP server."""

    @mcp.tool()
    async def register_log_source(request: RegisterLogSourceRequest) -> Dict[str, Any]:
        """
        Register a new log source for analysis.

        This tool allows you to register various types of log sources including:
        - Windows Event Logs (evt)
        - Windows Event Trace Logs (etl)
        - JSON logs
        - XML logs
        - CSV logs
        - Unstructured text logs
        """
        from mcp_log_analyzer.core.models import LogSource

        from ..server import log_sources, parsers, parser_aliases

        if request.name in log_sources:
            return {"error": f"Log source '{request.name}' already exists"}

        # Check if source_type is an alias and map it to the actual type
        actual_source_type = parser_aliases.get(request.source_type, request.source_type)
        
        if actual_source_type not in parsers:
            supported_types = list(parsers.keys())
            return {"error": f"Unsupported source type: {request.source_type}. Supported types are: {', '.join(supported_types)}"}

        log_source = LogSource(
            name=request.name,
            type=actual_source_type,
            path=request.path,
            metadata=request.config,
        )

        log_sources[request.name] = log_source
        
        # Persist state
        from ..server import state_manager, get_log_sources
        state_manager.save_log_sources(get_log_sources())

        return {
            "message": f"Log source '{request.name}' registered successfully",
            "source": log_source.model_dump(),
        }

    @mcp.tool()
    async def list_log_sources() -> Dict[str, Any]:
        """
        List all registered log sources.

        Returns information about all currently registered log sources
        including their names, types, and paths.
        """
        from ..server import log_sources

        return {
            "sources": [source.model_dump() for source in log_sources.values()],
            "count": len(log_sources),
        }

    @mcp.tool()
    async def get_log_source(name: str) -> Dict[str, Any]:
        """
        Get details about a specific log source.

        Args:
            name: The name of the log source to retrieve
        """
        from ..server import log_sources

        if name not in log_sources:
            return {"error": f"Log source '{name}' not found"}

        return {"source": log_sources[name].model_dump()}

    @mcp.tool()
    async def delete_log_source(name: str) -> Dict[str, Any]:
        """
        Delete a registered log source.

        Args:
            name: The name of the log source to delete
        """
        from ..server import log_sources

        if name not in log_sources:
            return {"error": f"Log source '{name}' not found"}

        # Get source details before deletion
        source = log_sources[name]
        
        # Clean up ETL cache if this is an ETL source
        if source.type == "etl":
            try:
                from mcp_log_analyzer.parsers.etl_cached_parser import EtlCachedParser
                EtlCachedParser.cleanup_cache_for_source(source.path)
            except Exception as e:
                # Log error but don't fail the deletion
                pass

        del log_sources[name]
        
        # Persist state
        from ..server import state_manager, get_log_sources
        state_manager.save_log_sources(get_log_sources())
        
        return {"message": f"Log source '{name}' deleted successfully"}

    @mcp.tool()
    async def query_logs(request: QueryLogsRequest) -> Dict[str, Any]:
        """
        Query logs from a registered source.

        This tool allows you to:
        - Filter logs by various criteria
        - Specify time ranges
        - Paginate through results
        """
        from ..server import log_sources, parsers
        import logging
        
        logger = logging.getLogger(__name__)

        if request.source_name not in log_sources:
            return {"error": f"Log source '{request.source_name}' not found"}

        source = log_sources[request.source_name]
        parser = parsers[source.type]

        try:
            # Use longer timeout for ETL files (10 minutes)
            timeout = 600.0 if source.type == "etl" else 30.0
            
            # Log start of operation for ETL files
            if source.type == "etl":
                import os
                file_size_mb = os.path.getsize(source.path) / (1024 * 1024)
                logger.info(f"Starting ETL query for {source.name} ({file_size_mb:.1f} MB file)")
            
            # Add timeout for log parsing
            logs = await asyncio.wait_for(
                asyncio.to_thread(
                    parser.parse,
                    source.path,
                    filters=request.filters,
                    start_time=request.start_time,
                    end_time=request.end_time,
                    limit=request.limit,
                    offset=request.offset,
                ),
                timeout=timeout
            )

            logger.info(f"Successfully queried {len(logs)} logs from {request.source_name}")
            
            return {
                "logs": [log.model_dump() for log in logs],
                "count": len(logs),
                "source": request.source_name,
            }
        except asyncio.TimeoutError:
            timeout = 600.0 if source.type == "etl" else 30.0
            logger.error(f"Query timed out after {timeout} seconds for {request.source_name}")
            return {"error": f"Query timed out after {timeout} seconds. The log file may be too large or complex to parse."}
        except Exception as e:
            logger.error(f"Query failed for {request.source_name}: {str(e)}")
            return {"error": f"Failed to query logs: {str(e)}"}

    @mcp.tool()
    async def analyze_logs(request: AnalyzeLogsRequest) -> Dict[str, Any]:
        """
        Analyze logs from a registered source.

        Available analysis types:
        - summary: General statistics and overview
        - pattern: Pattern detection and frequency analysis
        - anomaly: Anomaly detection
        """
        from ..server import log_sources, parsers
        import logging
        
        logger = logging.getLogger(__name__)

        if request.source_name not in log_sources:
            return {"error": f"Log source '{request.source_name}' not found"}

        source = log_sources[request.source_name]
        parser = parsers[source.type]

        try:
            # First, get the logs with timeout
            timeout = 600.0 if source.type == "etl" else 30.0
            
            # Log start of operation for ETL files
            if source.type == "etl":
                import os
                file_size_mb = os.path.getsize(source.path) / (1024 * 1024)
                logger.info(f"Starting ETL analysis for {source.name} ({file_size_mb:.1f} MB file)")
            
            logs = await asyncio.wait_for(
                asyncio.to_thread(
                    parser.parse,
                    source.path,
                    filters=request.filters,
                    start_time=request.start_time,
                    end_time=request.end_time,
                ),
                timeout=timeout
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
        except asyncio.TimeoutError:
            timeout = 600.0 if source.type == "etl" else 30.0
            logger.error(f"Analysis timed out after {timeout} seconds for {request.source_name}")
            return {"error": f"Analysis timed out after {timeout} seconds. The log file may be too large or complex to parse."}
        except Exception as e:
            logger.error(f"Analysis failed for {request.source_name}: {str(e)}")
            return {"error": f"Failed to analyze logs: {str(e)}"}
