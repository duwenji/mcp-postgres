"""
Main entry point for PostgreSQL MCP Server
"""

import asyncio
import logging
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .config import load_config
from .database import DatabaseManager
from .tools.crud_tools import get_crud_tools, get_crud_handlers
from .tools.schema_tools import get_schema_tools, get_schema_handlers
from .resources import (
    get_database_resources,
    get_resource_handlers,
    get_table_schema_resource_handler,
)
from mcp import Resource

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point for the MCP server"""
    try:
        # Load configuration
        config = load_config()
        logger.info("Configuration loaded successfully")

    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Create MCP server
    server = Server("postgres-mcp-server")

    # Get tools and handlers
    crud_tools = get_crud_tools()
    crud_handlers = get_crud_handlers()
    schema_tools = get_schema_tools()
    schema_handlers = get_schema_handlers()

    # Combine all tools and handlers
    all_tools = crud_tools + schema_tools
    all_handlers = {**crud_handlers, **schema_handlers}

    # Register tool handlers
    @server.call_tool()
    async def handle_tool_call(name: str, arguments: dict) -> dict:
        """Handle tool execution requests"""
        logger.info(f"Tool call: {name} with arguments: {arguments}")

        if name in all_handlers:
            handler = all_handlers[name]
            try:
                result = await handler(**arguments)
                logger.info(f"Tool {name} executed successfully")
                return result
            except Exception as e:
                logger.error(f"Tool {name} execution failed: {e}")
                return {"success": False, "error": str(e)}
        else:
            logger.error(f"Unknown tool: {name}")
            return {"success": False, "error": f"Unknown tool: {name}"}

    # Register tools via list_tools handler
    @server.list_tools()
    async def handle_list_tools() -> list:
        """List available tools"""
        logger.info("Listing available tools")
        return all_tools

    # Register resources
    database_resources = get_database_resources()
    resource_handlers = get_resource_handlers()
    table_schema_handler = get_table_schema_resource_handler()

    @server.list_resources()
    async def handle_list_resources() -> list:
        """List available resources"""
        resources = database_resources.copy()

        # Add dynamic table schema resources
        try:
            config = load_config()
            db_manager = DatabaseManager(config.postgres)
            db_manager.connection.connect()
            tables_result = db_manager.get_tables()
            db_manager.connection.disconnect()

            if tables_result["success"]:
                for table_name in tables_result["tables"]:
                    resources.append(
                        Resource(
                            uri=f"database://schema/{table_name}",
                            name=f"Table Schema: {table_name}",
                            description=f"Schema information for table {table_name}",
                            mimeType="text/markdown",
                        )
                    )
        except Exception as e:
            logger.error(f"Error listing table resources: {e}")

        return resources

    @server.read_resource()
    async def handle_read_resource(uri: str) -> str:
        """Read resource content"""
        logger.info(f"Reading resource: {uri}")

        # Handle static resources
        if uri in resource_handlers:
            handler = resource_handlers[uri]
            return await handler()

        # Handle dynamic table schema resources
        if uri.startswith("database://schema/"):
            table_name = uri.replace("database://schema/", "")
            return await table_schema_handler(table_name)

        return f"Resource {uri} not found"

    # Start the server
    logger.info("Starting PostgreSQL MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


def cli_main():
    """CLI entry point for uv run"""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()
