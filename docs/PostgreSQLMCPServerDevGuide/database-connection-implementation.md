# データベース接続実装ガイド

このガイドでは、PostgreSQL MCPサーバーのデータベース接続機能の実装方法について詳細に説明します。

## 接続管理の基本設計

### 接続プーリングの重要性

データベース接続の確立はリソース集約的な操作です。接続プーリングを使用することで：
- 接続の再利用によるパフォーマンス向上
- 同時接続数の制御
- リソースリークの防止

### 実装アプローチ

1. **SimpleConnectionPool**: 基本的な接続プーリング
2. **ThreadedConnectionPool**: マルチスレッド環境向け
3. **Async Connection Pool**: 非同期環境向け

## 実装詳細

### 1. 設定クラスの実装

```python
# src/mcp_postgres_duwenji/config.py
from pydantic import BaseSettings, Field, validator
from typing import Optional
import os

class PostgresConfig(BaseSettings):
    """PostgreSQL接続設定"""
    
    host: str = Field(..., description="データベースホスト名またはIPアドレス")
    port: int = Field(5432, description="データベースポート番号")
    database: str = Field(..., description="データベース名")
    username: str = Field(..., description="接続ユーザー名")
    password: str = Field(..., description="接続パスワード")
    
    # 接続プール設定
    pool_size: int = Field(5, description="接続プールの最小接続数")
    max_overflow: int = Field(10, description="接続プールの最大オーバーフロー接続数")
    pool_timeout: int = Field(30, description="接続取得のタイムアウト（秒）")
    
    # SSL設定
    ssl_mode: str = Field("prefer", description="SSLモード (disable, allow, prefer, require, verify-ca, verify-full)")
    
    # 接続タイムアウト
    connect_timeout: int = Field(10, description="接続確立のタイムアウト（秒）")
    command_timeout: int = Field(30, description="コマンド実行のタイムアウト（秒）")
    
    class Config:
        env_prefix = "POSTGRES_"
        case_sensitive = False
        env_file = ".env"
    
    @validator('ssl_mode')
    def validate_ssl_mode(cls, v):
        valid_modes = ['disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full']
        if v not in valid_modes:
            raise ValueError(f"SSLモードは {valid_modes} のいずれかである必要があります")
        return v
    
    @validator('pool_size')
    def validate_pool_size(cls, v):
        if v < 1:
            raise ValueError("プールサイズは1以上である必要があります")
        return v

def load_config() -> PostgresConfig:
    """設定の読み込みとバリデーション"""
    try:
        config = PostgresConfig()
        return config
    except Exception as e:
        raise ValueError(f"設定の読み込みに失敗しました: {str(e)}")
```

### 2. データベースマネージャーの実装

