# テストと品質保証ガイド

このガイドでは、PostgreSQL MCPサーバーのテスト戦略と品質保証の実装方法について説明します。

## テスト戦略の基本

### テストピラミッド

```
      /\
     /  \    E2Eテスト (少数)
    /____\
   /      \  統合テスト (中程度)
  /________\
 /          \ 単体テスト (多数)
/____________\
```

### テストの種類

1. **単体テスト**: 個々の関数・メソッドのテスト
2. **統合テスト**: コンポーネント間の連携テスト
3. **E2Eテスト**: システム全体の動作テスト
4. **パフォーマンステスト**: 性能要件の検証
5. **セキュリティテスト**: セキュリティ要件の検証

## テスト環境の構築

### 1. テスト依存関係の設定

```toml
# pyproject.toml の開発依存関係
[project.optional-dependencies]
dev = [
    "pytest>=8.4.2",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=7.0.0",
    "pytest-mock>=3.14.0",
    "pytest-xdist>=3.6.1",
    "black>=24.10.0",
    "flake8>=7.1.1",
    "mypy>=1.13.0",
    "freezegun>=1.5.0",
    "docker>=7.1.0",  # Dockerベースのテスト用
]
```

**依存関係のインストール**:
```bash
# 開発依存関係のインストール
uv add --group dev pytest pytest-asyncio pytest-cov pytest-mock pytest-xdist black flake8 mypy freezegun docker

# または pyproject.toml に追加後
uv sync
```

### 2. テストディレクトリ構造

```
test/
├── conftest.py           # テスト設定
├── unit/                 # 単体テスト
│   ├── test_config.py
│   ├── test_database.py
│   └── test_tools.py
├── integration/          # 統合テスト
│   ├── test_database_integration.py
│   └── test_mcp_server.py
├── docker/               # Dockerテスト環境
│   ├── docker-compose.test.yml
│   ├── Dockerfile.test
│   └── init-test-db.sql
└── fixtures/             # テストデータ
    └── test_data.sql
```

## 単体テストの実装

### 1. 設定クラスのテスト

```python
# test/unit/test_config.py
import pytest
import os
from unittest.mock import patch
from src.mcp_postgres_duwenji.config import PostgresConfig, load_config

class TestPostgresConfig:
    """PostgresConfigクラスのテスト"""
    
    def test_default_values(self):
        """デフォルト値のテスト"""
        with patch.dict(os.environ, {
            'POSTGRES_HOST': 'localhost',
            'POSTGRES_DB': 'testdb',
            'POSTGRES_USER': 'testuser',
            'POSTGRES_PASSWORD': 'testpass'
        }):
            config = PostgresConfig()
            
            assert config.host == 'localhost'
            assert config.port == 5432  # デフォルト値
            assert config.database == 'testdb'
            assert config.username == 'testuser'
            assert config.password == 'testpass'
            assert config.pool_size == 5  # デフォルト値
            assert config.ssl_mode == 'prefer'  # デフォルト値
    
    def test_ssl_mode_validation(self):
        """SSLモードのバリデーションテスト"""
        with patch.dict(os.environ, {
            'POSTGRES_HOST': 'localhost',
            'POSTGRES_DB': 'testdb',
            'POSTGRES_USER': 'testuser',
            'POSTGRES_PASSWORD': 'testpass',
            'POSTGRES_SSL_MODE': 'invalid_mode'
        }):
            with pytest.raises(ValueError, match="SSLモードは"):
                PostgresConfig()
    
    def test_pool_size_validation(self):
        """プールサイズのバリデーションテスト"""
        with patch.dict(os.environ, {
            'POSTGRES_HOST': 'localhost',
            'POSTGRES_DB': 'testdb',
            'POSTGRES_USER': 'testuser',
            'POSTGRES_PASSWORD': 'testpass',
            'POSTGRES_POOL_SIZE': '0'
        }):
            with pytest.raises(ValueError, match="プールサイズは1以上"):
                PostgresConfig()
    
    def test_load_config_success(self):
        """設定読み込みの成功テスト"""
        with patch.dict(os.environ, {
            'POSTGRES_HOST': 'localhost',
            'POSTGRES_DB': 'testdb',
            'POSTGRES_USER': 'testuser',
            'POSTGRES_PASSWORD': 'testpass'
        }):
            config = load_config()
            assert isinstance(config, PostgresConfig)
            assert config.host == 'localhost'
```

