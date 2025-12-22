#!/usr/bin/env python3
"""Test connection sharing without actual database connection"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import Mock, MagicMock, patch
from src.mcp_postgres_duwenji.config import PostgresConfig, ServerConfig, DockerConfig
from src.mcp_postgres_duwenji.database import DatabaseManager
from src.mcp_postgres_duwenji.tools.crud_tools import set_global_db_connection

def test_connection_sharing_logic():
    """Test the logic of connection sharing without actual database"""
    print("Testing connection sharing logic...")
    
    # Create mock config with all required attributes
    mock_config = Mock()
    mock_config.postgres = Mock(spec=PostgresConfig)
    mock_config.postgres.host = "localhost"
    mock_config.postgres.port = 5432
    mock_config.postgres.database = "testdb"
    mock_config.postgres.username = "testuser"
    mock_config.postgres.password = "testpass"
    mock_config.postgres.ssl_mode = "prefer"
    mock_config.postgres.pool_size = 5
    mock_config.postgres.max_overflow = 10
    
    # Create mock connection
    mock_connection = Mock()
    mock_connection.test_connection = Mock(return_value=True)
    
    # Set global connection
    set_global_db_connection(mock_connection, mock_config)
    print("✓ Set global mock connection")
    
    # Import crud_tools after setting global connection
    from src.mcp_postgres_duwenji.tools import crud_tools
    
    # Check that global variables are set
    assert crud_tools._global_db_connection == mock_connection
    assert crud_tools._global_config == mock_config
    print("✓ Global variables correctly set")
    
    # Test DatabaseManager with shared connection
    db_manager = DatabaseManager(mock_config.postgres, mock_connection)
    assert db_manager._owns_connection == False
    assert db_manager.connection == mock_connection
    print("✓ DatabaseManager correctly uses shared connection")
    
    # Test DatabaseManager without connection (should create its own)
    db_manager2 = DatabaseManager(mock_config.postgres)
    assert db_manager2._owns_connection == True
    assert db_manager2.connection != mock_connection
    print("✓ DatabaseManager without connection creates its own")
    
    # Test connect/disconnect behavior
    db_manager.connect()
    # Should not call connect on shared connection since _owns_connection is False
    mock_connection.connect.assert_not_called()
    print("✓ Shared connection manager does not call connect on shared connection")
    
    db_manager.disconnect()
    mock_connection.disconnect.assert_not_called()
    print("✓ Shared connection manager does not call disconnect on shared connection")
    
    print("\nAll tests passed! Connection sharing logic is correct.")

if __name__ == "__main__":
    test_connection_sharing_logic()
