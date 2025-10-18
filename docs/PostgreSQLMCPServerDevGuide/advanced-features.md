# 高度な機能ガイド

このガイドでは、PostgreSQL MCPサーバーの高度な機能と最適化手法について説明します。

## 非同期処理の最適化

### 1. 非同期データベース接続

```python
# src/mcp_postgres_duwenji/async_database.py
import asyncio
import asyncpg
from typing import List, Dict, Any, Optional
import logging
from .config import PostgresConfig

logger = logging.getLogger(__name__)

class AsyncDatabaseManager:
    """非同期データベース接続管理クラス"""
    
    def __init__(self, config: PostgresConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self) -> None:
        """非同期接続プールの初期化"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                min_size=1,
                max_size=self.config.pool_size,
                command_timeout=self.config.command_timeout
            )
            logger.info("非同期データベース接続プールを初期化しました")
        except Exception as e:
            logger.error(f"非同期接続プールの初期化に失敗: {str(e)}")
            raise
    
    async def execute_query(
        self, 
        query: str, 
        params: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """非同期クエリ実行"""
        if not self.pool:
            await self.initialize()
        
        try:
            async with self.pool.acquire() as connection:
                # パラメータ化クエリの実行
                if params:
                    result = await connection.fetch(query, *params.values())
                else:
                    result = await connection.fetch(query)
                
                # 結果を辞書形式に変換
                return [dict(record) for record in result]
                
        except Exception as e:
            logger.error(f"非同期クエリ実行エラー: {str(e)}")
            raise
    
    async def execute_transaction(
        self, 
        queries: List[Dict[str, Any]]
    ) -> List[Any]:
        """非同期トランザクション実行"""
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                results = []
                for query_info in queries:
                    query = query_info['query']
                    params = query_info.get('params', {})
                    
                    if params:
                        result = await connection.fetch(query, *params.values())
                    else:
                        result = await connection.fetch(query)
                    
                    results.append([dict(record) for record in result])
                
                return results
    
    async def close(self) -> None:
        """接続プールを閉じる"""
        if self.pool:
            await self.pool.close()
            logger.info("非同期データベース接続プールを閉じました")
```

### 2. 非同期ツールの実装

```python
# src/mcp_postgres_duwenji/tools/async_tools.py
from mcp.server import Server
from mcp.server.models import Tool
from typing import Dict, Any, List
import logging
from ..async_database import AsyncDatabaseManager
from ..config import load_config

logger = logging.getLogger(__name__)

class AsyncToolManager:
    """非同期ツール管理クラス"""
    
    def __init__(self):
        self.config = load_config()
        self.db_manager = AsyncDatabaseManager(self.config)
    
    async def initialize(self) -> None:
        """非同期ツールの初期化"""
        await self.db_manager.initialize()
    
    async def execute_async_query(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """非同期クエリ実行ツール"""
        query = arguments.get("query", "").strip()
        parameters = arguments.get("parameters", {})
        
        if not query:
            raise ValueError("クエリが空です")
        
        # クエリ実行
        result = await self.db_manager.execute_query(query, parameters)
        
        return [{
            "type": "text",
            "text": f"非同期クエリ結果: {len(result)} 行のデータ\n\n{self._format_result(result)}"
        }]
    
    async def batch_execute_queries(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """バッチクエリ実行ツール"""
        queries = arguments.get("queries", [])
        
        if not queries:
            raise ValueError("クエリが指定されていません")
        
        # バッチ実行
        results = await self.db_manager.execute_transaction(queries)
        
        response_text = "バッチクエリ実行結果:\n\n"
        for i, result in enumerate(results):
            response_text += f"クエリ {i+1}: {len(result)} 行\n"
        
        return [{
            "type": "text",
            "text": response_text
        }]
    
    def _format_result(self, result: List[Dict[str, Any]]) -> str:
        """結果のフォーマット"""
        if not result:
            return "結果は空です"
        
        # 簡易的なテーブル形式での表示
        headers = list(result[0].keys())
        header_line = " | ".join(headers)
        separator = "-" * len(header_line)
        
        rows = []
        for row in result[:5]:  # 最初の5行のみ表示
            row_data = [str(row.get(col, "")) for col in headers]
            rows.append(" | ".join(row_data))
        
        formatted = f"{header_line}\n{separator}\n"
        formatted += "\n".join(rows)
        
        if len(result) > 5:
            formatted += f"\n\n... 他 {len(result) - 5} 行"
        
        return formatted

def register_async_tools(server: Server) -> None:
    """非同期ツールを登録"""
    
    tool_manager = AsyncToolManager()
    
    @server.list_tools()
    async def handle_list_tools() -> List[Tool]:
        return [
            Tool(
                name="async_query_execute",
                description="非同期でSQLクエリを実行します（高性能）",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "実行するSQLクエリ"
                        },
                        "parameters": {
                            "type": "object",
                            "description": "クエリパラメータ"
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="batch_query_execute",
                description="複数のクエリをトランザクション内で実行します",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "queries": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string"},
                                    "parameters": {"type": "object"}
                                },
                                "required": ["query"]
                            },
                            "description": "実行するクエリのリスト"
                        }
                    },
                    "required": ["queries"]
                }
            )
        ]
    
    @server.call_tool()
    async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            if name == "async_query_execute":
                return await tool_manager.execute_async_query(arguments)
            elif name == "batch_query_execute":
                return await tool_manager.batch_execute_queries(arguments)
            else:
                raise ValueError(f"不明な非同期ツール: {name}")
        except Exception as e:
            logger.error(f"非同期ツール実行エラー: {str(e)}")
            return [{
                "type": "text",
                "text": f"非同期ツール実行エラー: {str(e)}"
            }]
```

