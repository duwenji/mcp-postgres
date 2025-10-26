"""
CRUD tools for PostgreSQL MCP Server
"""

import logging
from typing import Any, Dict, List, Optional, Callable, Coroutine
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
                "description": ("Dictionary of column names and values to insert"),
                "additionalProperties": True,
            },
        },
        "required": ["table_name", "data"],
    },
)


read_entity = Tool(
    name="read_entity",
    description="Read entities from a PostgreSQL table with optional conditions and advanced features",
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
                "description": ("Maximum number of rows to return (default: 100)"),
                "default": 100,
                "minimum": 1,
                "maximum": 1000,
            },
            "offset": {
                "type": "integer",
                "description": "Number of rows to skip (for pagination, default: 0)",
                "default": 0,
                "minimum": 0,
            },
            "order_by": {
                "type": "string",
                "description": "Column name to order by",
            },
            "order_direction": {
                "type": "string",
                "description": "Order direction (ASC or DESC, default: ASC)",
                "enum": ["ASC", "DESC"],
                "default": "ASC",
            },
            "aggregate": {
                "type": "string",
                "description": "Aggregate function (e.g., COUNT(*), SUM(column), AVG(column))",
            },
            "group_by": {
                "type": "string",
                "description": "Column name to group by",
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
                "description": ("WHERE conditions to identify which rows to update"),
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
                "description": ("WHERE conditions to identify which rows to delete"),
                "additionalProperties": True,
            },
        },
        "required": ["table_name", "conditions"],
    },
)


# Batch operation tool definitions
batch_create_entities = Tool(
    name="batch_create_entities",
    description="Create multiple entities in a single operation",
    inputSchema={
        "type": "object",
        "properties": {
            "table_name": {
                "type": "string",
                "description": "Name of the table to insert into",
            },
            "data_list": {
                "type": "array",
                "description": "List of dictionaries containing column names and values",
                "items": {
                    "type": "object",
                    "additionalProperties": True,
                },
            },
        },
        "required": ["table_name", "data_list"],
    },
)

batch_update_entities = Tool(
    name="batch_update_entities",
    description="Update multiple entities with different conditions and updates",
    inputSchema={
        "type": "object",
        "properties": {
            "table_name": {
                "type": "string",
                "description": "Name of the table to update",
            },
            "conditions_list": {
                "type": "array",
                "description": "List of WHERE conditions for each entity",
                "items": {
                    "type": "object",
                    "additionalProperties": True,
                },
            },
            "updates_list": {
                "type": "array",
                "description": "List of updates for each entity",
                "items": {
                    "type": "object",
                    "additionalProperties": True,
                },
            },
        },
        "required": ["table_name", "conditions_list", "updates_list"],
    },
)

batch_delete_entities = Tool(
    name="batch_delete_entities",
    description="Delete multiple entities with different conditions",
    inputSchema={
        "type": "object",
        "properties": {
            "table_name": {
                "type": "string",
                "description": "Name of the table to delete from",
            },
            "conditions_list": {
                "type": "array",
                "description": "List of WHERE conditions for each entity",
                "items": {
                    "type": "object",
                    "additionalProperties": True,
                },
            },
        },
        "required": ["table_name", "conditions_list"],
    },
)


# Tool handlers
async def handle_create_entity(table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle create entity tool execution"""
    try:
        config = load_config()
        db_manager = DatabaseManager(config.postgres)

        # Connect to database
        db_manager.connect()

        result = db_manager.create_entity(table_name, data)

        # Disconnect from database
        db_manager.disconnect()

        return result

    except DatabaseError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in create_entity: {e}")
        return {"success": False, "error": f"Internal server error: {str(e)}"}


async def handle_read_entity(
    table_name: str,
    conditions: Optional[Dict[str, Any]] = None,
    limit: int = 100,
    offset: int = 0,
    order_by: Optional[str] = None,
    order_direction: str = "ASC",
    aggregate: Optional[str] = None,
    group_by: Optional[str] = None,
) -> Dict[str, Any]:
    """Handle read entity tool execution with advanced features"""
    try:
        config = load_config()
        db_manager = DatabaseManager(config.postgres)

        # Connect to database
        db_manager.connect()

        result = db_manager.read_entity(
            table_name=table_name,
            conditions=conditions,
            limit=limit,
            offset=offset,
            order_by=order_by,
            order_direction=order_direction,
            aggregate=aggregate,
            group_by=group_by,
        )

        # Disconnect from database
        db_manager.disconnect()

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
        db_manager.connect()

        result = db_manager.update_entity(table_name, conditions, updates)

        # Disconnect from database
        db_manager.disconnect()

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
        db_manager.connect()

        result = db_manager.delete_entity(table_name, conditions)

        # Disconnect from database
        db_manager.disconnect()

        return result

    except DatabaseError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in delete_entity: {e}")
        return {"success": False, "error": f"Internal server error: {str(e)}"}


# Batch operation handlers
async def handle_batch_create_entities(
    table_name: str, data_list: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Handle batch create entities tool execution"""
    try:
        config = load_config()
        db_manager = DatabaseManager(config.postgres)

        # Connect to database
        db_manager.connect()

        result = db_manager.batch_create_entities(table_name, data_list)

        # Disconnect from database
        db_manager.disconnect()

        return result

    except DatabaseError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in batch_create_entities: {e}")
        return {"success": False, "error": f"Internal server error: {str(e)}"}


async def handle_batch_update_entities(
    table_name: str,
    conditions_list: List[Dict[str, Any]],
    updates_list: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Handle batch update entities tool execution"""
    try:
        config = load_config()
        db_manager = DatabaseManager(config.postgres)

        # Connect to database
        db_manager.connect()

        result = db_manager.batch_update_entities(
            table_name, conditions_list, updates_list
        )

        # Disconnect from database
        db_manager.disconnect()

        return result

    except DatabaseError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in batch_update_entities: {e}")
        return {"success": False, "error": f"Internal server error: {str(e)}"}


async def handle_batch_delete_entities(
    table_name: str, conditions_list: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Handle batch delete entities tool execution"""
    try:
        config = load_config()
        db_manager = DatabaseManager(config.postgres)

        # Connect to database
        db_manager.connect()

        result = db_manager.batch_delete_entities(table_name, conditions_list)

        # Disconnect from database
        db_manager.disconnect()

        return result

    except DatabaseError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in batch_delete_entities: {e}")
        return {"success": False, "error": f"Internal server error: {str(e)}"}


# Tool registry
def get_crud_tools() -> List[Tool]:
    """Get all CRUD tools including batch operations"""
    return [
        create_entity,
        read_entity,
        update_entity,
        delete_entity,
        batch_create_entities,
        batch_update_entities,
        batch_delete_entities,
    ]


def get_crud_handlers() -> (
    Dict[str, Callable[..., Coroutine[Any, Any, Dict[str, Any]]]]
):
    """Get tool handlers for CRUD operations including batch operations"""
    return {
        "create_entity": handle_create_entity,
        "read_entity": handle_read_entity,
        "update_entity": handle_update_entity,
        "delete_entity": handle_delete_entity,
        "batch_create_entities": handle_batch_create_entities,
        "batch_update_entities": handle_batch_update_entities,
        "batch_delete_entities": handle_batch_delete_entities,
    }
