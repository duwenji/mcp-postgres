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
postgres://{resource_type}/{identifier}
```

例:
- `postgres://tables` - テーブル一覧
- `postgres://schema/users` - usersテーブルのスキーマ
- `postgres://info` - データベース情報

## リソース実装の詳細

### 1. リソース管理クラスの実装

```python
# src/mcp_postgres_duwenji/resources.py
from mcp.server import Server
from mcp.server.models import Resource
from typing import List, Dict, Any, Optional
import logging
import json
from urllib.parse import urlparse

from .database import DatabaseManagerSingleton

logger = logging.getLogger(__name__)

class ResourceManager:
    """リソース管理クラス"""
    
    def __init__(self):
        self.db_manager = DatabaseManagerSingleton.get_instance()
    
    def get_tables_resource(self) -> str:
        """テーブル一覧リソースを生成"""
        try:
            query = """
                SELECT 
                    table_name,
                    table_type,
                    table_schema
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """
            
            tables = self.db_manager.execute_query(query)
            
            resource_data = {
                "resource_type": "tables",
                "count": len(tables),
                "tables": tables
            }
            
            return json.dumps(resource_data, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"テーブル一覧リソースの生成に失敗: {str(e)}")
            return json.dumps({
                "resource_type": "tables",
                "error": str(e),
                "tables": []
            })
    
    def get_table_schema_resource(self, table_name: str) -> str:
        """テーブルスキーマリソースを生成"""
        try:
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
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position
            """
            
            columns = self.db_manager.execute_query(columns_query, {"table_name": table_name})
            
            # 制約情報の取得
            constraints_query = """
                SELECT 
                    constraint_name,
                    constraint_type
                FROM information_schema.table_constraints 
                WHERE table_schema = 'public' AND table_name = %s
            """
            
            constraints = self.db_manager.execute_query(constraints_query, {"table_name": table_name})
            
            # インデックス情報の取得
            indexes_query = """
                SELECT 
                    indexname,
                    indexdef
                FROM pg_indexes 
                WHERE schemaname = 'public' AND tablename = %s
            """
            
            indexes = self.db_manager.execute_query(indexes_query, {"table_name": table_name})
            
            resource_data = {
                "resource_type": "table_schema",
                "table_name": table_name,
                "columns": columns,
                "constraints": constraints,
                "indexes": indexes
            }
            
            return json.dumps(resource_data, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"テーブルスキーマリソースの生成に失敗: {str(e)}")
            return json.dumps({
                "resource_type": "table_schema",
                "table_name": table_name,
                "error": str(e),
                "columns": [],
                "constraints": [],
                "indexes": []
            })
    
    def get_database_info_resource(self) -> str:
        """データベース情報リソースを生成"""
        try:
            db_info = self.db_manager.get_database_info()
            
            # 追加のデータベース統計情報
            stats_query = """
                SELECT 
                    count(*) as table_count,
                    sum(pg_relation_size(schemaname||'.'||tablename)) as total_size_bytes
                FROM pg_tables 
                WHERE schemaname = 'public'
            """
            
            stats = self.db_manager.execute_query(stats_query)
            
            resource_data = {
                "resource_type": "database_info",
                "database": db_info['current_database'],
                "version": db_info['version'],
                "connection_count": db_info['connection_count'],
                "pool_size": db_info['pool_size'],
                "max_overflow": db_info['max_overflow'],
                "table_count": stats[0]['table_count'] if stats else 0,
                "total_size_bytes": stats[0]['total_size_bytes'] if stats else 0
            }
            
            return json.dumps(resource_data, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"データベース情報リソースの生成に失敗: {str(e)}")
            return json.dumps({
                "resource_type": "database_info",
                "error": str(e)
            })
    
    def get_query_history_resource(self, limit: int = 10) -> str:
        """クエリ履歴リソースを生成（簡易実装）"""
        # 注: 本番環境では永続的なクエリ履歴ストレージが必要
        resource_data = {
            "resource_type": "query_history",
            "limit": limit,
            "note": "クエリ履歴機能は簡易実装です",
            "queries": []
        }
        
        return json.dumps(resource_data, indent=2, ensure_ascii=False)

def register_resources(server: Server) -> None:
    """リソースをMCPサーバーに登録"""
    
    resource_manager = ResourceManager()
    
    @server.list_resources()
    async def handle_list_resources() -> List[Resource]:
        """利用可能なリソースの一覧を返す"""
        return [
            Resource(
                uri="postgres://tables",
                name="Database Tables",
                description="データベースのテーブル一覧",
                mimeType="application/json"
            ),
            Resource(
                uri="postgres://info",
                name="Database Information",
                description="データベースの基本情報",
                mimeType="application/json"
            ),
            Resource(
                uri="postgres://query_history",
                name="Query History",
                description="実行されたクエリの履歴",
                mimeType="application/json"
            )
        ]
    
    @server.read_resource()
    async def handle_read_resource(uri: str) -> str:
        """リソースの内容を読み込む"""
        try:
            parsed_uri = urlparse(uri)
            path_parts = parsed_uri.path.strip('/').split('/')
            
            if uri == "postgres://tables":
                return resource_manager.get_tables_resource()
            
            elif uri == "postgres://info":
                return resource_manager.get_database_info_resource()
            
            elif uri == "postgres://query_history":
                return resource_manager.get_query_history_resource()
            
            elif parsed_uri.path.startswith("/schema/"):
                table_name = path_parts[1] if len(path_parts) > 1 else None
                if table_name:
                    return resource_manager.get_table_schema_resource(table_name)
                else:
                    return json.dumps({"error": "テーブル名が指定されていません"})
            
            else:
                return json.dumps({"error": f"不明なリソースURI: {uri}"})
                
        except Exception as e:
            logger.error(f"リソース読み込みエラー: {str(e)}")
            return json.dumps({"error": f"リソースの読み込みに失敗しました: {str(e)}"})
```