**依存関係のインストール**:
```bash
# asyncpgのインストール
uv add asyncpg
```

## 監視とロギングの強化

### 1. 構造化ロギング

```python
# src/mcp_postgres_duwenji/logging_config.py
import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any

class StructuredFormatter(logging.Formatter):
    """構造化ログフォーマッター"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 追加のコンテキスト情報
        if hasattr(record, 'context'):
            log_entry['context'] = record.context
        
        return json.dumps(log_entry, ensure_ascii=False)

def setup_logging(level: str = "INFO") -> None:
    """ロギングの設定"""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredFormatter())
    logger.addHandler(console_handler)
    
    # ファイルハンドラー（オプション）
    file_handler = logging.FileHandler("mcp_postgres.log")
    file_handler.setFormatter(StructuredFormatter())
    logger.addHandler(file_handler)

class DatabaseLogger:
    """データベース操作のロギング"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def log_query(
        self, 
        query: str, 
        params: Dict[str, Any] = None,
        execution_time: float = None,
        row_count: int = None
    ) -> None:
        """クエリ実行のロギング"""
        log_context = {
            "query": query,
            "params": params,
            "execution_time": execution_time,
            "row_count": row_count,
            "operation": self._detect_operation(query)
        }
        
        self.logger.info(
            "Query executed",
            extra={"context": log_context}
        )
    
    def log_connection_event(self, event: str, details: Dict[str, Any] = None) -> None:
        """接続イベントのロギング"""
        log_context = {
            "event": event,
            "details": details or {}
        }
        
        self.logger.info(
            f"Connection event: {event}",
            extra={"context": log_context}
        )
    
    def _detect_operation(self, query: str) -> str:
        """クエリの操作タイプを検出"""
        query_upper = query.upper().strip()
        
        if query_upper.startswith("SELECT"):
            return "SELECT"
        elif query_upper.startswith("INSERT"):
            return "INSERT"
        elif query_upper.startswith("UPDATE"):
            return "UPDATE"
        elif query_upper.startswith("DELETE"):
            return "DELETE"
        elif query_upper.startswith("CREATE"):
            return "CREATE"
        elif query_upper.startswith("DROP"):
            return "DROP"
        else:
            return "OTHER"
```

### 2. パフォーマンスメトリクス

