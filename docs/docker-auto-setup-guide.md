# Docker自動セットアップガイド

## 概要

PostgreSQL MCP Serverは、ユーザーがMCPサーバーを追加する際に自動的にPostgreSQL Docker環境をセットアップする機能を提供します。これにより、手動でのDocker操作なしでPostgreSQLデータベースを利用できます。

## 機能の特徴

- **自動コンテナ起動**: MCPサーバー起動時にPostgreSQL Dockerコンテナを自動起動
- **データ永続化**: Dockerボリュームによるデータの永続化
- **自動ヘルスチェック**: PostgreSQLの起動完了を自動検出
- **フォールバック対応**: Dockerが利用できない場合は既存のPostgreSQL接続を使用
- **カスタマイズ可能**: ポート、パスワード、データベース名などの設定変更可能

## 使用方法

### 基本的な設定

1. `.env`ファイルを作成し、以下の設定を追加：

```bash
# Docker自動セットアップを有効化
MCP_DOCKER_AUTO_SETUP=true

# PostgreSQL接続設定（Docker自動セットアップ時は自動設定されるため不要）
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
# POSTGRES_DB=postgres
# POSTGRES_USER=postgres
# POSTGRES_PASSWORD=postgres
```

2. MCPサーバーを起動：

```bash
uv run mcp-postgres
```

### カスタマイズ設定

すべての設定オプション：

```bash
# Docker自動セットアップ
MCP_DOCKER_AUTO_SETUP=true

# Dockerイメージ設定
MCP_DOCKER_IMAGE=postgres:16
MCP_DOCKER_CONTAINER_NAME=mcp-postgres-auto

# ポート設定
MCP_DOCKER_PORT=5432

# データ永続化
MCP_DOCKER_DATA_VOLUME=mcp_postgres_data

# データベース認証設定
MCP_DOCKER_PASSWORD=postgres
MCP_DOCKER_DATABASE=postgres
MCP_DOCKER_USERNAME=postgres

# 起動タイムアウト設定
MCP_DOCKER_MAX_WAIT_TIME=30
```

## 動作フロー

1. **設定読み込み**: MCPサーバー起動時にDocker設定を読み込み
2. **Docker可用性チェック**: Dockerデーモンが利用可能か確認
3. **コンテナ起動**: PostgreSQLコンテナを起動（既存の場合は再利用）
4. **ヘルスチェック**: PostgreSQLが接続可能になるまで待機
5. **接続設定**: 自動的にPostgreSQL接続情報を設定
6. **サーバー起動**: MCPサーバーを通常通り起動

## エラーハンドリング

### Dockerが利用できない場合

Docker自動セットアップが有効でもDockerが利用できない場合は、警告を出力して既存のPostgreSQL接続設定を使用します。

```bash
[WARNING] Docker auto-setup enabled but Docker is not available. Using existing PostgreSQL connection.
```

### ポート競合の場合

指定したポートが既に使用されている場合は、コンテナ起動に失敗します。別のポートを指定してください。

### コンテナ起動失敗の場合

コンテナ起動に失敗してもMCPサーバーは起動を続行します。既存のPostgreSQL接続を使用するか、設定を確認してください。

## トラブルシューティング

### コンテナが起動しない場合

1. Dockerが実行中か確認：
   ```bash
   docker ps
   ```

2. ポートが空いているか確認：
   ```bash
   netstat -an | grep 5432
   ```

3. コンテナログを確認：
   ```bash
   docker logs mcp-postgres-auto
   ```

### データ永続化の問題

データボリュームが正しくマウントされているか確認：
```bash
docker volume ls
docker volume inspect mcp_postgres_data
```

### 接続エラーの場合

1. コンテナが実行中か確認：
   ```bash
   docker ps
   ```

2. PostgreSQLがリッスンしているか確認：
   ```bash
   docker exec mcp-postgres-auto pg_isready
   ```

## 手動操作

### コンテナの手動起動/停止

```bash
# コンテナ起動
docker start mcp-postgres-auto

# コンテナ停止
docker stop mcp-postgres-auto

# コンテナ削除
docker rm mcp-postgres-auto

# ボリューム削除
docker volume rm mcp_postgres_data
```

### データベースへの接続

```bash
# コンテナ内でPostgreSQLに接続
docker exec -it mcp-postgres-auto psql -U postgres -d postgres

# ホストから接続
psql -h localhost -p 5432 -U postgres -d postgres
```

## セキュリティ考慮事項

- デフォルトのパスワードを変更することを推奨
- 本番環境では適切なセキュリティ設定を実施
- ファイアウォール設定で不要な外部アクセスを制限

## パフォーマンス最適化

### リソース制限

Dockerコンテナにリソース制限を設定：
```bash
docker update mcp-postgres-auto --memory=1g --cpus=1
```

### データベース設定

`postgresql.conf`をカスタマイズしてパフォーマンスを最適化：
```bash
docker exec mcp-postgres-auto cat /var/lib/postgresql/data/postgresql.conf
```

## 既知の制限

- Windows環境でのDocker Desktopの動作確認が必要
- 複数インスタンス同時実行時のポート競合に注意
- 大規模データセット時のボリュームサイズ管理が必要

## サポート

問題が発生した場合は、以下の情報を収集して報告してください：

1. MCPサーバーのログ
2. Dockerコンテナのログ
3. 環境情報（OS、Dockerバージョン、PostgreSQLバージョン）
4. 設定ファイルの内容
