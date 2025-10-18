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

## ツール実装の詳細

### 1. CRUDツールの実装

```python
# src/mcp_postgres_duwenji/tools/crud_tools.py
from mcp.server import Server
from mcp.server.models import Tool
from typing import Dict, Any, List, Optional
import logging
from ..database import DatabaseManagerSingleton, QueryError

logger = logging.getLogger(__name__)

def register_crud_tools(server: Server) -> None:
    """CRUD操作ツールを登録"""
    
    @server.list_tools()
    async def handle_list_tools() -> List[Tool]:
        """利用可能なツールの一覧を返す"""
        return [
            Tool(
                name="query_execute",
                description="SQLクエリを実行し、結果を返します",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "実行するSQLクエリ"
                        },
                        "parameters": {
                            "type": "object",
                            "description": "クエリパラメータ（オプション）",
                            "additionalProperties": True
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "クエリタイムアウト（秒、オプション）",
                            "minimum": 1,
                            "maximum": 300
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="insert_data",
                description="テーブルにデータを挿入します",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "table": {
                            "type": "string",
                            "description": "データを挿入するテーブル名"
                        },
                        "data": {
                            "type": "object",
                            "description": "挿入するデータ",
                            "additionalProperties": True
                        }
                    },
                    "required": ["table", "data"]
                }
            ),
            Tool(
                name="update_data",
                description="テーブルのデータを更新します",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "table": {
                            "type": "string",
                            "description": "データを更新するテーブル名"
                        },
                        "data": {
                            "type": "object",
                            "description": "更新するデータ",
                            "additionalProperties": True
                        },
                        "conditions": {
                            "type": "object",
                            "description": "更新条件",
                            "additionalProperties": True
                        }
                    },
                    "required": ["table", "data", "conditions"]
                }
            ),
            Tool(
                name="delete_data",
                description="テーブルからデータを削除します",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "table": {
                            "type": "string",
                            "description": "データを削除するテーブル名"
                        },
                        "conditions": {
                            "type": "object",
                            "description": "削除条件",
                            "additionalProperties": True
                        }
                    },
                    "required": ["table", "conditions"]
                }
            )
        ]
    
    @server.call_tool()
    async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """ツールの実行"""
        try:
            db_manager = DatabaseManagerSingleton.get_instance()
            
            if name == "query_execute":
                return await _execute_query(db_manager, arguments)
            elif name == "insert_data":
                return await _insert_data(db_manager, arguments)
            elif name == "update_data":
                return await _update_data(db_manager, arguments)
            elif name == "delete_data":
                return await _delete_data(db_manager, arguments)
            else:
                raise ValueError(f"不明なツール: {name}")
                
        except QueryError as e:
            logger.error(f"クエリ実行エラー: {str(e)}")
            return [{
                "type": "text",
                "text": f"クエリ実行エラー: {str(e)}"
            }]
        except Exception as e:
            logger.error(f"ツール実行エラー: {str(e)}")
            return [{
                "type": "text",
                "text": f"ツール実行エラー: {str(e)}"
            }]

async def _execute_query(db_manager, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """SQLクエリを実行"""
    query = arguments.get("query", "").strip()
    parameters = arguments.get("parameters", {})
    timeout = arguments.get("timeout")
    
    # 入力バリデーション
    if not query:
        raise ValueError("クエリが空です")
    
    # 危険な操作の検出
    _validate_query_safety(query)
    
    # クエリ実行
    result = db_manager.execute_query(query, parameters, timeout)
    
    # 結果のフォーマット
    if result and "rows_affected" in result[0]:
        return [{
            "type": "text",
            "text": f"クエリが正常に実行されました。影響を受けた行数: {result[0]['rows_affected']}"
        }]
    else:
        return [{
            "type": "text",
            "text": f"クエリ結果: {len(result)} 行のデータが見つかりました\n\n{_format_query_result(result)}"
        }]

async def _insert_data(db_manager, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """データを挿入"""
    table = arguments["table"]
    data = arguments["data"]
    
    # 入力バリデーション
    _validate_table_name(table)
    _validate_data_dict(data)
    
    # INSERTクエリの構築
    columns = ", ".join(data.keys())
    placeholders = ", ".join([f"%({key})s" for key in data.keys()])
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    
    # クエリ実行
    result = db_manager.execute_query(query, data)
    
    return [{
        "type": "text",
        "text": f"データが正常に挿入されました。テーブル: {table}"
    }]

async def _update_data(db_manager, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """データを更新"""
    table = arguments["table"]
    data = arguments["data"]
    conditions = arguments["conditions"]
    
    # 入力バリデーション
    _validate_table_name(table)
    _validate_data_dict(data)
    _validate_conditions(conditions)
    
    # UPDATEクエリの構築
    set_clause = ", ".join([f"{key} = %({key})s" for key in data.keys()])
    where_clause = " AND ".join([f"{key} = %(condition_{key})s" for key in conditions.keys()])
    
    # パラメータの結合
    all_params = data.copy()
    for key, value in conditions.items():
        all_params[f"condition_{key}"] = value
    
    query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
    
    # クエリ実行
    result = db_manager.execute_query(query, all_params)
    
    return [{
        "type": "text",
        "text": f"データが正常に更新されました。テーブル: {table}, 影響を受けた行数: {result[0]['rows_affected']}"
    }]

async def _delete_data(db_manager, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """データを削除"""
    table = arguments["table"]
    conditions = arguments["conditions"]
    
    # 入力バリデーション
    _validate_table_name(table)
    _validate_conditions(conditions)
    
    # DELETEクエリの構築
    where_clause = " AND ".join([f"{key} = %({key})s" for key in conditions.keys()])
    query = f"DELETE FROM {table} WHERE {where_clause}"
    
    # クエリ実行
    result = db_manager.execute_query(query, conditions)
    
    return [{
        "type": "text",
        "text": f"データが正常に削除されました。テーブル: {table}, 削除された行数: {result[0]['rows_affected']}"
    }]

def _validate_query_safety(query: str) -> None:
    """クエリの安全性を検証"""
    dangerous_operations = ['DROP', 'TRUNCATE', 'ALTER', 'CREATE', 'GRANT', 'REVOKE']
    upper_query = query.upper()
    
    for operation in dangerous_operations:
        if operation in upper_query:
            raise ValueError(f"危険な操作 '{operation}' は許可されていません")

def _validate_table_name(table: str) -> None:
    """テーブル名の検証"""
    if not table or not table.strip():
        raise ValueError("テーブル名が空です")
    
    # 基本的なSQLインジェクション対策
    if any(char in table for char in [';', "'", '"', '--', '/*', '*/']):
        raise ValueError("無効なテーブル名です")

def _validate_data_dict(data: Dict[str, Any]) -> None:
    """データ辞書の検証"""
    if not data:
        raise ValueError("データが空です")
    
    for key, value in data.items():
        if not key or not key.strip():
            raise ValueError("データキーが空です")

def _validate_conditions(conditions: Dict[str, Any]) -> None:
    """条件の検証"""
    if not conditions:
        raise ValueError("条件が指定されていません")

def _format_query_result(result: List[Dict[str, Any]]) -> str:
    """クエリ結果を整形"""
    if not result:
        return "結果は空です"
    
    # ヘッダーの作成
    headers = list(result[0].keys())
    header_line = " | ".join(headers)
    separator = "-" * len(header_line)
    
    # データ行の作成
    rows = []
    for row in result[:10]:  # 最初の10行のみ表示
        row_data = [str(row.get(col, "")) for col in headers]
        rows.append(" | ".join(row_data))
    
    # 結果の組み立て
    formatted = f"{header_line}\n{separator}\n"
    formatted += "\n".join(rows)
    
    if len(result) > 10:
        formatted += f"\n\n... 他 {len(result) - 10} 行"
    
    return formatted
```

