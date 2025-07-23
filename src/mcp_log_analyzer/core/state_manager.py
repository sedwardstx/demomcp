"""
State persistence manager for MCP Log Analyzer.

Manages persistent storage of log sources and other state that needs
to survive server restarts.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from .models import LogSource, LogType

logger = logging.getLogger(__name__)


class StateManager:
    """Manages persistent state for the MCP server."""
    
    def __init__(self, state_dir: Optional[Path] = None):
        """Initialize state manager.
        
        Args:
            state_dir: Directory to store state files. Defaults to user's app data.
        """
        if state_dir is None:
            # Use platform-appropriate directory
            if os.name == 'nt':  # Windows
                app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
                state_dir = Path(app_data) / 'MCPLogAnalyzer'
            else:  # Unix-like
                state_dir = Path.home() / '.config' / 'mcp-log-analyzer'
        
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        self.state_file = self.state_dir / 'server_state.json'
        self.sources_file = self.state_dir / 'log_sources.json'
        
        logger.info(f"State manager initialized with directory: {self.state_dir}")
    
    def save_log_sources(self, log_sources: Dict[str, LogSource]) -> None:
        """Save log sources to persistent storage.
        
        Args:
            log_sources: Dictionary of log sources to save.
        """
        try:
            sources_data = {
                name: {
                    'id': str(source.id),
                    'name': source.name,
                    'type': source.type,
                    'path': source.path,
                    'metadata': source.metadata,
                    'created_at': source.created_at.isoformat() if source.created_at else None,
                    'updated_at': source.updated_at.isoformat() if source.updated_at else None,
                }
                for name, source in log_sources.items()
            }
            
            with open(self.sources_file, 'w') as f:
                json.dump(sources_data, f, indent=2)
            
            logger.info(f"Saved {len(log_sources)} log sources to {self.sources_file}")
            
        except Exception as e:
            logger.error(f"Failed to save log sources: {e}")
    
    def load_log_sources(self) -> Dict[str, LogSource]:
        """Load log sources from persistent storage.
        
        Returns:
            Dictionary of loaded log sources.
        """
        log_sources = {}
        
        if not self.sources_file.exists():
            logger.info("No saved log sources found")
            return log_sources
        
        try:
            with open(self.sources_file, 'r') as f:
                sources_data = json.load(f)
            
            for name, data in sources_data.items():
                # Convert datetime strings back to datetime objects
                if data.get('created_at'):
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                if data.get('updated_at'):
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                
                # Create LogSource instance
                source = LogSource(
                    id=data['id'],
                    name=data['name'],
                    type=data['type'],
                    path=data['path'],
                    metadata=data.get('metadata', {}),
                    created_at=data.get('created_at'),
                    updated_at=data.get('updated_at')
                )
                
                log_sources[name] = source
            
            logger.info(f"Loaded {len(log_sources)} log sources from {self.sources_file}")
            
        except Exception as e:
            logger.error(f"Failed to load log sources: {e}")
        
        return log_sources
    
    def save_server_state(self, state: Dict[str, Any]) -> None:
        """Save general server state.
        
        Args:
            state: State dictionary to save.
        """
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.info(f"Saved server state to {self.state_file}")
            
        except Exception as e:
            logger.error(f"Failed to save server state: {e}")
    
    def load_server_state(self) -> Dict[str, Any]:
        """Load general server state.
        
        Returns:
            Loaded state dictionary or empty dict if none exists.
        """
        if not self.state_file.exists():
            logger.info("No saved server state found")
            return {}
        
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            logger.info(f"Loaded server state from {self.state_file}")
            return state
            
        except Exception as e:
            logger.error(f"Failed to load server state: {e}")
            return {}
    
    def clear_state(self) -> None:
        """Clear all saved state."""
        try:
            if self.sources_file.exists():
                self.sources_file.unlink()
                logger.info("Cleared log sources state")
            
            if self.state_file.exists():
                self.state_file.unlink()
                logger.info("Cleared server state")
                
        except Exception as e:
            logger.error(f"Failed to clear state: {e}")


# Global state manager instance
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """Get the global state manager instance."""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager