# プロジェクト構造ガイド

このガイドでは、PostgreSQL MCPサーバーのプロジェクト構造と各ファイルの役割について説明します。

## プロジェクト全体構造

```
mcp-postgres-duwenji/
├── src/
│   └── mcp_postgres_duwenji/
│       ├── __init__.py
│       ├── main.py              # MCPサーバーコア
│       ├── config.py            # 設定管理
│       ├── database.py          # データベース接続
│       ├── resources.py         # リソース管理
│       └── tools/
│           ├── __init__.py
│           ├── crud_tools.py    # CRUD操作ツール
│           └── schema_tools.py  # スキーマ情報ツール
├── docs/                        # ドキュメント
├── test/                        # テストファイル
├── scripts/                     # ユーティリティスクリプト
├── pyproject.toml              # プロジェクト設定
├── README.md                   # プロジェクト説明
├── CHANGELOG.md               # 変更履歴
├── LICENSE                    # ライセンス
└── .gitignore                 # Git除外設定
```

## 主要ファイルの役割

### 1. pyproject.toml - プロジェクト設定

```toml
[project]
name = "mcp-postgres-duwenji"
version = "1.0.1"
description = "MCP server for PostgreSQL database operations"
authors = [
    { name = "mcp-postgres" },
    { name = "duwenji", email = "duwenji@gmail.com" },
]
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "build>=1.3.0",
    "mcp>=1.0.0",
    "psycopg2-binary>=2.9.0",
    "pydantic>=2.0.0",
    "python-dotenv>=1.0.0",
    "twine>=6.2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.0.0",
    "pytest-xdist>=3.0.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "mypy>=1.0.0",
    "freezegun>=1.0.0",
]

[project.scripts]
mcp_postgres_duwenji = "mcp_postgres_duwenji.main:cli_main"

[build-system]
requires = ["uv_build >= 0.9.2, <0.10.0"]
build-backend = "uv_build"

[tool.black]
target-version = ['py310']
line-length = 88
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.mypy]
python_version = "1.0.1"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["test"]

[tool.uv]
[dependency-groups]
dev = [
    "pytest>=8.4.2",
    "pytest-cov>=7.0.0",
]
```

**役割**:
- プロジェクトメタデータの定義
- 依存関係の管理
- ビルドシステムの設定
- スクリプトエントリーポイントの定義

### 2. main.py - MCPサーバーコア

```python
# src/mcp_postgres_duwenji/main.py
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
from .resources import get_database_resources, get_resource_handlers, get_table_schema_resource_handler
from mcp import Resource

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
                            mimeType="text/markdown"
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
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def cli_main():
    """CLI entry point for uv run"""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()
```

**役割**:
- MCPサーバーの起動と実行
- ツールとリソースの登録管理
- プロトコル通信の処理

### 3. config.py - 設定管理

```python
# src/mcp_postgres_duwenji/config.py
from pydantic import BaseSettings, Field
from typing import Optional

class PostgresConfig(BaseSettings):
    """PostgreSQL接続設定"""
    host: str = Field(..., description="データベースホスト")
    port: int = Field(5432, description="データベースポート")
    database: str = Field(..., description="データベース名")
    username: str = Field(..., description="ユーザー名")
    password: str = Field(..., description="パスワード")
    ssl_mode: str = Field("prefer", description="SSLモード")
    pool_size: int = Field(5, description="接続プールサイズ")
    max_overflow: int = Field(10, description="最大オーバーフロー接続数")
    
    class Config:
        env_prefix = "POSTGRES_"
        case_sensitive = False

def load_config() -> PostgresConfig:
    """設定の読み込み"""
    return PostgresConfig()
```

**役割**:
- 環境変数からの設定読み込み
- 設定値のバリデーション
- デフォルト値の提供

### 4. database.py - データベース接続

```python
# src/mcp_postgres_duwenji/database.py
import psycopg2
from psycopg2 import pool
from typing import List, Dict, Any
from .config import PostgresConfig

class DatabaseManager:
    """データベース接続管理"""
    
    def __init__(self, config: PostgresConfig):
        self.config = config
        self.connection_pool = None
    
    def initialize_pool(self):
        """接続プールの初期化"""
        self.connection_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=self.config.pool_size,
            host=self.config.host,
            port=self.config.port,
            database=self.config.database,
            user=self.config.username,
            password=self.config.password,
            sslmode=self.config.ssl_mode
        )
    
    def execute_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """クエリの実行"""
        if not self.connection_pool:
            self.initialize_pool()
        
        connection = self.connection_pool.getconn()
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    results = cursor.fetchall()
                    return [dict(zip(columns, row)) for row in results]
                else:
                    return []
        finally:
            self.connection_pool.putconn(connection)
```

