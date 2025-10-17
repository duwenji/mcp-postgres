# Technical Context: PostgreSQL MCP Server

## 技術スタック

### コア技術
- **プログラミング言語**: Python 3.8+
- **MCPフレームワーク**: 標準MCPプロトコル実装
- **データベース接続**: psycopg2 (PostgreSQLアダプター)
- **非同期処理**: asyncio (必要に応じて)
- **設定管理**: Pydantic + 環境変数

### 主要ライブラリ
- `mcp`: MCPプロトコル実装
- `psycopg2`: PostgreSQLデータベース接続
- `pydantic`: 設定バリデーション
- `python-dotenv`: 環境変数管理

## 開発環境設定

### 前提条件
- Python 3.8以上
- PostgreSQL 12以上
- pip (Pythonパッケージマネージャー)

### 推奨開発ツール
- **エディター**: VS Code with Python拡張機能
- **仮想環境**: venvまたはconda
- **バージョン管理**: Git
- **テストフレームワーク**: pytest

## 技術的制約

### パフォーマンス要件
- 接続プーリングによる効率的なリソース管理
- 非同期処理によるスケーラビリティ
- メモリ使用量の最適化

### セキュリティ要件
- 環境変数による機密情報の管理
- SQLインジェクション対策
- 適切なエラーハンドリングとロギング

### 互換性
- PostgreSQL 12以上との互換性
- Python 3.8+との互換性
- 主要OS（Windows, macOS, Linux）での動作

## 依存関係

### コア依存関係
```python
# requirements.txt の想定内容
mcp>=1.0.0
psycopg2-binary>=2.9.0
pydantic>=2.0.0
python-dotenv>=1.0.0
```

### 開発依存関係
```python
# requirements-dev.txt の想定内容
pytest>=7.0.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.0.0
```

## ツール使用パターン

### MCPツール定義
- **query_execute**: SQLクエリの実行
- **get_tables**: テーブル一覧の取得
- **get_table_schema**: テーブル構造の取得
- **insert_data**: データの挿入
- **update_data**: データの更新
- **delete_data**: データの削除

### リソース定義
- **database_info**: データベース接続情報
- **query_history**: 実行クエリ履歴

## 設定管理

### 環境変数
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

### 設定ファイル構造
```python
# config.py の想定構造
from pydantic import BaseSettings

class PostgresConfig(BaseSettings):
    host: str
    port: int = 5432
    database: str
    username: str
    password: str
    ssl_mode: str = "prefer"
    pool_size: int = 5
    max_overflow: int = 10
```

## 開発ワークフロー

### ローカル開発
1. 仮想環境のセットアップ
2. 依存関係のインストール
3. 環境変数の設定
4. 開発サーバーの起動
5. テストの実行

### テスト戦略
- 単体テスト: 個々の関数・メソッド
- 統合テスト: データベース接続テスト
- E2Eテスト: MCPツールの動作テスト

## デプロイメント

### パッケージング
- PyPIへの公開準備
- Dockerイメージの作成
- 設定テンプレートの提供

### 監視とロギング
- 構造化ロギングの実装
- パフォーマンスメトリクスの収集
- エラートラッキングの設定