### 2. 動的リソースの自動生成

```python
# src/mcp_postgres_duwenji/resources.py (続き)

class DynamicResourceGenerator:
    """動的リソース生成クラス"""
    
    def __init__(self):
        self.resource_manager = ResourceManager()
    
    def generate_table_resources(self) -> List[Resource]:
        """テーブルごとのリソースを動的に生成"""
        try:
            query = """
                SELECT table_name
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """
            
            tables = self.resource_manager.db_manager.execute_query(query)
            
            resources = []
            for table in tables:
                table_name = table['table_name']
                resources.append(
                    Resource(
                        uri=f"postgres://schema/{table_name}",
                        name=f"Table Schema: {table_name}",
                        description=f"{table_name}テーブルの詳細なスキーマ情報",
                        mimeType="application/json"
                    )
                )
            
            return resources
            
        except Exception as e:
            logger.error(f"動的リソース生成エラー: {str(e)}")
            return []
    
    def generate_dynamic_resources(self) -> List[Resource]:
        """すべての動的リソースを生成"""
        dynamic_resources = []
        
        # テーブルスキーマリソースの追加
        dynamic_resources.extend(self.generate_table_resources())
        
        return dynamic_resources

def register_dynamic_resources(server: Server) -> None:
    """動的リソースをMCPサーバーに登録"""
    
    generator = DynamicResourceGenerator()
    
    @server.list_resources()
    async def handle_list_resources() -> List[Resource]:
        """静的リソースと動的リソースの一覧を返す"""
        static_resources = [
            Resource(
                uri="postgres://tables",
                name="Database Tables",
                description="データベースのテーブル一覧",
                mimeType="application/json"
            ),
            Resource(
                uri="postgres://info",
                name="Database Information",
                description="データベースの基本情報",
                mimeType="application/json"
            ),
            Resource(
                uri="postgres://query_history",
                name="Query History",
                description="実行されたクエリの履歴",
                mimeType="application/json"
            )
        ]
        
        dynamic_resources = generator.generate_dynamic_resources()
        
        return static_resources + dynamic_resources
```

### 3. リソースキャッシュの実装

```python
# src/mcp_postgres_duwenji/resources.py (続き)

import time
from typing import Dict, Tuple

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

class CachedResourceManager(ResourceManager):
    """キャッシュ付きリソース管理クラス"""
    
    def __init__(self):
        super().__init__()
        self.cache = ResourceCache()
    
    def get_tables_resource(self) -> str:
        """キャッシュ付きテーブル一覧リソース生成"""
        cache_key = "tables"
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug("テーブル一覧をキャッシュから取得")
            return cached
        
        result = super().get_tables_resource()
        self.cache.set(cache_key, result)
        return result
    
    def get_table_schema_resource(self, table_name: str) -> str:
        """キャッシュ付きテーブルスキーマリソース生成"""
        cache_key = f"schema_{table_name}"
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug(f"テーブルスキーマ {table_name} をキャッシュから取得")
            return cached
        
        result = super().get_table_schema_resource(table_name)
        self.cache.set(cache_key, result)
        return result
    
    def get_database_info_resource(self) -> str:
        """キャッシュ付きデータベース情報リソース生成"""
        cache_key = "database_info"
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug("データベース情報をキャッシュから取得")
            return cached
        
        result = super().get_database_info_resource()
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
# AIが postgres://tables リソースを参照して利用可能なテーブルを把握

# 2. テーブル詳細の確認  
# AIが postgres://schema/users リソースを参照してusersテーブルの構造を理解

# 3. クエリの最適化
# AIがスキーマ情報を基に適切なクエリを生成
```

### 2. リソース更新のトリガー

```python
class ResourceUpdateManager:
    """リソース更新管理"""
    
    def __init__(self, cached_manager: CachedResourceManager):
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
            "query_history": 30   # 30秒
        }
    
    def get_ttl_for_key(self, key: str) -> int:
        """キーに基づいてTTLを決定"""
        for pattern, ttl in self.ttl_config.items():
            if pattern in key:
                return ttl
        return self.ttl  # デフォルトTTL
```

### 2. リソースの部分更新

```python
def get_partial_table_schema(self, table_name: str, fields: List[str] = None) -> str:
    """テーブルスキーマの部分的な取得"""
    full_schema = json.loads(self.get_table_schema_resource(table_name))
    
    if fields:
        partial_schema = {field: full_schema.get(field) for field in fields}
        return json.dumps(partial_schema, indent=2, ensure_ascii=False)
    
    return json.dumps(full_schema, indent=2, ensure_ascii=False)
```

## セキュリティ考慮事項

### 1. リソースアクセス制御

```python
def validate_resource_access(uri: str, user_context: Dict[str, Any]) -> bool:
    """リソースアクセスの検証"""
    # ユーザーコンテキストに基づいたアクセス制御
    if uri.startswith("postgres://schema/") and not user_context.get('can_read_schema'):
        return False
    
    return True
```

### 2. 機密情報のマスキング

```python
def get_safe_database_info(self) -> str:
    """安全なデータベース情報（機密情報をマスク）"""
    db_info = self.db_manager.get_database_info()
    
    safe_info = {
        "resource_type": "database_info",
        "database": db_info['current_database'],
        "version": db_info['version'],
        "connection_count": db_info['connection_count'],
        "pool_size": db_info['pool_size'],
        "host": "***",  # 機密情報をマスク
        "user": "***"   # 機密情報をマスク
    }
    
    return json.dumps(safe_info, indent=2, ensure_