### 2. データベースマネージャーのテスト

```python
# test/unit/test_database.py
import pytest
from unittest.mock import Mock, patch, MagicMock
import psycopg2
from src.mcp_postgres_duwenji.database import (
    DatabaseManager, DatabaseError, ConnectionError, QueryError
)
from src.mcp_postgres_duwenji.config import PostgresConfig

class TestDatabaseManager:
    """DatabaseManagerクラスのテスト"""
    
    @pytest.fixture
    def mock_config(self):
        """モック設定の作成"""
        return PostgresConfig(
            host='localhost',
            port=5432,
            database='testdb',
            username='testuser',
            password='testpass',
            pool_size=2
        )
    
    @pytest.fixture
    def mock_connection_pool(self):
        """モック接続プールの作成"""
        mock_pool = Mock()
        mock_connection = Mock()
        mock_cursor = Mock()
        
        # モックの設定
        mock_pool.getconn.return_value = mock_connection
        mock_pool.putconn.return_value = None
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.description = [('id',), ('name',)]
        mock_cursor.fetchall.return_value = [(1, 'test')]
        
        return mock_pool
    
    def test_initialization_success(self, mock_config, mock_connection_pool):
        """初期化の成功テスト"""
        with patch('psycopg2.pool.SimpleConnectionPool') as mock_pool_class:
            mock_pool_class.return_value = mock_connection_pool
            
            db_manager = DatabaseManager(mock_config)
            db_manager.initialize()
            
            assert db_manager._is_initialized == True
            mock_pool_class.assert_called_once()
    
    def test_initialization_failure(self, mock_config):
        """初期化の失敗テスト"""
        with patch('psycopg2.pool.SimpleConnectionPool') as mock_pool_class:
            mock_pool_class.side_effect = psycopg2.OperationalError("Connection failed")
            
            db_manager = DatabaseManager(mock_config)
            
            with pytest.raises(ConnectionError, match="データベース接続に失敗しました"):
                db_manager.initialize()
    
    def test_execute_query_success(self, mock_config, mock_connection_pool):
        """クエリ実行の成功テスト"""
        with patch('psycopg2.pool.SimpleConnectionPool') as mock_pool_class:
            mock_pool_class.return_value = mock_connection_pool
            
            db_manager = DatabaseManager(mock_config)
            db_manager.connection_pool = mock_connection_pool
            db_manager._is_initialized = True
            
            result = db_manager.execute_query("SELECT * FROM test")
            
            assert len(result) == 1
            assert result[0]['id'] == 1
            assert result[0]['name'] == 'test'
    
    def test_execute_query_empty(self, mock_config, mock_connection_pool):
        """空クエリのテスト"""
        db_manager = DatabaseManager(mock_config)
        db_manager.connection_pool = mock_connection_pool
        db_manager._is_initialized = True
        
        with pytest.raises(QueryError, match="クエリが空です"):
            db_manager.execute_query("")
    
    def test_execute_query_error(self, mock_config, mock_connection_pool):
        """クエリ実行エラーのテスト"""
        mock_connection_pool.getconn.return_value.cursor.side_effect = (
            psycopg2.Error("Query failed")
        )
        
        db_manager = DatabaseManager(mock_config)
        db_manager.connection_pool = mock_connection_pool
        db_manager._is_initialized = True
        
        with pytest.raises(QueryError, match="クエリ実行に失敗しました"):
            db_manager.execute_query("SELECT * FROM test")
    
    def test_get_connection_context_manager(self, mock_config, mock_connection_pool):
        """接続コンテキストマネージャのテスト"""
        db_manager = DatabaseManager(mock_config)
        db_manager.connection_pool = mock_connection_pool
        db_manager._is_initialized = True
        
        with db_manager.get_connection() as connection:
            assert connection is not None
        
        # 接続が確実に返却されたことを確認
        mock_connection_pool.putconn.assert_called_once()
```

