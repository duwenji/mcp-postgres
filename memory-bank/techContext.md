# Technical Context: PostgreSQL MCP Server

## 技術スタック

### コア技術
- **プログラミング言語**: Python 3.10+
- **MCPフレームワーク**: 標準MCPプロトコル実装
- **データベース接続**: psycopg2-binary (PostgreSQLアダプター)
- **非同期処理**: asyncio
- **設定管理**: Pydantic + 環境変数
- **パッケージ管理**: uv

### 主要ライブラリ
- `mcp @ git+https://github.com/duwenji/python-sdk-1936.git@Proposal--Concern-Based-Filtering-%231936`: Concernベースフィルタリング対応MCPプロトコル実装
- `psycopg2-binary>=2.9.0`: PostgreSQLデータベース接続
- `pydantic>=2.0.0`: 設定バリデーション
- `python-dotenv>=1.0.0`: 環境変数管理
- `docker>=6.0.0`: Dockerコンテナ管理
- `build>=1.3.0`: パッケージビルド
- `twine>=6.2.0`: PyPI公開

## 開発環境設定

### 前提条件
- Python 3.10以上
- PostgreSQL 12以上
- [uv](https://github.com/astral-sh/uv) (Pythonパッケージマネージャー)

### 推奨開発ツール
- **エディター**: VS Code with Python拡張機能
- **パッケージマネージャー**: uv
- **仮想環境**: uvによる自動管理
- **バージョン管理**: Git
- **テストフレームワーク**: pytest
- **コードフォーマッター**: black
- **リンター**: flake8
- **型チェッカー**: mypy

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
- Python 3.10+との互換性
- 主要OS（Windows, macOS, Linux）での動作

## 依存関係

### 依存関係管理
- **パッケージマネージャー**: uv
- **設定ファイル**: `pyproject.toml`
- **ビルドシステム**: uv_build（hatchlingから移行）

### コア依存関係
```python
# pyproject.toml の依存関係
mcp>=1.0.0
psycopg2-binary>=2.9.0
pydantic>=2.0.0
python-dotenv>=1.0.0
```

### 開発依存関係
```python
# pyproject.toml の開発依存関係
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
pytest-mock>=3.0.0
pytest-xdist>=3.0.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.0.0
freezegun>=1.0.0
```

## ツール使用パターン

### MCPツール定義
- **CRUD操作**: create_entity, read_entity, update_entity, delete_entity
- **テーブル管理**: create_table, alter_table, drop_table
- **スキーマ情報**: get_tables, get_table_schema, get_database_info
- **MCP Sampling**: request_llm_analysis, generate_normalization_plan, assess_data_quality, optimize_schema_with_llm
- **トランザクション**: トランザクション管理ツール

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
4. 開発サーバーの起動（`uv run mcp-postgres`）
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

---
*最終更新: 2025年12月31日*
