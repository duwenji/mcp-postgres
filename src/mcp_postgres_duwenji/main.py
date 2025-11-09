"""
Main entry point for PostgreSQL MCP Server
"""

import asyncio
import json
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


def setup_logging(log_dir: str = "") -> tuple[logging.Logger, logging.Logger]:
    """
    Setup logging with custom directory

    Args:
        log_dir: Custom log directory path. If empty, uses current directory.

    Returns:
        Tuple of (general logger, protocol logger)
    """
    import os

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

    # 基本ログ設定 - ファイルと標準出力の両方に出力
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # ファイルハンドラー
    file_handler = logging.FileHandler(general_log_path)
    file_handler.setLevel(logging.DEBUG)

    # 標準出力ハンドラー（フォールバック用）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # フォーマッター
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # ハンドラーを追加
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False  # 重複ログを防ぐ

    # プロトコルロガー設定
    protocol_logger = logging.getLogger("mcp_protocol")
    protocol_logger.setLevel(logging.DEBUG)
    protocol_handler = logging.FileHandler(protocol_log_path)
    protocol_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    protocol_logger.addHandler(protocol_handler)
    protocol_logger.propagate = False  # Prevent duplicate logging

    return logger, protocol_logger


# Initialize logging with None - will be properly configured in main()
logger = None
protocol_logger = None

# Global configuration - loaded once in main()
global_config = None


def sanitize_log_output(result: Any) -> Any:
    """
    ログ出力用に機密情報をマスクする関数

    Args:
        result: ログ出力する結果データ

    Returns:
        機密情報がマスクされた結果データ
    """
    if isinstance(result, dict):
        sanitized = result.copy()
        # 機密情報を含む可能性のあるフィールドをマスク
        sensitive_fields = ["password", "secret", "token", "key", "auth"]
        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = "***MASKED***"

        # ネストされた辞書も再帰的に処理
        for key, value in sanitized.items():
            if isinstance(value, dict):
                sanitized[key] = sanitize_log_output(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    sanitize_log_output(item) if isinstance(item, dict) else item
                    for item in value
                ]

        return sanitized
    elif isinstance(result, list):
        return [
            sanitize_log_output(item) if isinstance(item, dict) else item
            for item in result
        ]
    else:
        return result


def sanitize_protocol_message(message: str) -> str:
    """
    MCPプロトコルメッセージの機密情報をマスクする関数

    Args:
        message: JSON形式のプロトコルメッセージ

    Returns:
        機密情報がマスクされたメッセージ
    """
    try:
        data = json.loads(message)
        sanitized_data = sanitize_log_output(data)
        return json.dumps(sanitized_data, ensure_ascii=False)
    except (json.JSONDecodeError, TypeError):
        # JSONとして解析できない場合は元のメッセージを返す
        return message


