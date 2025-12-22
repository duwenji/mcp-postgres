"""
Main entry point for PostgreSQL MCP Server
"""

import asyncio
import logging
import signal
import datetime
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .config import load_config, ServerConfig
from .database import DatabaseManager, ConnectionPoolManager
from .docker_manager import DockerManager
from .tools.crud_tools import (
    get_crud_tools,
    get_crud_handlers,
)
from .tools.schema_tools import get_schema_tools, get_schema_handlers
from .tools.table_tools import get_table_tools, get_table_handlers
from .tools.sampling_tools import get_sampling_tools, get_sampling_handlers
from .tools.transaction_tools import get_transaction_tools, get_transaction_handlers
from .tools.sampling_integration import (
    get_sampling_integration_tools,
    get_sampling_integration_handlers,
)
from .tools.elicitation_tools import (
    get_elicitation_tools,
    get_elicitation_handlers,
)
from .resources import (
    get_database_resources,
    get_resource_handlers,
    get_table_schema_resource_handler,
)
from .protocol_logging import (
    sanitize_log_output,
    protocol_logging_server,
)
from .prompts import get_prompt_manager
from mcp import (
    Resource,
    Tool,
    ListPromptsRequest,
    ListPromptsResult,
    GetPromptResult,
)
import mcp.types as types


def setup_logging(
    log_level: str = "INFO", log_dir: str = ""
) -> tuple[logging.Logger, logging.Logger]:
    """
    Setup logging with custom directory and log level

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Custom log directory path. If empty, uses current directory.

    Returns:
        Tuple of (general logger, protocol logger)
    """
    import os

    # ログレベルを数値に変換
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # ログディレクトリが指定されている場合は使用
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        general_log_path = os.path.join(log_dir, "mcp_postgres.log")
        protocol_log_path = os.path.join(log_dir, "mcp_protocol.log")
    else:
        general_log_path = "mcp_postgres.log"
        protocol_log_path = "mcp_protocol.log"

    # ルートロガーのリセット
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 基本ログ設定 - ファイルのみに出力（sys.stdout/sys.stderrへの出力なし）
    logger = logging.getLogger(__name__)
    logger.setLevel(numeric_level)

    # ファイルハンドラー
    file_handler = logging.FileHandler(general_log_path)
    file_handler.setLevel(numeric_level)

    # フォーマッター - ファイル名と行番号を追加
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )
    file_handler.setFormatter(formatter)

    # ファイルハンドラーのみ追加
    logger.addHandler(file_handler)
    logger.propagate = False  # 重複ログを防ぐ

    # プロトコルロガー設定 - ファイル名と行番号を追加
    protocol_logger = logging.getLogger("mcp_protocol")
    protocol_logger.setLevel(numeric_level)
    protocol_handler = logging.FileHandler(protocol_log_path)
    protocol_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        )
    )
    protocol_logger.addHandler(protocol_handler)
    protocol_logger.propagate = False  # Prevent duplicate logging

    return logger, protocol_logger


# Initialize logging with None - will be properly configured in main()
logger = None
protocol_logger = None

# Global configuration - loaded once in main()
global_config: Optional[ServerConfig] = None

# Global connection pool manager for connection pooling
global_pool_manager: Optional[ConnectionPoolManager] = None

# Graceful shutdown flag
shutdown_event = asyncio.Event()


def setup_signal_handlers() -> None:
    """Setup signal handlers for graceful shutdown"""

    def signal_handler(signum: int, frame: Any) -> None:
        # signal_handler may be called before main() initializes logger
        if logger is not None:
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def graceful_shutdown() -> None:
    """Perform graceful shutdown of server resources"""
    # logger is initialized in main() before this function is called
    if logger is None:
        # If logger is not initialized, we cannot log, but we should still proceed with shutdown
        print("Performing graceful shutdown (logger not initialized)...")
    else:
        logger.info("Performing graceful shutdown...")

    # Close database connections
    if global_pool_manager:
        try:
            global_pool_manager.disconnect()
            if logger:
                logger.info("Database connection pool closed")
        except Exception as e:
            if logger:
                logger.error(f"Error closing database connection pool: {e}")

    # Wait for ongoing operations to complete (with timeout)
    try:
        await asyncio.wait_for(shutdown_event.wait(), timeout=10.0)
        if logger:
            logger.info("All ongoing operations completed")
    except asyncio.TimeoutError:
        if logger:
            logger.warning("Timeout waiting for operations to complete")

    if logger:
        logger.info("Graceful shutdown completed")


