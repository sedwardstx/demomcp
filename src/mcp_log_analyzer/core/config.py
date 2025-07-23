"""Configuration for MCP Log Analyzer."""

from pydantic import BaseModel


class Settings(BaseModel):
    """Simple settings for MCP Log Analyzer."""

    server_name: str = "mcp-log-analyzer"
    version: str = "0.1.0"

    # Parser settings
    max_file_size_mb: int = 100
    max_events: int = 10000
    batch_size: int = 1000

    # Cache settings
    cache_dir: str = "cache"
    max_cache_size_mb: int = 1024