### 3. ツールクラスのテスト

```python
# test/unit/test_tools.py
import pytest
from unittest.mock import Mock, patch
from src.mcp_postgres_duwenji.tools.crud_tools import (
    register_crud_tools, _validate_query_safety, _validate_table_name
)

class TestCrudTools:
    """CRUDツールのテスト"""
    
    def test_validate_query_safety_safe(self):
        """安全なクエリの検証テスト"""
        # 安全なクエリ
        safe_queries = [
            "SELECT * FROM users",
            "INSERT INTO users (name) VALUES ('test')",
            "UPDATE users SET name = 'test' WHERE id = 1",
            "DELETE FROM users WHERE id = 1"
        ]
        
        for query in safe_queries:
            # 例外が発生しないことを確認
            _validate_query_safety(query)
    
    def test_validate_query_safety_dangerous(self):
        """危険なクエリの検証テスト"""
        dangerous_queries = [
            "DROP TABLE users",
            "TRUNCATE TABLE users",
            "ALTER TABLE users ADD COLUMN test TEXT",
            "CREATE TABLE test (id SERIAL)"
        ]
        
        for query in dangerous_queries:
            with pytest.raises(ValueError, match="危険な操作"):
                _validate_query_safety(query)
    
    def test_validate_table_name_valid(self):
        """有効なテーブル名の検証テスト"""
        valid_names = ["users", "user_profiles", "table_1"]
        
        for name in valid_names:
            _validate_table_name(name)
    
    def test_validate_table_name_invalid(self):
        """無効なテーブル名の検証テスト"""
        invalid_names = ["", "  ", "users;", "users--", "users/*", "users*/"]
        
        for name in invalid_names:
            with pytest.raises(ValueError):
                _validate_table_name(name)
    
    @patch('src.mcp_postgres_duwenji.tools.crud_tools.DatabaseManagerSingleton')
    def test_register_crud_tools(self, mock_db_singleton):
        """ツール登録のテスト"""
        mock_server = Mock()
        
        register_crud_tools(mock_server)
        
        # ツール登録関数が呼び出されたことを確認
        assert mock_server.list_tools.called
        assert mock_server.call_tool.called
```

## 統合テストの実装

### 1. データベース統合テスト

```python
# test/integration/test_database_integration.py
import pytest
import asyncio
from src.mcp_postgres_duwenji.database import DatabaseManager
from src.mcp_postgres_duwenji.config import PostgresConfig

@pytest.mark.integration
class TestDatabaseIntegration:
    """データベース統合テスト"""
    
    @pytest.fixture(scope="class")
    def test_config(self):
        """テスト用設定"""
        return PostgresConfig(
            host='localhost',
            port=5433,  # テスト用ポート
            database='test_db',
            username='test_user',
            password='test_password',
            pool_size=2
        )
    
    @pytest.fixture(scope="class")
    def db_manager(self, test_config):
        """データベースマネージャーの作成"""
        manager = DatabaseManager(test_config)
        manager.initialize()
        yield manager
        manager.close()
    
    def test_connection_establishment(self, db_manager):
        """接続確立のテスト"""
        # 接続テストクエリ
        result = db_manager.execute_query("SELECT 1 as test_value")
        
        assert len(result) == 1
        assert result[0]['test_value'] == 1
    
    def test_query_execution(self, db_manager):
        """クエリ実行のテスト"""
        # テストテーブルの作成（存在する場合）
        try:
            db_manager.execute_query("""
                CREATE TABLE IF NOT EXISTS test_integration (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
        except Exception:
            pass  # テーブルが既に存在する場合
        
        # データ挿入テスト
        insert_result = db_manager.execute_query("""
            INSERT INTO test_integration (name) VALUES (%s) RETURNING id
        """, {"name": "integration_test"})
        
        assert len(insert_result) == 1
        assert 'id' in insert_result[0]
        
        # データ取得テスト
        select_result = db_manager.execute_query("""
            SELECT * FROM test_integration WHERE name = %s
        """, {"name": "integration_test"})
        
        assert len(select_result) >= 1
        assert select_result[0]['name'] == 'integration_test'
    
    def test_transaction_execution(self, db_manager):
        """トランザクション実行のテスト"""
        queries = [
            {
                'query': "INSERT INTO test_integration (name) VALUES (%s)",
                'params': {"name": "transaction_test_1"}
            },
            {
                'query': "INSERT INTO test_integration (name) VALUES (%s)", 
                'params': {"name": "transaction_test_2"}
            }
        ]
        
        results = db_manager.execute_transaction(queries)
        
        assert len(results) == 2
        assert all('rows_affected' in result for result in results)
```

