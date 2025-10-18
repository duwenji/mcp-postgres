# MCPツール実装ガイド

このガイドでは、PostgreSQL MCPサーバーのツール実装方法について詳細に説明します。MCPツールはAIアシスタントが実行できる操作を定義します。

## ツール設計の基本原則

### ツールの種類

1. **クエリ実行ツール**: SQLクエリの実行
2. **スキーマ情報ツール**: データベース構造の取得
3. **データ操作ツール**: CRUD操作の実行
4. **管理ツール**: データベース管理操作

### 設計ガイドライン

- **単一責任の原則**: 各ツールは1つの明確な目的を持つ
- **入力バリデーション**: すべての入力パラメータを検証
- **エラーハンドリング**: 明確なエラーメッセージを提供
- **セキュリティ**: SQLインジェクション対策を実装

## 実装パターン

実際のPostgreSQL MCPサーバーでは、以下のパターンを使用しています：

1. **ツール定義とハンドラーの分離**: ツールの定義と実行ロジックを分離
2. **モジュール化**: 機能ごとにモジュールを分割
3. **レジストリパターン**: ツールとハンドラーを登録する統一された方法
4. **動的ツール登録**: 単一の`@server.call_tool()`デコレーターで複数ツールを処理

## ツール実装の詳細

### 1. CRUDツールの実装

```python
# src/mcp_postgres_duwenji/tools/crud_tools.py
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
                "description": "Name of the table to insert into"
            },
            "data": {
                "type": "object",
                "description": "Dictionary of column names and values to insert",
                "additionalProperties": True
            }
        },
        "required": ["table_name", "data"]
    }
)


read_entity = Tool(
    name="read_entity",
    description="Read entities from a PostgreSQL table with optional conditions",
    inputSchema={
        "type": "object",
        "properties": {
            "table_name": {
                "type": "string",
                "description": "Name of the table to query"
            },
            "conditions": {
                "type": "object",
                "description": "Optional WHERE conditions as key-value pairs",
                "additionalProperties": True
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of rows to return (default: 100)",
                "default": 100,
                "minimum": 1,
                "maximum": 1000
            }
        },
        "required": ["table_name"]
    }
)


update_entity = Tool(
    name="update_entity",
    description="Update entities in a PostgreSQL table",
    inputSchema={
        "type": "object",
        "properties": {
            "table_name": {
                "type": "string",
                "description": "Name of the table to update"
            },
            "conditions": {
                "type": "object",
                "description": "WHERE conditions to identify which rows to update",
                "additionalProperties": True
            },
            "updates": {
                "type": "object",
                "description": "Dictionary of columns and values to update",
                "additionalProperties": True
            }
        },
        "required": ["table_name", "conditions", "updates"]
    }
)


delete_entity = Tool(
    name="delete_entity",
    description="Delete entities from a PostgreSQL table",
    inputSchema={
        "type": "object",
        "properties": {
            "table_name": {
                "type": "string",
                "description": "Name of the table to delete from"
            },
            "conditions": {
                "type": "object",
                "description": "WHERE conditions to identify which rows to delete",
                "additionalProperties": True
            }
        },
        "required": ["table_name", "conditions"]
    }
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
    table_name: str, 
    conditions: Optional[Dict[str, Any]] = None,
    limit: int = 100
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
    table_name: str, 
    conditions: Dict[str, Any], 
    updates: Dict[str, Any]
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
    table_name: str, 
    conditions: Dict[str, Any]
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
```

### 2. スキーマツールの実装

