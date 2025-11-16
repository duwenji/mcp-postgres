# PostgreSQL パフォーマンス監視ガイド

このガイドでは、MCP PostgreSQL Serverで実装されたパフォーマンス監視機能について説明します。

## 概要

MCP PostgreSQL Serverは、実行速度が遅いSQLクエリ（1秒以上）とその実行計画を自動的にログに出力し、定期的なログレビューとユーザーへのアラート通知を行う仕組みを提供します。

## 主な機能

### 1. 遅いクエリの自動検出とロギング

- **log_min_duration_statement**: 1000ms（1秒）以上の実行時間を持つクエリを自動的にログに記録
- **auto_explain**: 遅いクエリの実行計画を詳細にログ出力
- **詳細なログ設定**: タイミング、バッファ使用量、トリガー情報などを含む詳細な実行計画情報

### 2. ログ設定

- **ログディレクトリ**: `/var/lib/postgresql/data/log`
- **ログファイル名**: `postgresql-%Y-%m-%d_%H%M%S.log`
- **ログローテーション**: 1日ごと、または100MBで自動ローテーション

### 3. 拡張機能の自動ロード

- **auto_explain**: 共有プリロードライブラリとして自動的にロード
- **詳細な実行計画分析**: ANALYZE、BUFFERS、TIMING、TRIGGERS、VERBOSE情報を出力

## 設定パラメータ

### 主要な監視設定

```conf
# 遅いクエリの閾値（1秒）
log_min_duration_statement = 1000

# ログ収集の有効化
logging_collector = on
log_directory = '/var/lib/postgresql/data/log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'

# auto_explain拡張機能
shared_preload_libraries = 'auto_explain'
auto_explain.log_min_duration = 1000
auto_explain.log_analyze = on
auto_explain.log_buffers = on
auto_explain.log_timing = on
auto_explain.log_triggers = on
auto_explain.log_verbose = on
```

### 環境変数によるカスタマイズ

以下の環境変数で設定をカスタマイズできます：

```bash
# 遅いクエリの閾値（ミリ秒）
export MCP_SLOW_QUERY_THRESHOLD_MS=2000

# auto_explainの有効/無効
export MCP_ENABLE_AUTO_EXPLAIN=true

# Docker自動セットアップ
export MCP_DOCKER_AUTO_SETUP=true
export MCP_DOCKER_IMAGE=postgres:16
export MCP_DOCKER_PORT=5432
```

## 使用方法

### 1. Docker自動セットアップの有効化

```bash
# 環境変数の設定
export MCP_DOCKER_AUTO_SETUP=true
export MCP_SLOW_QUERY_THRESHOLD_MS=1000
export MCP_ENABLE_AUTO_EXPLAIN=true

# MCPサーバーの起動
npx -y @modelcontextprotocol/server-postgres-duwenji
```

### 2. 既存コンテナへの設定適用

```bash
# 設定適用スクリプトの実行
python scripts/apply_postgresql_conf.py
```

### 3. 手動での設定確認

```bash
# コンテナ内で設定を確認
docker exec mcp-postgres-auto psql -U postgres -c "SHOW log_min_duration_statement;"
docker exec mcp-postgres-auto psql -U postgres -c "SHOW shared_preload_libraries;"
```

## ログの確認方法

### ログファイルの場所

```bash
# コンテナ内のログディレクトリを確認
docker exec mcp-postgres-auto ls -la /var/lib/postgresql/data/log/

# 最新のログファイルを表示
docker exec mcp-postgres-auto tail -f /var/lib/postgresql/data/log/postgresql-*.log
```

### ログ内容の例

```
2024-01-01 12:00:00 UTC [123]: [1-1] user=postgres,db=postgres,app=psql,client=127.0.0.1 LOG:  duration: 1500.123 ms  statement: SELECT * FROM large_table WHERE condition = 'value';
2024-01-01 12:00:00 UTC [123]: [1-1] user=postgres,db=postgres,app=psql,client=127.0.0.1 LOG:  duration: 1500.123 ms  plan:
	Query Text: SELECT * FROM large_table WHERE condition = 'value';
	Seq Scan on large_table  (cost=0.00..12345.67 rows=1 width=100) (actual time=1500.123..1500.123 rows=1 loops=1)
	  Filter: (condition = 'value'::text)
	  Rows Removed by Filter: 999999
	Buffers: shared hit=5000 read=10000
	Planning Time: 10.123 ms
	Execution Time: 1500.123 ms
```

## パフォーマンス監視のベストプラクティス

### 1. 定期的なログレビュー

- 毎日または毎週、遅いクエリのログを確認
- 実行計画を分析し、インデックスの追加やクエリの最適化を検討

### 2. アラート設定

- ログ監視ツール（例: ELK Stack、Grafana）と連携
- 特定のパターンや閾値を超えた場合のアラート通知を設定

### 3. パフォーマンスチューニング

- 頻繁に遅くなるクエリのインデックス作成
- テーブルの統計情報更新
- クエリの書き直しやパラメータ化

## トラブルシューティング

### 設定が適用されない場合

1. コンテナが再起動されているか確認
2. 設定ファイルの権限を確認
3. PostgreSQLの設定リロードを実行

```bash
# 設定のリロード
docker exec mcp-postgres-auto psql -U postgres -c "SELECT pg_reload_conf();"
```

### auto_explainが動作しない場合

1. 共有プリロードライブラリが正しく設定されているか確認
2. PostgreSQLの再起動が必要な場合がある

```bash
# コンテナの再起動
docker restart mcp-postgres-auto
```

## 関連ドキュメント

- [PostgreSQL公式ドキュメント - ロギング](https://www.postgresql.org/docs/current/runtime-config-logging.html)
- [auto_explain拡張機能](https://www.postgresql.org/docs/current/auto-explain.html)
- [Docker自動セットアップガイド](../docs/docker-auto-setup-guide.md)
