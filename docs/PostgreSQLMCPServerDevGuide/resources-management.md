# リソース管理ガイド

このガイドでは、PostgreSQL MCPサーバーのリソース管理機能の実装方法について説明します。MCPリソースはAIアシスタントが参照できる情報を提供します。

## リソースの基本概念

### リソースの種類

1. **静的リソース**: 固定された情報（例：データベース接続情報）
2. **動的リソース**: 実行時に生成される情報（例：テーブル一覧、スキーマ情報）
3. **永続的リソース**: 変更されない情報
4. **一時的リソース**: 一時的な情報

### リソースURIの設計

```
database://{resource_type}/{identifier}
```

例:
- `database://tables` - テーブル一覧
- `database://schema/users` - usersテーブルのスキーマ
- `database://info` - データベース情報

## 現在の実装

### 1. リソース管理クラスの実装

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

### 2. 動的リソースの自動生成

現在の実装では、メインファイル（main.py）で動的にテーブルスキーマリソースを生成しています：

```python
# src/mcp_postgres_duwenji/main.py の一部
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
```

## キャッシュ機能の実装

### 現在の実装状況

**現在の実装にはキャッシュ機能は含まれていません：**
- 各リソースメソッドは毎回データベース接続を確立してクエリを実行
- 明示的なキャッシュ機構は実装されていない
- MCPパッケージ自体に組み込みのキャッシュ機能はない

### 推奨キャッシュ実装

```python
# 推奨キャッシュ実装例
import time
from typing import Dict, Tuple, Optional

class ResourceCache:
    """リソースキャッシュ管理"""
    
    def __init__(self, ttl: int = 300):  # 5分間キャッシュ
        self.cache: Dict[str, Tuple[str, float]] = {}
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[str]:
        """キャッシュから値を取得"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                # TTL超過でキャッシュを削除
                del self.cache[key]
        return None
    
    def set(self, key: str, value: str) -> None:
        """キャッシュに値を設定"""
        self.cache[key] = (value, time.time())
    
    def clear(self) -> None:
        """キャッシュをクリア"""
        self.cache.clear()

class CachedDatabaseResourceManager(DatabaseResourceManager):
    """キャッシュ付きリソース管理クラス"""
    
    def __init__(self):
        super().__init__()
        self.cache = ResourceCache()
    
    async def get_tables_resource(self) -> str:
        """キャッシュ付きテーブル一覧リソース生成"""
        cache_key = "tables"
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug("テーブル一覧をキャッシュから取得")
            return cached
        
        result = await super().get_tables_resource()
        self.cache.set(cache_key, result)
        return result
    
    async def get_table_schema_resource(self, table_name: str, schema: str = "public") -> str:
        """キャッシュ付きテーブルスキーマリソース生成"""
        cache_key = f"schema_{schema}_{table_name}"
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug(f"テーブルスキーマ {schema}.{table_name} をキャッシュから取得")
            return cached
        
        result = await super().get_table_schema_resource(table_name, schema)
        self.cache.set(cache_key, result)
        return result
    
    async def get_database_info_resource(self) -> str:
        """キャッシュ付きデータベース情報リソース生成"""
        cache_key = "database_info"
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug("データベース情報をキャッシュから取得")
            return cached
        
        result = await super().get_database_info_resource()
        self.cache.set(cache_key, result)
        return result
    
    def invalidate_cache(self, pattern: str = None) -> None:
        """キャッシュを無効化"""
        if pattern:
            keys_to_remove = [key for key in self.cache.cache.keys() if pattern in key]
            for key in keys_to_remove:
                if key in self.cache.cache:
                    del self.cache.cache[key]
        else:
            self.cache.clear()
```

## リソースの活用パターン

### 1. AIアシスタントとの連携

```python
# リソースを活用したAIアシスタントの動作例

# 1. データベース構造の理解
# AIが database://tables リソースを参照して利用可能なテーブルを把握

# 2. テーブル詳細の確認  
# AIが database://schema/users リソースを参照してusersテーブルの構造を理解

# 3. クエリの最適化
# AIがスキーマ情報を基に適切なクエリを生成
```

### 2. リソース更新のトリガー

```python
class ResourceUpdateManager:
    """リソース更新管理"""
    
    def __init__(self, cached_manager: CachedDatabaseResourceManager):
        self.cached_manager = cached_manager
    
    def on_table_change(self, table_name: str) -> None:
        """テーブル変更時のキャッシュ無効化"""
        self.cached_manager.invalidate_cache(f"schema_{table_name}")
        self.cached_manager.invalidate_cache("tables")
        logger.info(f"テーブル {table_name} 関連のキャッシュを無効化")
    
    def on_database_change(self) -> None:
        """データベース変更時のキャッシュ無効化"""
        self.cached_manager.invalidate_cache()
        logger.info("データベース関連のすべてのキャッシュを無効化")
```

## パフォーマンス最適化

### 1. キャッシュ戦略

```python
class SmartResourceCache(ResourceCache):
    """スマートキャッシュ管理"""
    
    def __init__(self):
        super().__init__()
        # リソースタイプごとのTTL設定
        self.ttl_config = {
            "tables": 300,        # 5分
            "schema": 600,        # 10分  
            "database_info": 60,  # 1分
        }
    
    def get_ttl_for_key(self, key: str) -> int:
        """キーに基づいてTTLを決定"""
        for pattern, ttl in self.ttl_config.items():
            if pattern in key:
                return ttl
        return self.ttl  # デフォルトTTL
```

## セキュリティ考慮事項

### 1. リソースアクセス制御

```python
def validate_resource_access(uri: str, user_context: Dict[str, Any]) -> bool:
    """リソースアクセスの検証"""
    # ユーザーコンテキストに基づいたアクセス制御
    if uri.startswith("database://schema/") and not user_context.get('can_read_schema'):
        return False
    
    return True
```

### 2. 機密情報のマスキング

```python
def get_safe_database_info(self) -> str:
    """安全なデータベース情報（機密情報をマスク）"""
    # 現在の実装では機密情報は含まれていない
    return await self.get_database_info_resource()
```

## まとめ

現在の実装は以下の特徴を持っています：
- **URI形式**: `database://` プレフィックス
- **コンテンツ形式**: Markdown形式
- **キャッシュ**: 実装されていない（推奨実装を提供）
- **リソースタイプ**: テーブル一覧、テーブルスキーマ、データベース情報

キャッシュ機能の実装により、パフォーマンスの大幅な改善が期待できます。