class ProtocolLoggingReceiveStream:
    """
    MCPプロトコルメッセージをログに記録する受信ストリームラッパー
    """

    def __init__(
        self, original_stream: Any, logger_instance: logging.Logger | None = None
    ) -> None:
        self.original_stream = original_stream
        self.logger = logger_instance or protocol_logger

        if self.logger:
            self.logger.debug(
                f"PROTOCOL_RECEIVE_STREAM_INIT - original_stream_type: {type(original_stream)}"
            )

    async def receive(self) -> Any:
        """受信操作をラップしてログに記録"""
        try:
            if self.logger:
                self.logger.debug("RECEIVE_START - Waiting for message")

            # 元のストリームのreceiveメソッドを呼び出し
            data = await self.original_stream.receive()

            if self.logger:
                self.logger.debug(
                    f"RECEIVE_COMPLETE - data_received: {data is not None}, data_type: {type(data)}"
                )

            if data is not None:
                try:
                    if self.logger:
                        # データがbytes型の場合はデコードしてログに記録
                        if isinstance(data, bytes):
                            message = data.decode("utf-8").strip()
                            if message:
                                sanitized_message = sanitize_protocol_message(message)
                                self.logger.debug(f"REQUEST: {sanitized_message}")
                            else:
                                self.logger.debug(
                                    "REQUEST_EMPTY - Empty message received"
                                )
                        else:
                            # その他の型の場合は文字列化してログに記録
                            message_str = str(data)
                            sanitized_message = sanitize_protocol_message(message_str)
                            self.logger.debug(f"REQUEST: {sanitized_message}")
                except Exception as e:
                    # loggerがNoneの場合でもエラーを出力しない
                    if self.logger:
                        self.logger.error(f"Error logging request: {e}")
            return data
        except Exception as e:
            # 詳細なエラー情報をログに記録
            if self.logger:
                import traceback

                self.logger.error(
                    f"RECEIVE_ERROR - error: {e}, traceback: {traceback.format_exc()}"
                )
            raise e

    async def __aenter__(self) -> Any:
        """非同期コンテキストマネージャーのエントリーポイント"""
        # 常にselfを返す - これが非同期コンテキストマネージャーの正しい実装
        try:
            if hasattr(self.original_stream, "__aenter__"):
                await self.original_stream.__aenter__()
        except Exception as e:
            # 元のストリームのエントリーポイントでエラーが発生した場合
            if self.logger:
                self.logger.error(f"Error in original stream __aenter__: {e}")
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Any:
        """非同期コンテキストマネージャーの終了ポイント"""
        try:
            if hasattr(self.original_stream, "__aexit__"):
                return await self.original_stream.__aexit__(exc_type, exc_val, exc_tb)
        except Exception as e:
            # 元のストリームの終了ポイントでエラーが発生した場合
            if self.logger:
                self.logger.error(f"Error in original stream __aexit__: {e}")
        return False

    def __getattr__(self, name: str) -> Any:
        """他のメソッドは元のストリームに委譲"""
        try:
            return getattr(self.original_stream, name)
        except AttributeError:
            # 元のストリームにメソッドがない場合はAttributeErrorをそのまま送出
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )

    def __aiter__(self) -> "ProtocolLoggingReceiveStream":
        """非同期イテレーターをサポート"""
        return self

    async def __anext__(self) -> Any:
        """非同期イテレーターの次の要素を返す"""
        try:
            data = await self.receive()
            if data is None:
                raise StopAsyncIteration
            return data
        except Exception as e:
            # 適切なエラーハンドリング
            if isinstance(e, StopAsyncIteration):
                raise
            # 元の例外を保持したままStopAsyncIterationを送出
            # これによりデバッグ情報が失われない
            if self.logger:
                self.logger.error(f"Async iteration error: {e}")
            raise StopAsyncIteration from e


