"""
Main entry point for PostgreSQL MCP Server
"""

import asyncio
import logging
import sys
from typing import Any, Dict, List
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .config import load_config
from .database import DatabaseManager
from .docker_manager import DockerManager
from .tools.crud_tools import get_crud_tools, get_crud_handlers
from .tools.schema_tools import get_schema_tools, get_schema_handlers
from .tools.table_tools import get_table_tools, get_table_handlers
from .tools.sampling_tools import get_sampling_tools, get_sampling_handlers
from .tools.transaction_tools import get_transaction_tools, get_transaction_handlers
from .tools.sampling_integration import (
    get_sampling_integration_tools,
    get_sampling_integration_handlers,
)
from .resources import (
    get_database_resources,
    get_resource_handlers,
    get_table_schema_resource_handler,
)
from mcp import Resource, Tool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("mcp_postgres.log"),  # ファイルへのログ出力
        logging.StreamHandler(sys.stderr),  # 標準エラー出力にも出力
    ],
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Main entry point for the MCP server"""
    try:
        # Load configuration
        config = load_config()
        logger.info(f"Configuration loaded successfully. config={config}")

        # Handle Docker auto-setup if enabled
        if config.docker.enabled:
            logger.info("Docker auto-setup enabled, starting PostgreSQL container...")
            docker_manager = DockerManager(config.docker)

            if docker_manager.is_docker_available():
                result = docker_manager.start_container()
                if result["success"]:
                    logger.info(f"PostgreSQL container started successfully: {result}")
                else:
                    logger.error(
                        f"Failed to start PostgreSQL container: {result.get('error', 'Unknown error')}"
                    )
                    # Continue without Docker setup - user might have external PostgreSQL
            else:
                logger.warning(
                    "Docker auto-setup enabled but Docker is not available. Using existing PostgreSQL connection."
                )

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
    table_tools = get_table_tools()
    table_handlers = get_table_handlers()
    sampling_tools = get_sampling_tools()
    sampling_handlers = get_sampling_handlers()
    transaction_tools = get_transaction_tools()
    transaction_handlers = get_transaction_handlers()
    sampling_integration_tools = get_sampling_integration_tools()
    sampling_integration_handlers = get_sampling_integration_handlers()

    # Combine all tools and handlers
    all_tools = (
        crud_tools
        + schema_tools
        + table_tools
        + sampling_tools
        + transaction_tools
        + sampling_integration_tools
    )
    all_handlers = {
        **crud_handlers,
        **schema_handlers,
        **table_handlers,
        **sampling_handlers,
        **transaction_handlers,
        **sampling_integration_handlers,
    }

    # Register tool handlers
    @server.call_tool()
    async def handle_tool_call(name: str, arguments: dict) -> Dict[str, Any]:
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
    async def handle_list_tools() -> List[Tool]:
        """List available tools"""
        logger.info("Listing available tools")
        return all_tools

    # Register resources
    database_resources = get_database_resources()
    resource_handlers = get_resource_handlers()
    table_schema_handler = get_table_schema_resource_handler()

    @server.list_resources()
    async def handle_list_resources() -> List[Resource]:
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
                            uri=f"database://schema/{table_name}",  # type: ignore
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
        # Convert uri to string if it's not already
        uri_str = str(uri)
        logger.info(f"Reading resource: {uri_str}")

        # Handle static resources
        if uri_str in resource_handlers:
            handler = resource_handlers[uri_str]
            return await handler()

        # Handle dynamic table schema resources
        if uri_str.startswith("database://schema/"):
            table_name = uri_str.replace("database://schema/", "")
            return await table_schema_handler(table_name, "public")

        return f"Resource {uri_str} not found"

    # Start the server
    logger.info("Starting PostgreSQL MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


def cli_main() -> None:
    """CLI entry point for uv run"""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()