```python
# src/mcp_postgres_duwenji/tools/schema_tools.py
"""
Schema tools for PostgreSQL MCP Server
"""

import logging
from typing import Any, Dict, List, Optional
from mcp import Tool

from ..database import DatabaseManager, DatabaseError
from ..config import load_config

logger = logging.getLogger(__name__)


# Tool definitions for schema operations
get_tables = Tool(
    name="get_tables",
    description="Get list of all tables in the PostgreSQL database",
    inputSchema={
        "type": "object",
        "properties": {
            "schema": {
                "type": "string",
                "description": "Schema name to filter tables (default: 'public')",
                "default": "public"
            }
        },
        "required": []
    }
)


get_table_schema = Tool(
    name="get_table_schema",
    description="Get detailed schema information for a specific table",
    inputSchema={
        "type": "object",
        "properties": {
            "table_name": {
                "type": "string",
                "description": "Name of the table to get schema for"
            },
            "schema": {
                "type": "string",
                "description": "Schema name (default: 'public')",
                "default": "public"
            }
        },
        "required": ["table_name"]
    }
)


get_database_info = Tool(
    name="get_database_info",
    description="Get database metadata and version information",
    inputSchema={
        "type": "object",
        "properties": {},
        "required": []
    }
)


# Tool handlers
async def handle_get_tables(schema: str = "public") -> Dict[str, Any]:
    """Handle get_tables tool execution"""
    try:
        config = load_config()
        db_manager = DatabaseManager(config.postgres)
        
        # Connect to database
        db_manager.connection.connect()
        
        # Use existing get_tables method
        result = db_manager.get_tables()
        
        # Disconnect from database
        db_manager.connection.disconnect()
        
        return result
        
    except DatabaseError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in get_tables: {e}")
        return {"success": False, "error": f"Internal server error: {str(e)}"}


async def handle_get_table_schema(table_name: str, schema: str = "public") -> Dict[str, Any]:
    """Handle get_table_schema tool execution"""
    try:
        config = load_config()
        db_manager = DatabaseManager(config.postgres)
        
        # Connect to database
        db_manager.connection.connect()
        
        # Query to get table schema information
        query = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length,
            numeric_precision,
            numeric_scale
        FROM information_schema.columns 
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
        """
        
        results = db_manager.connection.execute_query(query, (schema, table_name))
        
        # Get table constraints
        constraints_query = """
        SELECT 
            tc.constraint_name,
            tc.constraint_type,
            kcu.column_name
        FROM information_schema.table_constraints tc
        LEFT JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
            AND tc.table_name = kcu.table_name
        WHERE tc.table_schema = %s AND tc.table_name = %s
        ORDER BY tc.constraint_type, tc.constraint_name
        """
        
        constraints = db_manager.connection.execute_query(constraints_query, (schema, table_name))
        
        # Disconnect from database
        db_manager.connection.disconnect()
        
        return {
            "success": True,
            "table_name": table_name,
            "schema": schema,
            "columns": results,
            "constraints": constraints
        }
        
    except DatabaseError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in get_table_schema: {e}")
        return {"success": False, "error": f"Internal server error: {str(e)}"}


async def handle_get_database_info() -> Dict[str, Any]:
    """Handle get_database_info tool execution"""
    try:
        config = load_config()
        db_manager = DatabaseManager(config.postgres)
        
        # Connect to database
        db_manager.connection.connect()
        
        # Get database version
        version_result = db_manager.connection.execute_query("SELECT version();")
        version = version_result[0]["version"] if version_result else "Unknown"
        
        # Get database name and current user
        db_info_result = db_manager.connection.execute_query(
            "SELECT current_database(), current_user, current_schema();"
        )
        db_info = db_info_result[0] if db_info_result else {}
        
        # Get database size
        size_result = db_manager.connection.execute_query(
            "SELECT pg_size_pretty(pg_database_size(current_database())) as database_size;"
        )
        database_size = size_result[0]["database_size"] if size_result else "Unknown"
        
        # Get number of tables
        tables_count_result = db_manager.connection.execute_query(
            "SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'public';"
        )
        table_count = tables_count_result[0]["table_count"] if tables_count_result else 0
        
        # Disconnect from database
        db_manager.connection.disconnect()
        
        return {
            "success": True,
            "database_info": {
                "version": version,
                "database_name": db_info.get("current_database", "Unknown"),
                "current_user": db_info.get("current_user", "Unknown"),
                "current_schema": db_info.get("current_schema", "Unknown"),
                "database_size": database_size,
                "table_count": table_count
            }
        }
        
    except DatabaseError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in get_database_info: {e}")
        return {"success": False, "error": f"Internal server error: {str(e)}"}


# Tool registry
def get_schema_tools() -> List[Tool]:
    """Get all schema tools"""
    return [
        get_tables,
        get_table_schema,
        get_database_info,
    ]


def get_schema_handlers() -> Dict[str, callable]:
    """Get tool handlers for schema operations"""
    return {
        "get_tables": handle_get_tables,
        "get_table_schema": handle_get_table_schema,
        "get_database_info": handle_get_database_info,
    }
```

## 実装パターンの利点

### 1. ツールとハンドラーの分離
- **ツール定義**: 入力スキーマとメタデータのみを定義
- **ハンドラー**: 実際のビジネスロジックを実装
- **利点**: テストのしやすさ、コードの再利用性