**役割**:
- データベース接続プールの管理
- クエリ実行の抽象化
- 接続リソースの効率的な管理

### 5. tools/ - ツール実装

#### crud_tools.py

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

#### schema_tools.py

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

**役割**:
- MCPツールの定義と実装
- 入力パラメータのバリデーション
- ツール実行ロジックのカプセル化

### 6. resources.py - リソース管理

```python
# src/mcp_postgres_duwenji/resources.py
"""
Resource management for PostgreSQL MCP Server
"""

import logging
from typing import List, Dict, Any
from mcp import Resource

from .database import DatabaseManager, DatabaseError
from .config import load_config

logger = logging.getLogger(__name__)


class DatabaseResourceManager:
    """Manage database-related resources"""
    
    def __init__(self):
        self.config = load_config()
        self.db_manager = DatabaseManager(self.config.postgres)
    
    async def get_tables_resource(self) -> str:
        """Get tables list as resource content"""
        try:
            self.db_manager.connection.connect()
            result = self.db_manager.get_tables()
            self.db_manager.connection.disconnect()
            
            if result["success"]:
                tables = result["tables"]
                content = f"# Database Tables in {self.config.postgres.database}\n\n"
                content += f"Total tables: {len(tables)}\n\n"
                
                for table in tables:
                    content += f"- {table}\n"
                
                return content
            else:
                return f"Error retrieving tables: {result['error']}"
                
        except Exception as e:
            logger.error(f"Error in get_tables_resource: {e}")
            return f"Error retrieving tables: {str(e)}"
    
    async def get_table_schema_resource(self, table_name: str, schema: str = "public") -> str:
        """Get table schema as resource content"""
        try:
            self.db_manager.connection.connect()
            
            # Get table schema information
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
            
            columns = self.db_manager.connection.execute_query(query, (schema, table_name))
            
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
            
            constraints = self.db_manager.connection.execute_query(constraints_query, (schema, table_name))
            
            self.db_manager.connection.disconnect()
            
            # Format content
            content = f"# Table Schema: {schema}.{table_name}\n\n"
            
            # Columns section
            content += "## Columns\n\n"
            content += "| Column Name | Data Type | Nullable | Default | Max Length | Precision | Scale |\n"
            content += "|-------------|-----------|----------|---------|------------|-----------|-------|\n"
            
            for col in columns:
                content += f"| {col['column_name']} | {col['data_type']} | {col['is_nullable']} | {col['column_default'] or 'NULL'} | {col['character_maximum_length'] or '-'} | {col['numeric_precision'] or '-'} | {col['numeric_scale'] or '-'} |\n"
            
            content += "\n"
            
            # Constraints section
            if constraints:
                content += "## Constraints\n\n"
                content += "| Constraint Name | Type | Column |\n"
                content += "|-----------------|------|--------|\n"
                
                for constraint in constraints:
                    content += f"| {constraint['constraint_name']} | {constraint['constraint_type']} | {constraint['column_name'] or '-'} |\n"
            
            return content
            
        except Exception as e:
            logger.error(f"Error in get_table_schema_resource: {e}")
            return f"Error retrieving table schema: {str(e)}"
    
    async def get_database_info_resource(self) -> str:
        """Get database information as resource content"""
        try:
            self.db_manager.connection.connect()
            
            # Get database version
            version_result = self.db_manager.connection.execute_query("SELECT version();")
            version = version_result[0]["version"] if version_result else "Unknown"
            
            # Get database name and current user
            db_info_result = self.db_manager.connection.execute_query(
                "SELECT current_database(), current_user, current_schema();"
            )
            db_info = db_info_result[0] if db_info_result else {}
            
            # Get database size
            size_result = self.db_manager.connection.execute_query(
                "SELECT pg_size_pretty(pg_database_size(current_database())) as database_size;"
            )
            database_size = size_result[0]["database_size"] if size_result else "Unknown"
            
            # Get number of tables
            tables_count_result = self.db_manager.connection.execute_query(
                "SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'public';"
            )
            table_count = tables_count_result[0]["table_count"] if tables_count_result else 0
            
            self.db_manager.connection.disconnect()
            
            # Format content
            content = f"# Database Information\n\n"
            content += f"**Database Name**: {db_info.get('current_database', 'Unknown')}\n"
            content += f"**PostgreSQL Version**: {version}\n"
            content += f"**Current User**: {db_info.get('current_user', 'Unknown')}\n"
            content += f"**Current Schema**: {db_info.get('current_schema', 'Unknown')}\n"
            content += f"**Database Size**: {database_size}\n"
            content += f"**Table Count**: {table_count}\n"
            
            return content
            
        except Exception as e:
            logger.error(f"Error in get_database_info_resource: {e}")
            return f"Error retrieving database information: {str(e)}"


# Resource definitions
database_tables_resource = Resource(
    uri="database://tables",
    name="Database Tables",
    description="List of all tables in the database",
    mimeType="text/markdown"
)

database_info_resource = Resource(
    uri="database://info",
    name="Database Information",
    description="Database metadata and version information",
    mimeType="text/markdown"
)


def get_database_resources() -> List[Resource]:
    """Get all database resources"""
    return [
        database_tables_resource,
        database_info_resource,
    ]


def get_resource_handlers() -> Dict[str, callable]:
    """Get resource handlers"""
    resource_manager = DatabaseResourceManager()
    
    return {
        "database://tables": resource_manager.get_tables_resource,
        "database://info": resource_manager.get_database_info_resource,
    }


def get_table_schema_resource_handler() -> callable:
    """Get table schema resource handler factory"""
    resource_manager = DatabaseResourceManager()
    return resource_manager.get_table_schema_resource
```

