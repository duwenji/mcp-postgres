# PostgreSQL MCP サーバー

PostgreSQLデータベース操作のためのModel Context Protocol（MCP）サーバーです。このサーバーはAIアシスタントに標準化されたインターフェースを通じてPostgreSQLデータベースのCRUD操作と管理機能を提供します。

## 機能

- **エンティティCRUD操作**: PostgreSQLテーブルでの作成、読み取り、更新、削除操作
- **動的テーブルサポート**: 事前設定なしでデータベース内の任意のテーブルを操作
- **安全な接続管理**: 環境変数ベースの設定と検証
- **パラメータ化クエリ**: SQLインジェクション攻撃からの保護
- **柔軟なクエリ**: 複雑な条件と結果制限のサポート

## 利用可能なツール

### CRUD操作
- `create_entity`: テーブルに新しい行を挿入
- `read_entity`: オプションの条件付きでテーブルをクエリ
- `update_entity`: 条件に基づいて既存の行を更新
- `delete_entity`: テーブルから行を削除

## クイックスタート

### 前提条件

- Python 3.8以上
- PostgreSQLデータベース（バージョン12以上）
- [uv](https://github.com/astral-sh/uv) パッケージマネージャー（最新版）

### インストール

1. **リポジトリをクローン**:
   ```bash
   git clone https://github.com/duwenji/mcp-postgres.git
   cd mcp-postgres
   ```

2. **uvで依存関係をインストール**:
   ```bash
   uv sync
   ```

3. **データベース接続を設定**:
   ```bash
   cp .env.example .env
   # .envを編集してPostgreSQL接続情報を入力
   ```

4. **MCPクライアントを設定**（例：Claude Desktop）:
   MCPクライアントの設定にサーバー設定を追加します。

### 設定

PostgreSQL接続情報を含む`.env`ファイルを作成:

```bash
# PostgreSQL接続設定
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=your_database
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password

# オプション設定
POSTGRES_SSL_MODE=prefer
POSTGRES_POOL_SIZE=5
POSTGRES_MAX_OVERFLOW=10
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
│   ├── main.py          # MCPサーバーエントリーポイント
│   ├── config.py        # 設定管理
│   ├── database.py      # データベース接続と操作
│   └── tools/
│       ├── __init__.py
│       └── crud_tools.py # CRUD操作ツール
├── pyproject.toml       # プロジェクト設定と依存関係
├── .env.example         # 環境変数テンプレート
└── README.md
```

### サーバーの実行

テスト用にサーバーを直接実行:

```bash
uv run python -m src.main
```

### 新しいツールの追加

1. `src/tools/`に新しいツール定義を作成
2. ツールハンドラー関数を追加
3. `get_crud_tools()`と`get_crud_handlers()`にツールを登録
4. ツールはMCPインターフェースを通じて自動的に利用可能になります

## セキュリティ考慮事項

- 機密接続情報には常に環境変数を使用
- サーバーはSQLインジェクション防止のためパラメータ化クエリを使用
- データベースユーザーの権限を必要な操作のみに制限
- 本番環境ではデータベース接続にSSL/TLSの使用を検討

## ライセンス

Apache 2.0
