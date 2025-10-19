# GitHub Actions サービスコンテナ完全ガイド

## はじめに

GitHub Actionsのサービスコンテナ機能を使用すると、ワークフロー内でデータベース、キャッシュ、メッセージキューなどのサービスを実行できます。これにより、アプリケーションの統合テストや依存サービスの動作確認が可能になります。

## 基本概念

### サービスコンテナとは
- ワークフロー内で実行されるDockerコンテナ
- ジョブのステップと並行して実行
- ネットワーク経由で通信可能
- データベース、キャッシュ、メッセージブローカーなどに使用

### 主な用途
- データベース接続のテスト
- 外部サービスとの統合テスト
- 開発環境の再現
- 依存サービスの動作確認

## サービスコンテナの設定

### 基本構文
```yaml
services:
  service_name:
    image: image:tag
    env:
      ENV_VAR: value
    ports:
      - host_port:container_port
    options: >-
      docker_options
```

### このプロジェクトの実装例
```yaml
services:
  postgres:
    image: postgres:15
    env:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: test_db
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
    ports:
      - 5432:5432
```

## サービスコンテナの詳細設定

### 1. イメージ指定
```yaml
services:
  database:
    image: postgres:15          # 公式イメージ
    # image: mysql:8.0          # MySQL
    # image: redis:alpine       # Redis
    # image: mongo:6.0          # MongoDB
```

### 2. 環境変数
```yaml
env:
  POSTGRES_USER: postgres
  POSTGRES_PASSWORD: postgres
  POSTGRES_DB: test_db
  # MySQLの場合
  # MYSQL_ROOT_PASSWORD: password
  # MYSQL_DATABASE: test_db
```

### 3. ポートマッピング
```yaml
ports:
  - 5432:5432    # ホスト:コンテナ
  # - 3306:3306  # MySQL
  # - 6379:6379  # Redis
```

### 4. ヘルスチェック
```yaml
options: >-
  --health-cmd pg_isready
  --health-interval 10s
  --health-timeout 5s
  --health-retries 5
```

## 一般的なサービス設定例

### PostgreSQL
```yaml
services:
  postgres:
    image: postgres:15
    env:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: test_db
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
    ports:
      - 5432:5432
```

### MySQL
```yaml
services:
  mysql:
    image: mysql:8.0
    env:
      MYSQL_ROOT_PASSWORD: password
      MYSQL_DATABASE: test_db
    options: >-
      --health-cmd "mysqladmin ping"
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
    ports:
      - 3306:3306
```

### Redis
```yaml
services:
  redis:
    image: redis:alpine
    options: >-
      --health-cmd "redis-cli ping"
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
    ports:
      - 6379:6379
```

### MongoDB
```yaml
services:
  mongodb:
    image: mongo:6.0
    env:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password
    options: >-
      --health-cmd "mongosh --eval 'db.adminCommand(\"ping\")'"
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
    ports:
      - 27017:27017
```

## ステップでのサービス利用

### 環境変数の設定
```yaml
steps:
  - name: Run tests
    env:
      POSTGRES_HOST: localhost
      POSTGRES_PORT: 5432
      POSTGRES_DB: test_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    run: |
      python -m pytest tests/
```

### 接続確認
```yaml
- name: Wait for PostgreSQL
  run: |
    until pg_isready -h localhost -p 5432; do
      echo "Waiting for PostgreSQL..."
      sleep 2
    done
```

## 高度な設定

### 複数サービスの使用
```yaml
services:
  postgres:
    image: postgres:15
    env:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: test_db
    ports:
      - 5432:5432

  redis:
    image: redis:alpine
    ports:
      - 6379:6379

  # サービス間の依存関係
  app:
    image: your-app:latest
    env:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/test_db
      REDIS_URL: redis://redis:6379
```

### カスタムDockerfileの使用
```yaml
services:
  custom-service:
    image: your-custom-image:latest
    # または
    # build: ./path/to/dockerfile
    ports:
      - 8080:8080
```

### ボリュームマウント
```yaml
services:
  postgres:
    image: postgres:15
    env:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: test_db
    options: >-
      -v /tmp/postgres-data:/var/lib/postgresql/data
    ports:
      - 5432:5432
```