async def health_check() -> Dict[str, Any]:
    """
    Perform health check of server components

    Returns:
        Dictionary with health status information
    """
    # Check if logger is initialized
    if logger is None:
        # If logger is not initialized, we cannot log, but we can still perform health check
        print("Health check called (logger not initialized)...")

    health_status = {
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "components": {},
    }

    # Check database connection
    if global_pool_manager:
        try:
            db_healthy = global_pool_manager.test_connection()
            health_status["components"]["database"] = {
                "status": "healthy" if db_healthy else "unhealthy",
                "connection_test": db_healthy,
            }
            if not db_healthy:
                health_status["status"] = "unhealthy"
        except Exception as e:
            health_status["components"]["database"] = {
                "status": "error",
                "error": str(e),
            }
            health_status["status"] = "unhealthy"
    else:
        health_status["components"]["database"] = {"status": "not_initialized"}
        health_status["status"] = "unhealthy"

    return health_status


@asynccontextmanager
async def lifespan(server: Server):
    """
    Lifespan context manager for MCP server lifecycle management

    Note: Initialization is now done in main() function.
    This lifespan only handles graceful shutdown.
    """
    try:
        # Startup phase - already done in main()
        assert logger is not None, "logger should be initialized"
        logger.info("PostgreSQL MCP Server lifespan started")

        # Yield control to server runtime
        yield

    except Exception as e:
        assert logger is not None, "logger should be initialized"
        logger.error(f"Server runtime error: {e}")
        raise
    finally:
        # Shutdown phase
        assert logger is not None, "logger should be initialized"
        logger.info("Starting PostgreSQL MCP Server shutdown...")
        await graceful_shutdown()
        logger.info("PostgreSQL MCP Server shutdown completed")