### 2. MCPサーバー統合テスト

```python
# test/integration/test_mcp_server.py
import pytest
import asyncio
from unittest.mock import Mock, patch
from src.mcp_postgres_duwenji.main import main
from src.mcp_postgres_duwenji.tools.crud_tools import register_crud_tools

@pytest.mark.integration
@pytest.mark.asyncio
class TestMCPServerIntegration:
    """MCPサーバー統合テスト"""
    
    @pytest.fixture
    def mock_server(self):
        """モックサーバーの作成"""
        return Mock()
    
    @pytest.fixture
    def mock_db_manager(self):
        """モックデータベースマネージャーの作成"""
        mock_manager = Mock()
        mock_manager.execute_query.return_value = [{'id': 1, 'name': 'test'}]
        return mock_manager
    
    async def test_tool_registration(self, mock_server, mock_db_manager):
        """ツール登録の統合テスト"""
        with patch('src.mcp_postgres_duwenji.tools.crud_tools.DatabaseManagerSingleton.get_instance', 
                  return_value=mock_db_manager):
            
            register_crud_tools(mock_server)
            
            # ツール一覧関数が登録されたことを確認
            assert mock_server.list_tools.called
            
            # ツール呼び出し関数が登録されたことを確認
            assert mock_server.call_tool.called
    
    async def test_query_execution_tool(self, mock_server, mock_db_manager):
        """クエリ実行ツールの統合テスト"""
        with patch('src.mcp_postgres_duwenji.tools.crud_tools.DatabaseManagerSingleton.get_instance', 
                  return_value=mock_db_manager):
            
            register_crud_tools(mock_server)
            
            # ツール呼び出しのシミュレーション
            tool_handler = mock_server.call_tool.call_args[0][0]
            arguments = {
                "query": "SELECT * FROM test",
                "parameters": {}
            }
            
            result = await tool_handler("query_execute", arguments)
            
            assert len(result) == 1
            assert result[0]['type'] == 'text'
            assert 'クエリ結果' in result[0]['text']
            
            # データベースクエリが呼び出されたことを確認
            mock_db_manager.execute_query.assert_called_once()
```

## テスト実行方法

### 1. テストの実行

```bash
# すべてのテストを実行
uv run pytest

# 単体テストのみ実行
uv run pytest test/unit/

# 統合テストのみ実行
uv run pytest test/integration/

# カバレッジレポート付きで実行
uv run pytest --cov=src --cov-report=html

# 並列実行
uv run pytest -n auto
```

### 2. コード品質チェック

```bash
# コードフォーマット
uv run black src/ test/

# リンター実行
uv run flake8 src/ test/

# 型チェック
uv run mypy src/
```

## Dockerテスト環境

### 1. Docker Compose設定

```yaml
# test/docker/docker-compose.test.yml
version: '3.8'

services:
  postgres-test:
    build:
      context: .
      dockerfile: Dockerfile.test
    environment:
      POSTGRES_DB: test_db
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_password
    ports:
      - "5433:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test_user -d test_db"]
      interval: 5s
      timeout: 5s
      retries: 5
    volumes:
      - postgres_test_data:/var/lib/postgresql/data
      - ./init-test-db.sql:/docker-entrypoint-initdb.d/init-test
