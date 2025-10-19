"""
CRUD tools for PostgreSQL MCP Server
"""

import logging
from typing import Any, Dict, List, Optional
from mcp import Tool

from ..database import DatabaseManager, DatabaseError
from ..config import load_config

logger = logging.getLogger(__name__)


# Tool definitions for CRUD operations
create_entity = Tool(
    name="create_entity",
    description="Create a new entity (row) in a PostgreSQL table",
    inputSchema={
        "type": "object",
        "properties": {
            "table_name": {
                "type": "string",
                "description": "Name of the table to insert into",
            },
            "data": {
                "type": "object",
                "description": "Dictionary of column names and values to insert",
                "additionalProperties": True,
            },
        },
        "required": ["table_name", "data"],
    },
)


read_entity = Tool(
    name="read_entity",
    description="Read entities from a PostgreSQL table with optional conditions",
    inputSchema={
        "type": "object",
        "properties": {
            "table_name": {
                "type": "string",
                "description": "Name of the table to query",
            },
            "conditions": {
                "type": "object",
                "description": "Optional WHERE conditions as key-value pairs",
                "additionalProperties": True,
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of rows to return (default: 100)",
                "default": 100,
                "minimum": 1,
                "maximum": 1000,
            },
        },
        "required": ["table_name"],
    },
)


update_entity = Tool(
    name="update_entity",
    description="Update entities in a PostgreSQL table",
    inputSchema={
        "type": "object",
        "properties": {
            "table_name": {
                "type": "string",
                "description": "Name of the table to update",
            },
            "conditions": {
                "type": "object",
                "description": "WHERE conditions to identify which rows to update",
                "additionalProperties": True,
            },
            "updates": {
                "type": "object",
                "description": "Dictionary of columns and values to update",
                "additionalProperties": True,
            },
        },
        "required": ["table_name", "conditions", "updates"],
    },
)


delete_entity = Tool(
    name="delete_entity",
    description="Delete entities from a PostgreSQL table",
    inputSchema={
        "type": "object",
        "properties": {
            "table_name": {
                "type": "string",
                "description": "Name of the table to delete from",
            },
            "conditions": {
                "type": "object",
                "description": "WHERE conditions to identify which rows to delete",
                "additionalProperties": True,
            },
        },
        "required": ["table_name", "conditions"],
    },
)


# Tool handlers
async def handle_create_entity(table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle create entity tool execution"""
    try:
        config = load_config()
        db_manager = DatabaseManager(config.postgres)

        # Connect to database
        db_manager.connection.connect()

        result = db_manager.create_entity(table_name, data)

        # Disconnect from database
        db_manager.connection.disconnect()

        return result

    except DatabaseError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in create_entity: {e}")
        return {"success": False, "error": f"Internal server error: {str(e)}"}


async def handle_read_entity(
    table_name: str, conditions: Optional[Dict[str, Any]] = None, limit: int = 100
) -> Dict[str, Any]:
    """Handle read entity tool execution"""
    try:
        config = load_config()
        db_manager = DatabaseManager(config.postgres)

        # Connect to database
        db_manager.connection.connect()

        result = db_manager.read_entity(table_name, conditions, limit)

        # Disconnect from database
        db_manager.connection.disconnect()

        return result

    except DatabaseError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in read_entity: {e}")
        return {"success": False, "error": f"Internal server error: {str(e)}"}


async def handle_update_entity(
    table_name: str, conditions: Dict[str, Any], updates: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle update entity tool execution"""
    try:
        config = load_config()
        db_manager = DatabaseManager(config.postgres)

        # Connect to database
        db_manager.connection.connect()

        result = db_manager.update_entity(table_name, conditions, updates)

        # Disconnect from database
        db_manager.connection.disconnect()

        return result

    except DatabaseError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in update_entity: {e}")
        return {"success": False, "error": f"Internal server error: {str(e)}"}


async def handle_delete_entity(
    table_name: str, conditions: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle delete entity tool execution"""
    try:
        config = load_config()
        db_manager = DatabaseManager(config.postgres)

        # Connect to database
        db_manager.connection.connect()

        result = db_manager.delete_entity(table_name, conditions)

        # Disconnect from database
        db_manager.connection.disconnect()

        return result

    except DatabaseError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in delete_entity: {e}")
        return {"success": False, "error": f"Internal server error: {str(e)}"}


# Tool registry
def get_crud_tools() -> List[Tool]:
    """Get all CRUD tools"""
    return [
        create_entity,
        read_entity,
        update_entity,
        delete_entity,
    ]


def get_crud_handlers() -> Dict[str, callable]:
    """Get tool handlers for CRUD operations"""
    return {
        "create_entity": handle_create_entity,
        "read_entity": handle_read_entity,
        "update_entity": handle_update_entity,
        "delete_entity": handle_delete_entity,
    }
