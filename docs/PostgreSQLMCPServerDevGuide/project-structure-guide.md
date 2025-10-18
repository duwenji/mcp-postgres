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
├── examples/                    # 設定例
├── test/                        # テストファイル
├── scripts/                     # ユーティリティスクリプト
├── pyproject.toml              # プロジェクト設定
├── README.md                   # プロジェクト説明
├── README_ja.md               # 日本語説明
├── CHANGELOG.md               # 変更履歴
├── LICENSE                    # ライセンス
└── .gitignore                 # Git除外設定
```

## 主要ファイルの役割

### 1. pyproject.toml - プロジェクト設定

```toml
[project]
name = "mcp-postgres-duwenji"
version = "1.0.0"
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

[project.scripts]
mcp-postgres = "mcp_postgres_duwenji.main:main"

[build-system]
requires = ["uv_build >= 0.9.2, <0.10.0"]
build-backend = "uv_build"
```

**役割**:
- プロジェクトメタデータの定義
- 依存関係の管理
- ビルドシステムの設定
- スクリプトエントリーポイントの定義

### 2. main.py - MCPサーバーコア

```python
# src/mcp_postgres_duwenji/main.py
import asyncio
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio

# サーバーの作成
server = Server("postgres-mcp")

# ツールとリソースの登録
from .tools.crud_tools import register_crud_tools
from .tools.schema_tools import register_schema_tools
from .resources import register_resources

register_crud_tools(server)
register_schema_tools(server)
register_resources(server)

async def main():
    # 標準入出力でサーバーを実行
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="postgres-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                )
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
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
from mcp.server import Server
from typing import Dict, Any

def register_crud_tools(server: Server):
    """CRUD操作ツールの登録"""
    
    @server.list_tools()
    async def handle_list_tools():
        return [
            {
                "name": "query_execute",
                "description": "SQLクエリを実行します",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "実行するSQLクエリ"},
                        "params": {"type": "object", "description": "クエリパラメータ"}
                    },
                    "required": ["query"]
                }
            }
        ]
    
    @server.call_tool()
    async def handle_call_tool(name: str, arguments: Dict[str, Any]):
        if name == "query_execute":
            # クエリ実行ロジック
            pass
```

#### schema_tools.py

```python
# src/mcp_postgres_duwenji/tools/schema_tools.py
from mcp.server import Server

def register_schema_tools(server: Server):
    """スキーマ情報ツールの登録"""
    
    @server.list_tools()
    async def handle_list_tools():
        return [
            {
                "name": "get_tables",
                "description": "データベースのテーブル一覧を取得します",
                "inputSchema": {"type": "object", "properties": {}}
            }
        ]
```

**役割**:
- MCPツールの定義と実装
- 入力パラメータのバリデーション
- ツール実行ロジックのカプセル化

### 6. resources.py - リソース管理

```python
# src/mcp_postgres_duwenji/resources.py
from mcp.server import Server
from typing import List

def register_resources(server: Server):
    """リソースの登録"""
    
    @server.list_resources()
    async def handle_list_resources() -> List[dict]:
        return [
            {
                "uri": "postgres://tables",
                "name": "Database Tables",
                "description": "データベースのテーブル一覧",
                "mimeType": "application/json"
            }
        ]
    
    @server.read_resource()
    async def handle_read_resource(uri: str) -> str:
        if uri == "postgres://tables":
            # テーブル一覧の取得ロジック
            return '{"tables": []}'
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
