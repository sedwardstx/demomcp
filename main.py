#!/usr/bin/env python3
"""
Main entry point for the MCP Log Analyzer server with graceful shutdown support.
"""

import asyncio
import atexit
import signal
import sys
import logging
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_log_analyzer.mcp_server.server import mcp, log_sources, get_log_sources

logger = logging.getLogger(__name__)

# Track if cleanup has been performed
_cleanup_done = False


def cleanup_resources():
    """Clean up all resources on shutdown."""
    global _cleanup_done
    
    # Avoid duplicate cleanup
    if _cleanup_done:
        return
    
    _cleanup_done = True
    logger.info("Cleaning up resources on shutdown...")
    
    # Clean up ETL caches for all ETL sources
    etl_sources = [source for source in get_log_sources().values() if source.type == "etl"]
    if etl_sources:
        try:
            from mcp_log_analyzer.parsers.etl_cached_parser import EtlCachedParser
            logger.info(f"Cleaning up ETL caches for {len(etl_sources)} source(s)")
            for source in etl_sources:
                logger.info(f"Cleaning up ETL cache for: {source.name} ({source.path})")
                EtlCachedParser.cleanup_cache_for_source(source.path)
        except Exception as e:
            logger.error(f"Error cleaning up ETL caches: {e}")
    
    # Clean up all cached ETL files (including orphaned ones)
    try:
        from mcp_log_analyzer.parsers.etl_cached_parser import EtlCachedParser
        logger.info("Cleaning up any remaining ETL cache files...")
        EtlCachedParser.cleanup_all_cache()
    except Exception as e:
        logger.error(f"Error cleaning up all ETL caches: {e}")
    
    # Don't clear log sources - they should persist across restarts
    # log_sources.clear()
    logger.info(f"Keeping {len(get_log_sources())} log sources for next startup")


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    cleanup_resources()
    sys.exit(0)


async def async_signal_handler():
    """Async signal handler for asyncio."""
    cleanup_resources()


def setup_signal_handlers():
    """Set up signal handlers for graceful shutdown."""
    # Handle CTRL+C (SIGINT) and termination signals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # For Windows, also handle CTRL+BREAK
    if sys.platform == "win32":
        signal.signal(signal.SIGBREAK, signal_handler)
    
    # Set up asyncio signal handlers if running in event loop
    try:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(async_signal_handler()))
    except RuntimeError:
        # No event loop running yet
        pass


def main():
    """Run the MCP server with cleanup support."""
    # Set up logging with DEBUG level to see more details
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Register cleanup function with atexit
    atexit.register(cleanup_resources)
    
    # Set up signal handlers
    setup_signal_handlers()
    
    try:
        logger.info("Starting MCP Log Analyzer server...")
        
        # Add a handler to catch any unhandled exceptions
        import sys
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        
        sys.excepthook = handle_exception
        
        mcp.run()
        logger.info("MCP server run() method returned - server shutting down")
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
        cleanup_resources()
    except Exception as e:
        logger.error(f"Server error: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error args: {e.args}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        cleanup_resources()
        raise
    finally:
        # Final cleanup if not already done
        logger.info("In finally block - checking if cleanup needed")
        try:
            # Check if any log sources are loaded (use try/except in case lazy loading hasn't happened)
            sources = get_log_sources()
            if sources:
                logger.info(f"Found {len(sources)} log sources, cleaning up")
                cleanup_resources()
        except:
            # If there's any error checking, skip cleanup
            pass
        logger.info("MCP server process ending")


if __name__ == "__main__":
    main()