### 2. モジュール化
- **機能ごとの分離**: CRUD操作とスキーマ情報を別モジュールに分割
- **責務の明確化**: 各モジュールが単一の責任を持つ
- **利点**: 保守性の向上、チーム開発の効率化

### 3. レジストリパターン
- **統一された登録方法**: `get_*_tools()`と`get_*_handlers()`で一貫性のある登録
- **動的ツール管理**: 新しいツールの追加が容易
- **利点**: 拡張性の確保、コードの一貫性

### 4. 動的ツール登録
- **単一のハンドラー**: すべてのツールを単一の`@server.call_tool()`で処理
- **柔軟なルーティング**: ツール名に基づいて適切なハンドラーを選択
- **利点**: コードの簡潔さ、エラーハンドリングの統一

## ベストプラクティス

### 1. 入力バリデーション
```python
def validate_table_name(table: str) -> None:
    """テーブル名の検証"""
    if not table or not table.strip():
        raise ValueError("テーブル名が空です")
    
    # SQLインジェクション対策
    if any(char in table for char in [';', "'", '"', '--', '/*', '*/']):
        raise ValueError("無効なテーブル名です")
```

### 2. エラーハンドリング
```python
async def handle_tool_call(name: str, arguments: dict) -> dict:
    """ツール実行リクエストのハンドラー"""
    try:
        if name in all_handlers:
            handler = all_handlers[name]
            result = await handler(**arguments)
            return result
        else:
            return {"success": False, "error": f"Unknown tool: {name}"}
    except Exception as e:
        logger.error(f"Tool {name} execution failed: {e}")
        return {"success": False, "error": str(e)}
```

### 3. セキュリティ対策
```python
def validate_query_safety(query: str) -> None:
    """クエリの安全性を検証"""
    dangerous_operations = ['DROP', 'TRUNCATE', 'ALTER', 'CREATE', 'GRANT', 'REVOKE']
    upper_query = query.upper()
    
    for operation in dangerous_operations:
        if operation in upper_query:
            raise ValueError(f"危険な操作 '{operation}' は許可されていません")
```

### 4. ロギング
```python
import logging

logger = logging.getLogger(__name__)

async def handle_tool_call(name: str, arguments: dict) -> dict:
    """ツール実行リクエストのハンドラー"""
    logger.info(f"Tool call: {name} with arguments: {arguments}")
    
    try:
        if name in all_handlers:
            handler = all_handlers[name]
            result = await handler(**arguments)
            logger.info(f"Tool {name} executed successfully")
            return result
        else:
            logger.error(f"Unknown tool: {name}")
            return {"success": False, "error": f"Unknown tool: {name}"}
    except Exception as e:
        logger.error(f"Tool {name} execution failed: {e}")
        return {"success": False, "error": str(e)}
```

## Windows環境での考慮事項

### 1. パス関連の問題
```python
# Windowsではパス区切り文字に注意
import os

# 安全なパス構築
config_path = os.path.join('config', 'database.yaml')
log_path = os.path.join('logs', 'mcp_server.log')

# 環境変数の扱い
database_url = os.environ.get('POSTGRES_URL', 'localhost:5432')
```

### 2. 権限関連の問題
```python
import sys
import os

def check_permissions():
    """必要な権限を確認"""
    try:
        # ファイル書き込み権限の確認
        test_file = 'test_permission.txt'
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        return True
    except PermissionError:
        logger.error("ファイル書き込み権限がありません")
        return False
    except Exception as e:
        logger.error(f"権限確認エラー: {e}")
        return False
```

### 3. 文字コード問題
```python
# Windowsでの文字コード問題対策
import sys

if sys.platform == 'win32':
    # Windowsでは標準出力の文字コードを設定
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)
```

## まとめ

このガイドでは、PostgreSQL MCPサーバーのツール実装方法を詳細に説明しました。実際の実装パターンに基づいたコード例を提供し、以下の重要なポイントをカバーしました：

1. **ツールとハンドラーの分離**: 定義と実装の分離による保守性向上
2. **モジュール化**: 機能ごとの責務分離による拡張性確保
3. **レジストリパターン**: 統一されたツール登録方法
4. **動的ツール登録**: 単一ハンドラーによる効率的な処理
5. **Windows環境対応**: プラットフォーム固有の問題への対策

これらのパターンを活用することで、堅牢で拡張性の高いMCPサーバーを開発できます。次のステップでは、リソース管理や高度な機能の実装に進みましょう。