## このプロジェクトの実装分析

### PostgreSQLサービス設定
```yaml
services:
  postgres:
    image: postgres:15                    # PostgreSQL 15を使用
    env:
      POSTGRES_USER: postgres            # ユーザー名
      POSTGRES_PASSWORD: postgres        # パスワード
      POSTGRES_DB: test_db               # データベース名
    options: >-
      --health-cmd pg_isready           # ヘルスチェックコマンド
      --health-interval 10s             # チェック間隔
      --health-timeout 5s               # タイムアウト
      --health-retries 5                # リトライ回数
    ports:
      - 5432:5432                       # ポートマッピング
```

### テストステップでの利用
```yaml
steps:
  - name: Run tests
    env:
      POSTGRES_HOST: localhost          # サービスコンテナのホスト
      POSTGRES_PORT: 5432               # マッピングされたポート
      POSTGRES_DB: test_db              # データベース名
      POSTGRES_USER: postgres           # ユーザー名
      POSTGRES_PASSWORD: postgres       # パスワード
    run: |
      uv run pytest -v --cov=src --cov-report=xml
```

## ベストプラクティス

### 1. ヘルスチェックの実装
- サービスが準備完了になるまで待機
- 適切な間隔とタイムアウトの設定
- サービス固有のヘルスチェックコマンドを使用

### 2. 環境変数の管理
- 機密情報はGitHub Secretsを使用
- 開発環境と一致する設定
- 明確な命名規則

### 3. バージョン固定
- 特定のイメージバージョンの使用
- 互換性の確保
- 再現性の維持

### 4. リソース管理
- 必要最小限のサービスのみ実行
- 適切なポートマッピング
- メモリとCPUの制限

## トラブルシューティング

### 一般的な問題

#### 1. 接続タイムアウト
```yaml
# 解決策: ヘルスチェックの追加
options: >-
  --health-cmd pg_isready
  --health-interval 10s
  --health-timeout 5s
  --health-retries 5
```

#### 2. ポート競合
```yaml
# 解決策: 異なるポートの使用
ports:
  - 5433:5432  # ホストポートを変更
```

#### 3. サービス起動失敗
```bash
# デバッグ: ログの確認
docker logs container_name
```

### デバッグ手法

#### 1. 手動での接続確認
```yaml
- name: Test PostgreSQL connection
  run: |
    psql -h localhost -p 5432 -U postgres -d test_db -c "SELECT 1;"
```

#### 2. ネットワーク確認
```yaml
- name: Check network
  run: |
    ping -c 3 localhost
    netstat -tulpn | grep 5432
```

#### 3. サービスログの確認
```yaml
- name: Check service logs
  run: |
    docker ps -a
    docker logs $(docker ps -q -f name=postgres)
```

## パフォーマンス最適化

### 1. キャッシュの活用
```yaml
- name: Cache Docker layers
  uses: actions/cache@v3
  with:
    path: /tmp/.buildx-cache
    key: ${{ runner.os }}-buildx-${{ github.sha }}
    restore-keys: |
      ${{ runner.os }}-buildx-
```

### 2. イメージの最適化
- 軽量なベースイメージの使用（alpineなど）
- マルチステージビルド
- 不要なパッケージの削除

### 3. 並列実行
```yaml
jobs:
  test-with-postgres:
    services:
      postgres: ...
    steps: ...

  test-with-mysql:
    services:
      mysql: ...
    steps: ...
```

## セキュリティ考慮事項

### 1. 認証情報の保護
- GitHub Secretsの使用
- デフォルトパスワードの変更
- ネットワーク分離

### 2. イメージの信頼性
- 公式イメージの使用
- 特定バージョンの固定
- セキュリティスキャンの実施

### 3. ネットワークセキュリティ
- 必要なポートのみ公開
- 内部ネットワークの使用
- ファイアウォールの設定

## 参考リソース

- [GitHub Docs - About service containers](https://docs.github.com/ja/actions/using-containerized-services/about-service-containers)
- [Docker Hub](https://hub.docker.com/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [MySQL Docker Image](https://hub.docker.com/_/mysql)

---

*このガイドは、実際のプロジェクトで使用されているPostgreSQLサービスコンテナの実装に基づいて作成されています。*
