"""
MCPプロトコルメッセージのロギング機能を提供するモジュール
"""

import json
import logging
from typing import Any


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
        self.logger = logger_instance

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
                        # 詳細なデータ情報をログに記録
                        self.logger.debug(
                            f"RECEIVE_DATA_DETAILS - data_type: {type(data)}, data_repr: {repr(data)}"
                        )

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
                        elif hasattr(data, "message") and hasattr(data.message, "root"):
                            # MCP SessionMessageオブジェクトの場合
                            try:
                                import json
                                from mcp.shared.message import JSONRPCMessage

                                if isinstance(data.message, JSONRPCMessage):
                                    # JSON-RPCメッセージをJSON形式でログ出力
                                    message_dict = {
                                        "jsonrpc": data.message.root.jsonrpc,
                                        "id": getattr(data.message.root, "id", None),
                                        "method": getattr(
                                            data.message.root, "method", None
                                        ),
                                        "params": getattr(
                                            data.message.root, "params", None
                                        ),
                                    }
                                    sanitized_message = sanitize_log_output(
                                        message_dict
                                    )
                                    self.logger.debug(
                                        f"REQUEST: {json.dumps(sanitized_message, ensure_ascii=False, indent=2)}"
                                    )
                                else:
                                    # その他のメッセージタイプ
                                    message_str = str(data)
                                    sanitized_message = sanitize_protocol_message(
                                        message_str
                                    )
                                    self.logger.debug(f"REQUEST: {sanitized_message}")
                            except Exception as json_error:
                                self.logger.warning(
                                    f"JSON serialization error: {json_error}, falling back to string representation"
                                )
                                message_str = str(data)
                                sanitized_message = sanitize_protocol_message(
                                    message_str
                                )
                                self.logger.debug(f"REQUEST: {sanitized_message}")
                        else:
                            # その他の型の場合は文字列化してログに記録
                            message_str = str(data)
                            sanitized_message = sanitize_protocol_message(message_str)
                            self.logger.debug(f"REQUEST: {sanitized_message}")

                except Exception as e:
                    # 詳細なエラー情報をログに記録
                    if self.logger:
                        import traceback

                        self.logger.error(
                            f"Error logging request: {e}, traceback: {traceback.format_exc()}"
                        )
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
                # ストリーム終了を適切に通知
                if self.logger:
                    self.logger.debug("STREAM_END - End of stream reached")
                raise StopAsyncIteration
            return data
        except StopAsyncIteration:
            # StopAsyncIterationはそのまま送出
            if self.logger:
                self.logger.debug("STREAM_END - StopAsyncIteration raised")
            raise
        except Exception as e:
            # その他の例外はログに記録してからStopAsyncIterationを送出
            if self.logger:
                import traceback

                self.logger.error(f"STREAM_ERROR - Async iteration error: {e}")
                self.logger.debug(
                    f"STREAM_ERROR_TRACE - Traceback: {traceback.format_exc()}"
                )
            # 元の例外を保持したままStopAsyncIterationを送出
            raise StopAsyncIteration from e


class ProtocolLoggingSendStream:
    """
    MCPプロトコルメッセージをログに記録する送信ストリームラッパー
    """

    def __init__(
        self, original_stream: Any, logger_instance: logging.Logger | None = None
    ) -> None:
        self.original_stream = original_stream
        self.logger = logger_instance

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
                        # 詳細なデータ情報をログに記録
                        self.logger.debug(
                            f"SEND_DATA_DETAILS - item_type: {type(item)}, item_repr: {repr(item)}"
                        )

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
                        elif hasattr(item, "message") and hasattr(item.message, "root"):
                            # MCP SessionMessageオブジェクトの場合
                            try:
                                import json
                                from mcp.shared.message import JSONRPCMessage

                                if isinstance(item.message, JSONRPCMessage):
                                    # JSON-RPCメッセージをJSON形式でログ出力
                                    message_dict = {
                                        "jsonrpc": item.message.root.jsonrpc,
                                        "id": getattr(item.message.root, "id", None),
                                        "result": getattr(
                                            item.message.root, "result", None
                                        ),
                                        "error": getattr(
                                            item.message.root, "error", None
                                        ),
                                    }
                                    sanitized_message = sanitize_log_output(
                                        message_dict
                                    )
                                    self.logger.debug(
                                        f"RESPONSE: {json.dumps(sanitized_message, ensure_ascii=False, indent=2)}"
                                    )
                                else:
                                    # その他のメッセージタイプ
                                    message_str = str(item)
                                    sanitized_message = sanitize_protocol_message(
                                        message_str
                                    )
                                    self.logger.debug(f"RESPONSE: {sanitized_message}")
                            except Exception as json_error:
                                self.logger.warning(
                                    f"JSON serialization error: {json_error}, falling back to string representation"
                                )
                                message_str = str(item)
                                sanitized_message = sanitize_protocol_message(
                                    message_str
                                )
                                self.logger.debug(f"RESPONSE: {sanitized_message}")
                        else:
                            # その他の型の場合は文字列化してログに記録
                            message_str = str(item)
                            sanitized_message = sanitize_protocol_message(message_str)
                            self.logger.debug(f"RESPONSE: {sanitized_message}")
                except Exception as e:
                    # 詳細なエラー情報をログに記録
                    if self.logger:
                        import traceback

                        self.logger.error(
                            f"Error logging response: {e}, traceback: {traceback.format_exc()}"
                        )

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
    read_stream: Any,
    write_stream: Any,
    global_config: Any,
    protocol_logger: logging.Logger | None = None,
) -> tuple[Any, Any]:
    """
    MCPプロトコルメッセージをログに記録するラッパーサーバー

    Args:
        read_stream: 入力ストリーム
        write_stream: 出力ストリーム
        global_config: グローバル設定オブジェクト
        protocol_logger: プロトコルロガー

    Returns:
        ラップされたストリームのタプル
    """
    # プロトコルデバッグモードが有効な場合のみロギングを有効化
    if global_config and global_config.protocol_debug:
        if protocol_logger:
            protocol_logger.debug("PROTOCOL_LOGGING_SERVER - Starting stream wrapping")

        # 入出力ストリームをラップ
        wrapped_read_stream = ProtocolLoggingReceiveStream(read_stream, protocol_logger)
        wrapped_write_stream = ProtocolLoggingSendStream(write_stream, protocol_logger)

        if protocol_logger:
            protocol_logger.debug("PROTOCOL_LOGGING_SERVER - Stream wrapping completed")

        return wrapped_read_stream, wrapped_write_stream
    else:
        # プロトコルデバッグモードが無効な場合は元のストリームをそのまま返す
        if protocol_logger:
            protocol_logger.debug(
                "PROTOCOL_LOGGING_SERVER - Protocol debug disabled, using original streams"
            )
        return read_stream, write_stream
