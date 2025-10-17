"""
Main entry point for PostgreSQL MCP Server
"""

import asyncio
import logging
import sys
from mcp import MCPServer
from mcp.server.stdio import stdio_server

from .config import load_config
from .tools.crud_tools import get_crud_tools, get_crud_handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
    server = MCPServer("postgres-mcp-server")
    
    # Register tools
    crud_tools = get_crud_tools()
    crud_handlers = get_crud_handlers()
    
    for tool in crud_tools:
        server.register_tool(tool)
        logger.info(f"Registered tool: {tool.name}")
    
    # Register tool handlers
    @server.call_tool()
    async def handle_tool_call(name: str, arguments: dict) -> dict:
        """Handle tool execution requests"""
        logger.info(f"Tool call: {name} with arguments: {arguments}")
        
        if name in crud_handlers:
            handler = crud_handlers[name]
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
    
    # Register resources (placeholder for future implementation)
    @server.list_resources()
    async def handle_list_resources() -> list:
        """List available resources"""
        return []
    
    @server.read_resource()
    async def handle_read_resource(uri: str) -> str:
        """Read resource content"""
        return f"Resource {uri} not found"
    
    # Start the server
    logger.info("Starting PostgreSQL MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