async def main() -> None:
    """Main entry point for the MCP server"""
    # Load configuration and setup logging at the start
    global global_config, logger, protocol_logger, global_pool_manager

    # Load configuration
    global_config = load_config()

    # Setup logging
    logger, protocol_logger = setup_logging(
        log_level=global_config.log_level, log_dir=global_config.log_dir
    )

    logger.info(f"Configuration loaded successfully. config={global_config}")

    # Handle Docker auto-setup if enabled
    if global_config.docker.enabled:
        logger.info("Docker auto-setup enabled, starting PostgreSQL container...")
        docker_manager = DockerManager(global_config.docker)

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

    # Initialize global connection pool manager
    logger.info("Initializing connection pool manager...")
    global_pool_manager = ConnectionPoolManager(global_config.postgres)

    # Test database connection
    if global_pool_manager.test_connection():
        logger.info("Connection pool manager initialized successfully")
    else:
        logger.error("Failed to initialize connection pool manager")
        raise RuntimeError("Database connection failed")

    # Set global connection pool manager for sharing across tools
    from .shared import set_global_db_connection

    set_global_db_connection(global_pool_manager, global_config)
    logger.info("Global connection pool manager set for tool sharing")

    # Setup signal handlers for graceful shutdown
    setup_signal_handlers()

    logger.info("PostgreSQL MCP Server startup completed")

    # Create MCP server with lifespan management
    server = Server("postgres-mcp-server", lifespan=lifespan)

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
    elicitation_tools = get_elicitation_tools()
    elicitation_handlers = get_elicitation_handlers()

    # Combine all tools and handlers
    all_tools = (
        crud_tools
        + schema_tools
        + table_tools
        + sampling_tools
        + transaction_tools
        + sampling_integration_tools
        + elicitation_tools
    )
    all_handlers = {
        **crud_handlers,
        **schema_handlers,
        **table_handlers,
        **sampling_handlers,
        **transaction_handlers,
        **sampling_integration_handlers,
        **elicitation_handlers,
    }

    # Register tool handlers
    @server.call_tool()
    async def handle_tool_call(name: str, arguments: dict) -> Dict[str, Any]:  # type: ignore[no-untyped-def]
        """Handle tool execution requests"""

        # global_config is initialized in main() before server starts
        assert logger is not None, "logger should be initialized"
        assert global_config is not None, "global_config should be initialized"
        logger.info(f"TOOL_INPUT - Tool: {name}, Arguments: {arguments}")

        # Handle health check tool
        if name == "health_check":
            try:
                result = await health_check()
                logger.info(f"HEALTH_CHECK_RESULT - Status: {result['status']}")
                return {"success": True, "health": result}
            except Exception as e:
                logger.error(f"HEALTH_CHECK_ERROR - Error: {e}")
                return {"success": False, "error": str(e)}

        if name in all_handlers:
            handler = all_handlers[name]
            try:
                # プロトコルデバッグモード時の追加ログ
                if global_config.protocol_debug:
                    logger.debug(f"TOOL_DEBUG - Executing handler for: {name}")
                    logger.debug(f"TOOL_DEBUG - Handler function: {handler.__name__}")

                result = await handler(**arguments)
                # 詳細な出力ログ（機密情報をマスク）
                sanitized_result = sanitize_log_output(result)
                logger.info(f"TOOL_OUTPUT - Tool: {name}, Result: {sanitized_result}")

                # プロトコルデバッグモード時の追加ログ
                if global_config.protocol_debug:
                    logger.debug(f"TOOL_DEBUG - Raw result type: {type(result)}")
                    logger.debug(
                        f"TOOL_DEBUG - Raw result keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}"
                    )

                return result
            except Exception as e:
                logger.error(f"TOOL_ERROR - Tool: {name}, Error: {e}")
                # プロトコルデバッグモード時の詳細なエラー情報
                if global_config.protocol_debug:
                    import traceback

                    logger.debug(
                        f"TOOL_DEBUG - Error traceback: {traceback.format_exc()}"
                    )
                return {"success": False, "error": str(e)}
        else:
            logger.error(f"TOOL_UNKNOWN - Tool: {name}")
            # JSON-RPC 2.0準拠のエラーレスポンスを返す
            return {
                "success": False,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {name}",
                    "data": {
                        "available_methods": list(all_handlers.keys())
                        + ["health_check"],
                        "server_type": "PostgreSQL MCP Server",
                    },
                },
            }

    # Register tools via list_tools handler
    @server.list_tools()
    async def handle_list_tools() -> List[Tool]:
        """List available tools including health check"""
        # Check if logger is initialized
        if logger is not None:
            tool_count = len(all_tools) + 1  # +1 for health check
            logger.info(f"TOOL_LIST - Listing {tool_count} available tools")

        # Create health check tool definition
        health_tool = Tool(
            name="health_check",
            description="Check the health status of the PostgreSQL MCP Server",
            inputSchema={"type": "object", "properties": {}, "required": []},
        )

        return all_tools + [health_tool]

    # Register resources
    database_resources = get_database_resources()
    resource_handlers = get_resource_handlers()
    table_schema_handler = get_table_schema_resource_handler()

    @server.list_resources()
    async def handle_list_resources() -> List[Resource]:
        """List available resources"""
        # Check if logger is initialized
        if logger is not None:
            logger.info("RESOURCE_LIST - Listing available resources")
        resources = database_resources.copy()

        # Add dynamic table schema resources
        try:
            if global_config is None:
                raise RuntimeError("global_config should be initialized")
            db_manager = DatabaseManager(global_config.postgres, global_pool_manager)
            db_manager.connect()
            tables_result = db_manager.get_tables()
            db_manager.disconnect()

            if tables_result["success"]:
                # Convert to List[str] to fix mypy error
                tables_data = tables_result["tables"]
                table_list: List[str] = list(tables_data)  # type: ignore[index]
                table_count = len(table_list)
                if logger is not None:
                    logger.info(
                        f"RESOURCE_LIST - Found {table_count} tables in database"
                    )
                for table_name in table_list:
                    resources.append(
                        Resource(
                            uri=f"database://schema/{table_name}",  # type: ignore
                            name=f"Table Schema: {table_name}",
                            description=f"Schema information for table {table_name}",
                            mimeType="text/markdown",
                        )
                    )
            else:
                if logger is not None:
                    logger.warning(
                        f"RESOURCE_LIST - Failed to get tables: {tables_result.get('error', 'Unknown error')}"
                    )
        except Exception as e:
            if logger is not None:
                logger.error(
                    f"RESOURCE_LIST_ERROR - Error listing table resources: {e}"
                )

        total_resources = len(resources)
        if logger is not None:
            logger.info(f"RESOURCE_LIST - Total resources available: {total_resources}")
        return resources

    @server.list_resource_templates()
    async def handle_list_resource_templates() -> List[types.ResourceTemplate]:
        """List available resource templates"""
        # Check if logger is initialized
        if logger is not None:
            logger.info("RESOURCE_TEMPLATE_LIST - Listing resource templates")
        # Currently no resource templates implemented
        return []

    @server.read_resource()
    async def handle_read_resource(uri: str) -> str:
        """Read resource content"""
        # Assert logger is initialized (for mypy type narrowing)
        assert logger is not None, "logger should be initialized"

        # Convert uri to string if it's not already
        uri_str = str(uri)
        logger.info(f"RESOURCE_READ - Reading resource: {uri_str}")

        # Handle static resources
        if uri_str in resource_handlers:
            logger.info(f"RESOURCE_READ - Handling static resource: {uri_str}")
            handler = resource_handlers[uri_str]
            try:
                content = await handler()
                content_length = len(content) if content else 0
                logger.info(
                    f"RESOURCE_READ_SUCCESS - Resource: {uri_str}, Content length: {content_length}"
                )
                return content
            except Exception as e:
                logger.error(f"RESOURCE_READ_ERROR - Resource: {uri_str}, Error: {e}")
                return f"Error reading resource {uri_str}: {e}"

        # Handle dynamic table schema resources
        if uri_str.startswith("database://schema/"):
            table_name = uri_str.replace("database://schema/", "")
            logger.info(f"RESOURCE_READ - Handling table schema resource: {table_name}")
            try:
                content = await table_schema_handler(table_name, "public")
                content_length = len(content) if content else 0
                logger.info(
                    f"RESOURCE_READ_SUCCESS - Table schema: {table_name}, Content length: {content_length}"
                )
                return content
            except Exception as e:
                logger.error(
                    f"RESOURCE_READ_ERROR - Table schema: {table_name}, Error: {e}"
                )
                return f"Error reading table schema {table_name}: {e}"

        logger.warning(f"RESOURCE_NOT_FOUND - Resource: {uri_str}")
        return f"Resource {uri_str} not found"

    @server.list_prompts()
    async def handle_list_prompts(request: ListPromptsRequest) -> ListPromptsResult:
        """List available prompts"""
        # Check if logger is initialized
        if logger is not None:
            logger.info("PROMPT_LIST - Listing available prompts")
        try:
            prompt_manager = get_prompt_manager()
            prompts = prompt_manager.list_prompts()
            prompt_count = len(prompts)
            if logger is not None:
                logger.info(f"PROMPT_LIST_SUCCESS - Found {prompt_count} prompts")
            return ListPromptsResult(prompts=prompts)
        except Exception as e:
            if logger is not None:
                logger.error(f"PROMPT_LIST_ERROR - Error listing prompts: {e}")
            return ListPromptsResult(prompts=[])

    @server.get_prompt()
    async def handle_get_prompt(
        name: str, arguments: dict[str, str] | None
    ) -> GetPromptResult:
        """Get prompt content"""
        # Assert logger is initialized (for mypy type narrowing)
        assert logger is not None, "logger should be initialized"

        logger.info(f"PROMPT_GET - Getting prompt: {name}, arguments: {arguments}")
        try:
            prompt_manager = get_prompt_manager()
            # Convert arguments to Dict[str, Any] if needed
            args_dict: Dict[str, Any] = {}
            if arguments:
                # Convert dict[str, str] to Dict[str, Any]
                args_dict = {k: v for k, v in arguments.items()}

            prompt = prompt_manager.get_prompt(name, args_dict)

            if prompt:
                logger.info(f"PROMPT_GET_SUCCESS - Found prompt: {name}")
                # For now, return empty messages since MCP Prompt doesn't contain message content
                # In a real implementation, we would need to store the actual message content separately
                return GetPromptResult(description=prompt.description, messages=[])
            else:
                logger.warning(f"PROMPT_NOT_FOUND - Prompt not found: {name}")
                return GetPromptResult(description="", messages=[])
        except Exception as e:
            logger.error(f"PROMPT_GET_ERROR - Error getting prompt {name}: {e}")
            return GetPromptResult(description="", messages=[])

    # Start the server
    if logger is None:
        raise RuntimeError("logger should be initialized")
    if global_config is None:
        raise RuntimeError("global_config should be initialized")
    if protocol_logger is None:
        raise RuntimeError("protocol_logger should be initialized")

    logger.info("Starting PostgreSQL MCP Server...")

    try:
        async with stdio_server() as (read_stream, write_stream):
            # プロトコルロギングを有効化
            read_stream, write_stream = await protocol_logging_server(
                read_stream, write_stream, global_config, protocol_logger
            )

            await server.run(
                read_stream, write_stream, server.create_initialization_options()
            )

    except Exception as e:
        logger.error(f"Server error: {e}")
        import traceback

        logger.error(f"Server error traceback: {traceback.format_exc()}")
        # 詳細なエラー情報はファイルにのみ出力（sys.stderr/sys.stdoutへの出力なし）
        # 既にlogger.errorでファイルに出力されているため、追加の出力は不要
        raise


def cli_main() -> None:
    """CLI entry point for uv run"""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()