**役割**:
- 静的リソースの定義
- 動的リソースの生成
- リソースURIの管理

## ディレクトリ構造の設計思想

### 1. 関心の分離
- **main.py**: サーバー起動とプロトコル処理
- **config.py**: 設定管理
- **database.py**: データベース操作
- **tools/**: 機能ごとのツール実装
- **resources.py**: リソース管理

### 2. 拡張性の確保
- 新しいツールの追加が容易
- 設定の柔軟な変更
- データベース接続の交換可能性

### 3. テストのしやすさ
- 各コンポーネントが独立してテスト可能
- モックを使用した単体テストの実現
- 依存関係の明示的な管理

## ベストプラクティス

### 1. 環境変数の使用

#### Linux/macOS
```bash
# 必須設定
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=mydatabase
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword

# オプション設定
POSTGRES_SSL_MODE=prefer
POSTGRES_POOL_SIZE=5
POSTGRES_MAX_OVERFLOW=10
```

#### Windows
```powershell
# PowerShellでの一時的な環境変数設定
$env:POSTGRES_HOST="localhost"
$env:POSTGRES_PORT=5432
$env:POSTGRES_DB="mydatabase"
$env:POSTGRES_USER="myuser"
$env:POSTGRES_PASSWORD="mypassword"
$env:POSTGRES_SSL_MODE="prefer"
$env:POSTGRES_POOL_SIZE=5
$env:POSTGRES_MAX_OVERFLOW=10

# または永続的な設定（管理者権限が必要な場合あり）
[System.Environment]::SetEnvironmentVariable("POSTGRES_HOST", "localhost", "User")
[System.Environment]::SetEnvironmentVariable("POSTGRES_PORT", "5432", "User")
[System.Environment]::SetEnvironmentVariable("POSTGRES_DB", "mydatabase", "User")
[System.Environment]::SetEnvironmentVariable("POSTGRES_USER", "myuser", "User")
[System.Environment]::SetEnvironmentVariable("POSTGRES_PASSWORD", "mypassword", "User")
```

**注意**: WindowsではPowerShellを使用することを推奨します。環境変数の設定後、新しいPowerShellセッションを開始してください。

### 2. エラーハンドリング
```python
try:
    result = database.execute_query(query, params)
except psycopg2.Error as e:
    logger.error(f"Database error: {e}")
    raise MCPError(f"Query execution failed: {str(e)}")
```

### 3. ロギング
```python
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 構造化ロギングの実装
logger.info("Query executed", extra={
    "query": query,
    "params": params,
    "row_count": len(result)
})
```

## トラブルシューティング

### よくある問題

1. **インポートエラー**
   - Pythonパスが正しく設定されているか確認
   - `__init__.py`ファイルが存在するか確認

2. **設定読み込みエラー**
   - 環境変数が正しく設定されているか確認
   - 設定ファイルのパスを確認

3. **データベース接続エラー**
   - 接続情報が正しいか確認
   - ネットワーク接続を確認
   - ファイアウォール設定を確認

このプロジェクト構造を理解することで、独自のMCPサーバー開発や既存サーバーの拡張が容易になります。
