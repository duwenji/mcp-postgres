# System Patterns: PostgreSQL MCP Server

## システムアーキテクチャ

### 全体アーキテクチャ
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AI Assistant  │◄──►│  PostgreSQL MCP  │◄──►│  PostgreSQL     │
│                 │    │     Server       │    │   Database      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### コンポーネント構成
1. **MCPサーバーコア** (実装済み)
   - MCPプロトコルハンドラー (main.py)
   - ツール登録と実行管理 (main.py)
   - リソース管理 (resources.py)

2. **データベース接続層** (実装済み)
   - 接続プール管理 (database.py)
   - クエリ実行エンジン (database.py)
   - トランザクション管理 (database.py)

3. **設定管理層** (実装済み)
   - 環境変数読み込み (config.py)
   - 設定バリデーション (config.py)
   - セキュリティ設定 (config.py)

4. **ツールシステム** (実装済み)
   - CRUDツール (tools/crud_tools.py)
   - スキーマツール (tools/schema_tools.py)
   - テーブル管理ツール (tools/table_tools.py)
   - トランザクションツール (tools/transaction_tools.py)
   - MCP Samplingツール (tools/sampling_tools.py, tools/sampling_integration.py)
   - ツールハンドラー (tools/ディレクトリ)

## 主要技術的決定

### 接続管理パターン
- **接続プーリング**: SQLAlchemyまたは独自実装による効率的な接続管理
- **コンテキストマネージャ**: `with`文による安全な接続管理
- **リトライメカニズム**: 一時的な接続エラーに対する自動リトライ

### エラーハンドリングパターン
```python
# エラーハンドリングの基本パターン
try:
    result = await execute_query(query, params)
except psycopg2.Error as e:
    logger.error(f"Database error: {e}")
    raise MCPError(f"Query execution failed: {str(e)}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise MCPError("Internal server error")
```

### セキュリティパターン
- **パラメータ化クエリ**: SQLインジェクション対策
- **環境変数管理**: 機密情報の安全な保存
- **入力バリデーション**: クエリパラメータの検証

## 設計パターン

### リポジトリパターン
```python
class PostgresRepository:
    def __init__(self, connection_pool):
        self.pool = connection_pool
    
    async def execute_query(self, query: str, params: dict = None) -> List[Dict]:
        # クエリ実行ロジック
        pass
    
    async def get_tables(self) -> List[str]:
        # テーブル一覧取得
        pass
```

### ファクトリパターン
```python
class ConnectionPoolFactory:
    @staticmethod
    def create_pool(config: PostgresConfig) -> ConnectionPool:
        # 接続プールの作成
        pass
```

### ストラテジーパターン
```python
class QueryExecutor:
    def __init__(self, strategy: ExecutionStrategy):
        self.strategy = strategy
    
    async def execute(self, query: str, params: dict = None):
        return await self.strategy.execute(query, params)
```

## 重要な実装パス

### MCPツール登録フロー
1. ツール定義の作成
2. MCPサーバーへの登録
3. リクエストハンドラーの設定
4. エラーハンドリングの実装

### データベース接続フロー
1. 設定の読み込みとバリデーション
2. 接続プールの初期化
3. 接続の取得と解放
4. クエリの実行と結果の処理

### クエリ実行フロー
1. 入力パラメータのバリデーション
2. パラメータ化クエリの構築
3. データベース接続の取得
4. クエリの実行と結果の取得
5. 結果のフォーマットと返却

## コンポーネント関係

### 依存関係図
```
MCP Server Core (main.py)
    │
    ├── Tool Registry (main.py)
    │   ├── CRUD Tools (tools/crud_tools.py)
    │   ├── Schema Tools (tools/schema_tools.py)
    │   ├── Table Tools (tools/table_tools.py)
    │   ├── Transaction Tools (tools/transaction_tools.py)
    │   ├── Sampling Tools (tools/sampling_tools.py)
    │   └── Sampling Integration (tools/sampling_integration.py)
    │
    ├── Connection Manager (database.py)
    │   ├── Pool Factory (database.py)
    │   ├── Connection Pool (database.py)
    │   └── Retry Handler (database.py)
    │
    ├── Configuration Manager (config.py)
    │   ├── Env Loader (config.py)
    │   ├── Validator (config.py)
    │   └── Security Config (config.py)
    │
    └── Resource Manager (resources.py)
        ├── Static Resources (resources.py)
        └── Dynamic Resources (resources.py)
```

### データフロー
1. **ツールリクエスト受信**
2. **パラメータバリデーション**
3. **データベース接続取得**
4. **クエリ実行**
5. **結果フォーマット**
6. **レスポンス返却**

## クリティカルな実装詳細

### 接続プール設定
```python
# 最適なプール設定
MIN_CONNECTIONS = 1
MAX_CONNECTIONS = 20
CONNECTION_TIMEOUT = 30
IDLE_TIMEOUT = 300
```

### クエリタイムアウト
- デフォルトタイムアウト: 30秒
- 設定可能なタイムアウト値
- タイムアウト時の適切なエラーハンドリング

### メモリ管理
- 大きな結果セットのストリーミング処理
- 接続リークの防止
- リソースの適切な解放

## 拡張性の考慮

### プラグインアーキテクチャ
- 新しいツールの簡単な追加
- カスタムクエリプロセッサのサポート
- 監視とロギングの拡張

### 設定の柔軟性
- 環境ごとの設定切り替え
- 動的な設定リロード
- 複数データベース接続のサポート
