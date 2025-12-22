"""
Shared global variables for PostgreSQL MCP Server

This module provides centralized storage for global variables to avoid
circular imports and enable sharing across all tool modules.
"""

from typing import Optional
from .database import ConnectionPoolManager, DatabaseManager
from .config import ServerConfig

# Global connection pool manager for connection pooling
_global_pool_manager: Optional[ConnectionPoolManager] = None

# Global configuration - loaded once in main()
_global_config: Optional[ServerConfig] = None


def set_global_db_connection(
    pool_manager: ConnectionPoolManager, config: ServerConfig
) -> None:
    """Set global connection pool manager and configuration for sharing across tools"""
    global _global_pool_manager, _global_config
    _global_pool_manager = pool_manager
    _global_config = config


def get_global_pool_manager() -> Optional[ConnectionPoolManager]:
    """Get the global connection pool manager"""
    return _global_pool_manager


def get_global_config() -> Optional[ServerConfig]:
    """Get the global configuration"""
    return _global_config


def get_database_manager() -> DatabaseManager:
    """
    Get a DatabaseManager instance using global connection or create new one

    Returns:
        DatabaseManager instance ready for use
    """
    _global_pool_manager = get_global_pool_manager()
    _global_config = get_global_config()

    if _global_pool_manager is None or _global_config is None:
        from .config import load_config

        config = load_config()
        db_manager = DatabaseManager(config.postgres)
        db_manager.connect()
        return db_manager
    else:
        db_manager = DatabaseManager(_global_config.postgres, _global_pool_manager)
        db_manager._is_connected = True
        return db_manager