```python
# src/mcp_postgres_duwenji/database.py
import psycopg2
from psycopg2 import pool, sql
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional, Union
import logging
import time
from contextlib import contextmanager

from .config import PostgresConfig

logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """データベース操作に関するカスタム例外"""
    pass

class ConnectionError(DatabaseError):
    """接続関連のエラー"""
    pass

class QueryError(DatabaseError):
    """クエリ実行関連のエラー"""
    pass

class DatabaseManager:
    """データベース接続と操作を管理するクラス"""
    
    def __init__(self, config: PostgresConfig):
        self.config = config
        self.connection_pool: Optional[pool.SimpleConnectionPool] = None
        self._is_initialized = False
    
    def initialize(self) -> None:
        """データベース接続プールの初期化"""
        if self._is_initialized:
            return
        
        try:
            logger.info("データベース接続プールを初期化しています...")
            
            # 接続パラメータの構築
            connection_params = {
                'host': self.config.host,
                'port': self.config.port,
                'database': self.config.database,
                'user': self.config.username,
                'password': self.config.password,
                'sslmode': self.config.ssl_mode,
                'connect_timeout': self.config.connect_timeout,
            }
            
            # 接続プールの作成
            self.connection_pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=self.config.pool_size,
                **connection_params
            )
            
            # 接続テスト
            self._test_connection()
            
            self._is_initialized = True
            logger.info("データベース接続プールの初期化が完了しました")
            
        except psycopg2.OperationalError as e:
            logger.error(f"データベース接続に失敗しました: {str(e)}")
            raise ConnectionError(f"データベース接続に失敗しました: {str(e)}")
        except Exception as e:
            logger.error(f"接続プールの初期化に失敗しました: {str(e)}")
            raise DatabaseError(f"接続プールの初期化に失敗しました: {str(e)}")
    
    def _test_connection(self) -> None:
        """接続テストを実行"""
        connection = self.connection_pool.getconn()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result[0] != 1:
                    raise ConnectionError("接続テストに失敗しました")
        finally:
            self.connection_pool.putconn(connection)
    
    @contextmanager
    def get_connection(self):
        """接続を安全に取得するコンテキストマネージャ"""
        if not self._is_initialized:
            self.initialize()
        
        connection = None
        try:
            connection = self.connection_pool.getconn()
            yield connection
        except psycopg2.pool.PoolError as e:
            logger.error(f"接続の取得に失敗しました: {str(e)}")
            raise ConnectionError(f"接続の取得に失敗しました: {str(e)}")
        finally:
            if connection:
                self.connection_pool.putconn(connection)
    
    def execute_query(
        self, 
        query: str, 
        params: Dict[str, Any] = None,
        timeout: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """SQLクエリを実行し、結果を辞書のリストで返す"""
        
        if not query.strip():
            raise QueryError("クエリが空です")
        
        actual_timeout = timeout or self.config.command_timeout
        
        try:
            with self.get_connection() as connection:
                with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                    # タイムアウト設定
                    cursor.execute(f"SET statement_timeout = {actual_timeout * 1000}")
                    
                    # クエリ実行
                    start_time = time.time()
                    cursor.execute(query, params)
                    execution_time = time.time() - start_time
                    
                    # 結果の取得
                    if cursor.description:
                        results = cursor.fetchall()
                        # RealDictCursorはすでに辞書形式で結果を返す
                        return [dict(row) for row in results]
                    else:
                        # DMLクエリの場合
                        return [{"rows_affected": cursor.rowcount}]
                        
        except psycopg2.Error as e:
            logger.error(f"クエリ実行エラー: {str(e)}")
            raise QueryError(f"クエリ実行に失敗しました: {str(e)}")
    
    def execute_transaction(self, queries: List[Dict[str, Any]]) -> List[Any]:
        """トランザクション内で複数クエリを実行"""
        results = []
        
        with self.get_connection() as connection:
            try:
                connection.autocommit = False
                
                with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                    for query_info in queries:
                        query = query_info['query']
                        params = query_info.get('params')
                        
                        cursor.execute(query, params)
                        
                        if cursor.description:
                            results.append([dict(row) for row in cursor.fetchall()])
                        else:
                            results.append({"rows_affected": cursor.rowcount})
                
                connection.commit()
                return results
                
            except psycopg2.Error as e:
                connection.rollback()
                logger.error(f"トランザクションエラー: {str(e)}")
                raise QueryError(f"トランザクション実行に失敗しました: {str(e)}")
    
    def get_database_info(self) -> Dict[str, Any]:
        """データベースの基本情報を取得"""
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    # データベースバージョン
                    cursor.execute("SELECT version()")
                    version = cursor.fetchone()[0]
                    
                    # 現在のデータベース
                    cursor.execute("SELECT current_database()")
                    current_db = cursor.fetchone()[0]
                    
                    # 接続数
                    cursor.execute("""
                        SELECT count(*) 
                        FROM pg_stat_activity 
                        WHERE datname = %s
                    """, (current_db,))
                    connection_count = cursor.fetchone()[0]
                    
                    return {
                        "version": version,
                        "current_database": current_db,
                        "connection_count": connection_count,
                        "pool_size": self.config.pool_size,
                        "max_overflow": self.config.max_overflow
                    }
                    
        except psycopg2.Error as e:
            logger.error(f"データベース情報の取得に失敗しました: {str(e)}")
            raise DatabaseError(f"データベース情報の取得に失敗しました: {str(e)}")
    
    def close(self) -> None:
        """接続プールを閉じる"""
        if self.connection_pool:
            self.connection_pool.closeall()
            self._is_initialized = False
            logger.info("データベース接続プールを閉じました")
```

### 3. シングルトンパターンの実装