```python
# src/mcp_postgres_duwenji/metrics.py
import time
from typing import Dict, Any, List
from dataclasses import dataclass
from collections import defaultdict, deque
import statistics

@dataclass
class QueryMetrics:
    """クエリメトリクス"""
    query: str
    execution_time: float
    row_count: int
    timestamp: float
    success: bool

class PerformanceMonitor:
    """パフォーマンス監視クラス"""
    
    def __init__(self, max_history: int = 1000):
        self.query_history = deque(maxlen=max_history)
        self.error_count = 0
        self.success_count = 0
    
    def record_query(
        self, 
        query: str, 
        execution_time: float, 
        row_count: int, 
        success: bool = True
    ) -> None:
        """クエリ実行を記録"""
        metrics = QueryMetrics(
            query=query,
            execution_time=execution_time,
            row_count=row_count,
            timestamp=time.time(),
            success=success
        )
        
        self.query_history.append(metrics)
        
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """パフォーマンスサマリーを取得"""
        if not self.query_history:
            return {"message": "No queries recorded"}
        
        successful_queries = [q for q in self.query_history if q.success]
        
        if not successful_queries:
            return {"message": "No successful queries recorded"}
        
        execution_times = [q.execution_time for q in successful_queries]
        row_counts = [q.row_count for q in successful_queries]
        
        return {
            "total_queries": len(self.query_history),
            "successful_queries": self.success_count,
            "failed_queries": self.error_count,
            "success_rate": self.success_count / len(self.query_history) if self.query_history else 0,
            "average_execution_time": statistics.mean(execution_times),
            "median_execution_time": statistics.median(execution_times),
            "max_execution_time": max(execution_times),
            "min_execution_time": min(execution_times),
            "average_row_count": statistics.mean(row_counts),
            "queries_per_minute": self._calculate_qpm()
        }
    
    def get_slow_queries(self, threshold: float = 1.0) -> List[Dict[str, Any]]:
        """遅いクエリを取得"""
        slow_queries = [
            {
                "query": q.query,
                "execution_time": q.execution_time,
                "row_count": q.row_count,
                "timestamp": q.timestamp
            }
            for q in self.query_history
            if q.execution_time > threshold and q.success
        ]
        
        return sorted(slow_queries, key=lambda x: x["execution_time"], reverse=True)
    
    def _calculate_qpm(self) -> float:
        """1分あたりのクエリ数を計算"""
        if not self.query_history:
            return 0.0
        
        current_time = time.time()
        one_minute_ago = current_time - 60
        
        recent_queries = [
            q for q in self.query_history 
            if q.timestamp >= one_minute_ago
        ]
        
        return len(recent_queries)
```

## 設定の動的リロード

### 1. 動的設定管理

```python
# src/mcp_postgres_duwenji/dynamic_config.py
import asyncio
import os
import time
from typing import Dict, Any, Callable, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .config import load_config

class ConfigReloadHandler(FileSystemEventHandler):
    """設定ファイル変更ハンドラー"""
    
    def __init__(self, callback: Callable):
        self.callback = callback
        self.last_modified = 0
    
    def on_modified(self, event):
        """ファイル変更時の処理"""
        if event.src_path.endswith('.env') or event.src_path.endswith('config.py'):
            current_time = time.time()
            # 連続変更を防ぐためのデバウンス
            if current_time - self.last_modified > 1.0:
                self.last_modified = current_time
                self.callback()

class DynamicConfigManager:
    """動的設定管理クラス"""
    
    def __init__(self):
        self.current_config = None
        self.observers = []
        self.callbacks: List[Callable] = []
    
    def initialize(self) -> None:
        """初期化"""
        self.current_config = load_config()
        self._start_file_watcher()
    
    def add_reload_callback(self, callback: Callable) -> None:
        """リロードコールバックを追加"""
        self.callbacks.append(callback)
    
    def reload_config(self) -> None:
        """設定をリロード"""
        try:
            old_config = self.current_config
            self.current_config = load_config()
            
            # 設定変更を通知
            for callback in self.callbacks:
                callback(old_config, self.current_config)
            
            print("設定をリロードしました")
        except Exception as e:
            print(f"設定のリロードに失敗しました: {str(e)}")
    
    def _start_file_watcher(self) -> None:
        """ファイル監視を開始"""
        event_handler = ConfigReloadHandler(self.reload_config)
        observer = Observer()
        observer.schedule(event_handler, path='.', recursive=False)
        observer.start()
        self.observers.append(observer)
    
    def stop(self) -> None:
        """監視を停止"""
        for observer in self.observers:
            observer.stop()
            observer.join()
```

**依存関係のインストール**:
```bash
# watchdogのインストール
uv add watchdog
```

### 2. ホットリロード対応データベースマネージャー

```python
# src/mcp_postgres_duwenji/hot_reload_database.py
from .database import DatabaseManager
from .dynamic_config import DynamicConfigManager

class HotReloadDatabaseManager:
    """ホットリロード対応データベースマネージャー"""
    
    def __init__(self):
        self.config_manager = DynamicConfigManager()
        self.db_manager = None
        self._initialize_db_manager()
        
        # 設定変更時のコールバックを登録
        self.config_manager.add_reload_callback(self._on_config_changed)
    
    def _initialize_db_manager(self) -> None:
        """データベースマネージャーを初期化"""
        if self.db_manager:
            self.db_manager.close()
        
        self.db_manager = DatabaseManager(self.config_manager.current_config)
        self.db_manager.initialize()
    
    def _on_config_changed(self, old_config, new_config) -> None:
        """設定変更時の処理"""
        print("データベース