class ProtocolLoggingSendStream:
    """
    MCPプロトコルメッセージをログに記録する送信ストリームラッパー
    """

    def __init__(
        self, original_stream: Any, logger_instance: logging.Logger | None = None
    ) -> None:
        self.original_stream = original_stream
        self.logger = logger_instance or protocol_logger

        if self.logger:
            self.logger.debug(
                f"PROTOCOL_SEND_STREAM_INIT - original_stream_type: {type(original_stream)}"
            )

    async def send(self, item: Any) -> None:
        """送信操作をラップしてログに記録"""
        try:
            if self.logger:
                self.logger.debug(
                    f"SEND_START - item_type: {type(item)}, item_not_none: {item is not None}"
                )

            if item is not None:
                try:
                    if self.logger:
                        # データがbytes型の場合はデコードしてログに記録
                        if isinstance(item, bytes):
                            message = item.decode("utf-8").strip()
                            if message:
                                sanitized_message = sanitize_protocol_message(message)
                                self.logger.debug(f"RESPONSE: {sanitized_message}")
                            else:
                                self.logger.debug(
                                    "RESPONSE_EMPTY - Empty message to send"
                                )
                        else:
                            # その他の型の場合は文字列化してログに記録
                            message_str = str(item)
                            sanitized_message = sanitize_protocol_message(message_str)
                            self.logger.debug(f"RESPONSE: {sanitized_message}")
                except Exception as e:
                    # loggerがNoneの場合でもエラーを出力しない
                    if self.logger:
                        self.logger.error(f"Error logging response: {e}")

            # 元のストリームのsendメソッドを呼び出し
            await self.original_stream.send(item)

            if self.logger:
                self.logger.debug("SEND_COMPLETE - Message sent successfully")

        except Exception as e:
            # 詳細なエラー情報をログに記録
            if self.logger:
                import traceback

                self.logger.error(
                    f"SEND_ERROR - error: {e}, traceback: {traceback.format_exc()}"
                )
            raise e

    async def __aenter__(self) -> Any:
        """非同期コンテキストマネージャーのエントリーポイント"""
        # 常にselfを返す - これが非同期コンテキストマネージャーの正しい実装
        try:
            if hasattr(self.original_stream, "__aenter__"):
                await self.original_stream.__aenter__()
        except Exception as e:
            # 元のストリームのエントリーポイントでエラーが発生した場合
            if self.logger:
                self.logger.error(f"Error in original stream __aenter__: {e}")
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Any:
        """非同期コンテキストマネージャーの終了ポイント"""
        try:
            if hasattr(self.original_stream, "__aexit__"):
                return await self.original_stream.__aexit__(exc_type, exc_val, exc_tb)
        except Exception as e:
            # 元のストリームの終了ポイントでエラーが発生した場合
            if self.logger:
                self.logger.error(f"Error in original stream __aexit__: {e}")
        return False

    def __getattr__(self, name: str) -> Any:
        """他のメソッドは元のストリームに委譲"""
        try:
            return getattr(self.original_stream, name)
        except AttributeError:
            # 元のストリームにメソッドがない場合はAttributeErrorをそのまま送出
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )


async def protocol_logging_server(
    read_stream: Any, write_stream: Any
) -> tuple[Any, Any]:
    """
    MCPプロトコルメッセージをログに記録するラッパーサーバー

    Args:
        read_stream: 入力ストリーム
        write_stream: 出力ストリーム

    Returns:
        ラップされたストリームのタプル
    """
    if protocol_logger:
        protocol_logger.debug("PROTOCOL_LOGGING_SERVER - Starting stream wrapping")

    # 入出力ストリームをラップ
    wrapped_read_stream = ProtocolLoggingReceiveStream(read_stream)
    wrapped_write_stream = ProtocolLoggingSendStream(write_stream)

    if protocol_logger:
        protocol_logger.debug("PROTOCOL_LOGGING_SERVER - Stream wrapping completed")

    return wrapped_read_stream, wrapped_write_stream