### 2. スキーマツールの実装

```python
# src/mcp_postgres_duwenji/tools/schema_tools.py
from mcp.server import Server
from mcp.server.models import Tool
from typing import Dict, Any, List
import logging
from ..database import DatabaseManagerSingleton

logger = logging.getLogger(__name__)

def register_schema_tools(server: Server) -> None:
    """スキーマ情報ツールを登録"""
    
    @server.list_tools()
    async def handle_list_tools() -> List[Tool]:
        return [
            Tool(
                name="get_tables",
                description="データベースのテーブル一覧を取得します",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "schema": {
                            "type": "string",
                            "description": "スキーマ名（オプション、デフォルト: public）",
                            "default": "public"
                        }
                    }
                }
            ),
            Tool(
                name="get_table_schema",
                description="指定したテーブルの詳細なスキーマ情報を取得します",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "table": {
                            "type": "string",
                            "description": "テーブル名"
                        },
                        "schema": {
                            "type": "string",
                            "description": "スキーマ名（オプション、デフォルト: public）",
                            "default": "public"
                        }
                    },
                    "required": ["table"]
                }
            ),
            Tool(
                name="get_database_info",
                description="データベースの基本情報を取得します",
                inputSchema={"type": "object", "properties": {}}
            )
        ]
    
    @server.call_tool()
    async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            db_manager = DatabaseManagerSingleton.get_instance()
            
            if name == "get_tables":
                return await _get_tables(db_manager, arguments)
            elif name == "get_table_schema":
                return await _get_table_schema(db_manager, arguments)
            elif name == "get_database_info":
                return await _get_database_info(db_manager)
            else:
                raise ValueError(f"不明なツール: {name}")
                
        except Exception as e:
            logger.error(f"スキーマツール実行エラー: {str(e)}")
            return [{
                "type": "text",
                "text": f"スキーマ情報の取得に失敗しました: {str(e)}"
            }]

async def _get_tables(db_manager, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """テーブル一覧を取得"""
    schema = arguments.get("schema", "public")
    
    query = """
        SELECT 
            table_name,
            table_type,
            table_schema
        FROM information_schema.tables 
        WHERE table_schema = %s
        ORDER BY table_name
    """
    
    result = db_manager.execute_query(query, {"schema": schema})
    
    if not result:
        return [{
            "type": "text",
            "text": f"スキーマ '{schema}' にテーブルはありません"
        }]
    
    table_list = "\n".join([
        f"- {row['table_name']} ({row['table_type']})" 
        for row in result
    ])
    
    return [{
        "type": "text",
        "text": f"スキーマ '{schema}' のテーブル一覧:\n\n{table_list}"
    }]

async def _get_table_schema(db_manager, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """テーブルの詳細スキーマを取得"""
    table = arguments["table"]
    schema = arguments.get("schema", "public")
    
    # カラム情報の取得
    columns_query = """
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
    
    columns = db_manager.execute_query(columns_query, {
        "schema": schema,
        "table": table
    })
    
    if not columns:
        return [{
            "type": "text",
            "text": f"テーブル '{schema}.{table}' が見つかりません"
        }]
    
    # 制約情報の取得
    constraints_query = """
        SELECT 
            constraint_name,
            constraint_type
        FROM information_schema.table_constraints 
        WHERE table_schema = %s AND table_name = %s
    """
    
    constraints = db_manager.execute_query(constraints_query, {
        "schema": schema,
        "table": table
    })
    
    # スキーマ情報のフォーマット
    schema_info = f"テーブル: {schema}.{table}\n\n"
    schema_info += "カラム情報:\n"
    
    for col in columns:
        schema_info += f"- {col['column_name']}: {col['data_type']}"
        if col['character_maximum_length']:
            schema_info += f"({col['character_maximum_length']})"
        elif col['numeric_precision']:
            schema_info += f"({col['numeric_precision']},{col['numeric_scale'] or 0})"
        
        if col['is_nullable'] == 'NO':
            schema_info += " NOT NULL"
        
        if col['column_default']:
            schema_info += f" DEFAULT {col['column_default']}"
        
        schema_info += "\n"
    
    if constraints:
        schema_info += "\n制約:\n"
        for const in constraints:
            schema_info += f"- {const['constraint_name']}: {const['constraint_type']}\n"
    
    return [{
        "type": "text",
        "text": schema_info
    }]

async def _get_database_info(db_manager) -> List[Dict[str, Any]]:
    """データベース基本情報を取得"""
    info = db_manager.get_database_info()
    
    info_text = f"データベース情報:\n\n"
    info_text += f"バージョン: {info['version']}\n"
    info_text += f"現在のデータベース: {info['current_database']}\n"
    info_text += f"アクティブな接続数: {info['connection_count']}\n"
    info_text += f"接続プールサイズ: {info['pool_size']}\n"
    info_text += f"最大オーバーフロー接続数: {info['max_overflow']}"
    
    return [{
        "type": "text",
        "text": info_text
    }]
