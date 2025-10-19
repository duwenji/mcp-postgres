# PostgreSQL MCP サーバー

PostgreSQLデータベース操作のためのModel Context Protocol（MCP）サーバーです。このサーバーはAIアシスタントに標準化されたインターフェースを通じてPostgreSQLデータベースのCRUD操作と管理機能を提供します。

**プロジェクト状態**: ✅ **完了** - 完全実装、テスト済み、PyPIに公開済み

## 機能

- **エンティティCRUD操作**: PostgreSQLテーブルでの作成、読み取り、更新、削除操作
- **動的テーブルサポート**: 事前設定なしでデータベース内の任意のテーブルを操作
- **安全な接続管理**: 環境変数ベースの設定と検証
- **パラメータ化クエリ**: SQLインジェクション攻撃からの保護
- **柔軟なクエリ**: 複雑な条件と結果制限のサポート
- **テーブル管理**: テーブルの動的な作成、変更、削除
- **スキーマ情報**: 詳細なテーブルスキーマとデータベースメタデータの取得
- **包括的テスト**: 単体テスト、統合テスト、Dockerテスト環境

## 利用可能なツール

### CRUD操作
- `create_entity`: テーブルに新しい行を挿入
- `read_entity`: オプションの条件付きでテーブルをクエリ
- `update_entity`: 条件に基づいて既存の行を更新
- `delete_entity`: テーブルから行を削除

### テーブル管理操作
- `create_table`: 指定されたスキーマで新しいテーブルを作成
- `alter_table`: 既存のテーブル構造を変更
- `drop_table`: データベースからテーブルを削除

### スキーマ操作
- `get_tables`: データベース内の全テーブル一覧を取得
- `get_table_schema`: 特定のテーブルの詳細なスキーマ情報を取得
- `get_database_info`: データベースのメタデータとバージョン情報を取得

## 利用可能なリソース

### データベースリソース
- `database://tables`: データベース内の全テーブル一覧
- `database://info`: データベースのメタデータとバージョン情報
- `database://schema/{table_name}`: 特定のテーブルのスキーマ情報

## クイックスタート

### 前提条件

- Python 3.10以上
- PostgreSQLデータベース（バージョン12以上）
- [uv](https://github.com/astral-sh/uv) パッケージマネージャー（最新版）

### インストール

1. **PyPIからインストール**:
   ```bash
   uvx mcp-postgres-duwenji
   ```

2. **MCPクライアントを設定**（例：Claude Desktop）:
   MCPクライアントの設定にサーバー設定を追加し、`uvx`を使用します：

   **Claude Desktop設定例**:
   ```json
   {
     "mcpServers": {
       "postgres-mcp": {
         "command": "uvx",
         "args": ["mcp-postgres-duwenji"],
         "env": {
           "POSTGRES_HOST": "localhost",
           "POSTGRES_PORT": "5432",
           "POSTGRES_DB": "your_database",
           "POSTGRES_USER": "your_username",
           "POSTGRES_PASSWORD": "your_password",
           "POSTGRES_SSL_MODE": "prefer"
         }
       }
     }
   }
   ```


### 使用例

設定が完了すると、AIアシスタントを通じてMCPツールを使用できます:

**新しいユーザーを作成**:
```json
{
  "table_name": "users",
  "data": {
    "name": "山田太郎",
    "email": "taro@example.com",
    "age": 30
  }
}
```

**条件付きでユーザーを読み取り**:
```json
{
  "table_name": "users",
  "conditions": {
    "age": 30
  },
  "limit": 10
}
```

**ユーザー情報を更新**:
```json
{
  "table_name": "users",
  "conditions": {
    "id": 1
  },
  "updates": {
    "email": "newemail@example.com"
  }
}
```

**ユーザーを削除**:
```json
{
  "table_name": "users",
  "conditions": {
    "id": 1
  }
}
```

## 開発

### プロジェクト構造

```
mcp-postgres/
├── src/
│   └── mcp_postgres_duwenji/     # メインパッケージ
│       ├── __init__.py           # パッケージ初期化
│       ├── main.py               # MCPサーバーエントリーポイント
│       ├── config.py             # 設定管理
│       ├── database.py           # データベース接続と操作
│       ├── resources.py          # リソース管理
│       └── tools/                # MCPツール定義
│           ├── __init__.py
│           ├── crud_tools.py     # CRUD操作ツール
│           ├── schema_tools.py   # スキーマ操作ツール
│           └── table_tools.py    # テーブル管理ツール
├── test/                         # テスト関連
│   ├── unit/                     # ユニットテスト
│   ├── integration/              # 統合テスト
│   ├── docker/                   # Dockerテスト環境
│   └── docs/                     # テストドキュメント
├── docs/                         # プロジェクトドキュメント
│   ├── code-quality-checks-guide.md      # コード品質ツールガイド
│   ├── linting-and-type-checking-guide.md # リンターとタイプチェックガイド
│   ├── pypi-publishing-guide.md          # PyPI公開ガイド
│   └── github/                           # GitHubワークフローとガイド
├── examples/                     # 設定例
├── scripts/                      # ユーティリティスクリプト
├── memory-bank/                  # プロジェクトメモリバンク
├── pyproject.toml                # プロジェクト設定と依存関係
├── uv.lock                       # uv依存関係ロックファイル
├── .env.example                  # 環境変数テンプレート
├── README.md                     # 英語README
└── README_ja.md                  # 日本語README
```

### サーバーの実行

テスト用にサーバーを直接実行:

```bash
uvx mcp-postgres-duwenji
```

### コード品質ツール

このプロジェクトでは包括的なコード品質ツールを使用しています:

- **Black**: コードフォーマット
- **Flake8**: リンターとスタイルチェック
- **MyPy**: 静的型チェック
- **Bandit**: セキュリティスキャン

詳細な使用方法については `docs/code-quality-checks-guide.md` と `docs/linting-and-type-checking-guide.md` を参照してください。

### 新しいツールの追加

1. `src/mcp_postgres_duwenji/tools/`に新しいツール定義を作成
2. ツールハンドラー関数を追加
3. 適切なハンドラー関数にツールを登録
4. ツールはMCPインターフェースを通じて自動的に利用可能になります

## セキュリティ考慮事項

- 機密接続情報には常に環境変数を使用
- サーバーはSQLインジェクション防止のためパラメータ化クエリを使用
- データベースユーザーの権限を必要な操作のみに制限
- 本番環境ではデータベース接続にSSL/TLSの使用を検討

## ライセンス

Apache 2.0