```python
# src/mcp_postgres_duwenji/database.py (続き)

class DatabaseManagerSingleton:
    """データベースマネージャーのシングルトン実装"""
    
    _instance: Optional[DatabaseManager] = None
    
    @classmethod
    def get_instance(cls, config: Optional[PostgresConfig] = None) -> DatabaseManager:
        """シングルトンインスタンスを取得"""
        if cls._instance is None:
            if config is None:
                from .config import load_config
                config = load_config()
            cls._instance = DatabaseManager(config)
            cls._instance.initialize()
        return cls._instance
    
    @classmethod
    def close_instance(cls) -> None:
        """シングルトンインスタンスを閉じる"""
        if cls._instance:
            cls._instance.close()
            cls._instance = None
```

## セキュリティ考慮事項

### 1. SQLインジェクション対策

```python
def safe_execute_query(
    self, 
    query: str, 
    params: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """安全なクエリ実行（パラメータ化クエリを使用）"""
    
    # 危険なSQLキーワードの検出
    dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE']
    upper_query = query.upper()
    
    for keyword in dangerous_keywords:
        if keyword in upper_query and 'WHERE' not in upper_query:
            logger.warning(f"危険なSQL操作が検出されました: {keyword}")
            # 本番環境では例外をスローすることを検討
            # raise QueryError(f"危険なSQL操作は許可されていません: {keyword}")
    
    return self.execute_query(query, params)
```

### 2. 接続文字列の保護

```python
def get_safe_connection_info(self) -> Dict[str, Any]:
    """安全な接続情報の取得（パスワードをマスク）"""
    return {
        "host": self.config.host,
        "port": self.config.port,
        "database": self.config.database,
        "username": self.config.username,
        "ssl_mode": self.config.ssl_mode,
        "pool_size": self.config.pool_size,
        "password": "***"  # パスワードをマスク
    }
```

## パフォーマンス最適化

### 1. 接続プールの監視

```python
def get_pool_stats(self) -> Dict[str, Any]:
    """接続プールの統計情報を取得"""
    if not self.connection_pool:
        return {"status": "not_initialized"}
    
    return {
        "status": "active",
        "min_connections": 1,
        "max_connections": self.config.pool_size,
        "current_connections": len(self.connection_pool._used),
        "available_connections": len(self.connection_pool._rlist)
    }
```

### 2. クエリパフォーマンスの監視

```python
def execute_query_with_stats(
    self, 
    query: str, 
    params: Dict[str, Any] = None
) -> Dict[str, Any]:
    """クエリ実行とパフォーマンス統計を返す"""
    start_time = time.time()
    
    try:
        result = self.execute_query(query, params)
        execution_time = time.time() - start_time
        
        return {
            "success": True,
            "execution_time": execution_time,
            "row_count": len(result) if isinstance(result, list) else 0,
            "result": result
        }
    except Exception as e:
        execution_time = time.time() - start_time
        return {
            "success": False,
            "execution_time": execution_time,
            "error": str(e),
            "result": None
        }
```

## テストと検証

### 1. 接続テスト

```python
def test_connection(self) -> bool:
    """データベース接続のテスト"""
    try:
        self._test_connection()
        return True
    except Exception as e:
        logger.error(f"接続テスト失敗: {str(e)}")
        return False
```

### 2. パフォーマンステスト

```python
def performance_test(self, iterations: int = 10) -> Dict[str, Any]:
    """基本的なパフォーマンステスト"""
    times = []
    
    for i in range(iterations):
        start_time = time.time()
        self.execute_query("SELECT 1")
        times.append(time.time() - start_time)
    
    return {
        "iterations": iterations,
        "average_time": sum(times) / len(times),
        "min_time": min(times),
        "max_time": max(times),
        "total_time": sum(times)
    }
```

## トラブルシューティング

### よくある問題と解決策

1. **接続タイムアウト**
   - ネットワーク接続を確認
   - ファイアウォール設定を確認
   - `connect_timeout` を増やす

2. **接続プールの枯渇**
   - `pool_size` を増やす
   - 接続リークがないか確認
   - `max_overflow` を調整

3. **SSL接続エラー**
   - SSL証明書を確認
   - `ssl_mode` を `prefer` または `disable` に変更

4. **認証エラー**
   - ユーザー名とパスワードを確認
   - PostgreSQLの認証設定を確認

この実装により、安全で効率的なPostgreSQL接続管理が可能になります。次のステップでは、このデータベースマネージャーを使用してMCPツールを実装します。