async def main() -> None:
    """Main entry point for the MCP server"""
    try:
        # Load configuration once and store globally
        global global_config
        global_config = load_config()

        # ログ設定を再適用（カスタムディレクトリを反映）
        global logger, protocol_logger
        try:
            logger, protocol_logger = setup_logging(global_config.log_dir)
            logger.info(f"Configuration loaded successfully. config={global_config}")
        except Exception as log_error:
            # ログ設定失敗時のフォールバック
            print(f"Failed to setup logging: {log_error}", file=sys.stderr)
            print(
                f"Configuration loaded successfully. config={global_config}",
                file=sys.stderr,
            )
            # 最小限のロガーを作成
            logger = logging.getLogger(__name__)
            logger.addHandler(logging.StreamHandler(sys.stdout))
            logger.setLevel(logging.INFO)
            protocol_logger = logging.getLogger("mcp_protocol")
            protocol_logger.addHandler(logging.StreamHandler(sys.stdout))
            protocol_logger.setLevel(logging.INFO)

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

    except Exception as e:
        # 設定ロードエラー時は標準エラー出力に出力
        print(f"Failed to load configuration: {e}", file=sys.stderr)
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
        # 詳細な入力ログ
        logger.info(f"TOOL_INPUT - Tool: {name}, Arguments: {arguments}")

        if name in all_handlers:
            handler = all_handlers[name]
            try:
                result = await handler(**arguments)
                # 詳細な出力ログ（機密情報をマスク）
                sanitized_result = sanitize_log_output(result)
                logger.info(f"TOOL_OUTPUT - Tool: {name}, Result: {sanitized_result}")
                return result
            except Exception as e:
                logger.error(f"TOOL_ERROR - Tool: {name}, Error: {e}")
                return {"success": False, "error": str(e)}
        else:
            logger.error(f"TOOL_UNKNOWN - Tool: {name}")
            return {"success": False, "error": f"Unknown tool: {name}"}

    # Register tools via list_tools handler
    @server.list_tools()
    async def handle_list_tools() -> List[Tool]:
        """List available tools"""
        tool_count = len(all_tools)
        logger.info(f"TOOL_LIST - Listing {tool_count} available tools")
        return all_tools

    # Register resources
    database_resources = get_database_resources()
    resource_handlers = get_resource_handlers()
    table_schema_handler = get_table_schema_resource_handler()

    @server.list_resources()
    async def handle_list_resources() -> List[Resource]:
        """List available resources"""
        logger.info("RESOURCE_LIST - Listing available resources")
        resources = database_resources.copy()

        # Add dynamic table schema resources
        try:
            db_manager = DatabaseManager(global_config.postgres)
            db_manager.connection.connect()
            tables_result = db_manager.get_tables()
            db_manager.connection.disconnect()

            if tables_result["success"]:
                table_count = len(tables_result["tables"])
                logger.info(f"RESOURCE_LIST - Found {table_count} tables in database")
                for table_name in tables_result["tables"]:
                    resources.append(
                        Resource(
                            uri=f"database://schema/{table_name}",  # type: ignore
                            name=f"Table Schema: {table_name}",
                            description=f"Schema information for table {table_name}",
                            mimeType="text/markdown",
                        )
                    )
            else:
                logger.warning(
                    f"RESOURCE_LIST - Failed to get tables: {tables_result.get('error', 'Unknown error')}"
                )
        except Exception as e:
            logger.error(f"RESOURCE_LIST_ERROR - Error listing table resources: {e}")

        total_resources = len(resources)
        logger.info(f"RESOURCE_LIST - Total resources available: {total_resources}")
        return resources

    @server.read_resource()
    async def handle_read_resource(uri: str) -> str:
        """Read resource content"""
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

    # Start the server
    logger.info("Starting PostgreSQL MCP Server...")
    protocol_logger.info("MCP Protocol logging started")

    try:
        async with stdio_server() as (read_stream, write_stream):
            if protocol_logger:
                protocol_logger.debug(
                    "STDIO_SERVER - stdio_server context entered successfully"
                )

            # プロトコルロギングを有効化
            read_stream, write_stream = await protocol_logging_server(
                read_stream, write_stream
            )

            if protocol_logger:
                protocol_logger.debug("SERVER_RUN - Starting server.run()")

            await server.run(
                read_stream, write_stream, server.create_initialization_options()
            )

            if protocol_logger:
                protocol_logger.debug("SERVER_RUN - server.run() completed normally")

    except Exception as e:
        if protocol_logger:
            import traceback

            protocol_logger.error(
                f"SERVER_ERROR - Exception in main server loop: {e}, traceback: {traceback.format_exc()}"
            )
        logger.error(f"Server error: {e}")
        import traceback

        logger.error(f"Server error traceback: {traceback.format_exc()}")
        # 詳細なエラー情報を標準エラー出力にも出力
        print(f"Server error: {e}", file=sys.stderr)
        print(f"Server error traceback: {traceback.format_exc()}", file=sys.stderr)
        raise


def cli_main() -> None:
    """CLI entry point for uv run"""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()
