#!/usr/bin/env python3
"""Test script for global database connection sharing"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.mcp_postgres_duwenji.config import load_config
from src.mcp_postgres_duwenji.database import DatabaseConnection, DatabaseManager
from src.mcp_postgres_duwenji.tools.crud_tools import set_global_db_connection

def test_global_connection():
    """Test that global connection sharing works"""
    print("Testing global database connection sharing...")
    
    # Load configuration
    config = load_config()
    print(f"Loaded config for database: {config.postgres.database}")
    
    # Create global connection
    global_connection = DatabaseConnection(config.postgres)
    print("Created global DatabaseConnection")
    
    # Set global connection
    set_global_db_connection(global_connection, config)
    print("Set global database connection")
    
    # Test DatabaseManager with global connection
    db_manager1 = DatabaseManager(config.postgres, global_connection)
    print("Created DatabaseManager 1 with global connection")
    
    # Test DatabaseManager without connection (should create its own)
    db_manager2 = DatabaseManager(config.postgres)
    print("Created DatabaseManager 2 without connection (owns connection)")
    
    # Check connection ownership
    print(f"\nDatabaseManager 1 owns connection: {db_manager1._owns_connection}")
    print(f"DatabaseManager 2 owns connection: {db_manager2._owns_connection}")
    
    # Test connection
    print("\nTesting connection...")
    try:
        # Connect both managers
        db_manager1.connect()
        db_manager2.connect()
        print("Both managers connected successfully")
        
        # Test get_tables
        result = db_manager1.get_tables()
        if result["success"]:
            print(f"Successfully retrieved tables: {len(result.get('tables', []))} tables")
        else:
            print(f"Failed to get tables: {result.get('error')}")
        
        # Disconnect
        db_manager1.disconnect()
        db_manager2.disconnect()
        print("Both managers disconnected")
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    test_global_connection()
