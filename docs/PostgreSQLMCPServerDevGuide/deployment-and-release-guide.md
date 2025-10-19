# デプロイとリリースガイド

このガイドでは、PostgreSQL MCPサーバーのデプロイとリリースプロセスについて説明します。実際のプロジェクトで使用されているGitHub Actionsワークフローを基に、CI/CDパイプラインの構築方法を解説します。

## はじめに

### このガイドの目的
- 自動化されたテストとビルドプロセスの構築
- 安全なリリースプロセスの確立
- 品質保証とセキュリティチェックの実装

### 前提条件
- GitHubリポジトリへのアクセス
- GitHub Actionsの基本的な理解
- PostgreSQLデータベースの基本的な知識

## GitHub ActionsによるCI/CDパイプライン

### 実際のワークフロー構成

このプロジェクトでは以下の2つの主要なワークフローを使用しています：

1. **テストワークフロー** (`.github/workflows/test.yml`)
   - コード品質チェック
   - 自動テスト実行
   - セキュリティスキャン

2. **公開ワークフロー** (`.github/workflows/publish.yml`)
   - パッケージビルド
   - PyPI/TestPyPIへの公開

## テストワークフローの詳細実装

### トリガー条件
```yaml
# .github/workflows/test.yml
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
```

### PostgreSQLサービスコンテナの設定
```yaml
services:
  postgres:
    image: postgres:15
    env:
      POSTGRES_DB: mcp_test_db
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_password
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
    ports:
      - 5432:5432
```

### マトリックステストの実装
```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.14']
```

### UVを使用した依存関係管理
```yaml
- name: Install uv
  run: |
    pip install uv

- name: Install dependencies with uv
  run: |
    uv venv
    uv pip install -e .
    uv pip install -e ".[dev]"
```

### データベース初期化とテスト実行
```yaml
- name: Wait for PostgreSQL
  run: |
    for i in {1..30}; do
      if pg_isready -h localhost -p 5432 -U test_user; then
        echo "PostgreSQL is ready!"
        break
      fi
      echo "Waiting for PostgreSQL... ($i/30)"
      sleep 2
    done
    pg_isready -h localhost -p 5432 -U test_user || echo "PostgreSQL failed to start"

- name: Initialize test database
  run: |
    PGPASSWORD=test_password psql -h localhost -p 5432 -U test_user -d mcp_test_db -f test/docker/init-test-db.sql

- name: Run unit tests
  run: |
    uv run python -m pytest test/unit/ -v --tb=short --cov=src --cov-report=term-missing

- name: Run integration tests
  env:
    POSTGRES_HOST: localhost
    POSTGRES_PORT: 5432
    POSTGRES_DB: mcp_test_db
    POSTGRES_USER: test_user
    POSTGRES_PASSWORD: test_password
    POSTGRES_SSL_MODE: disable
    RUN_INTEGRATION_TESTS: 1
  run: |
    uv run python -m pytest test/integration/ -v --tb=short -m integration
```

## コード品質チェック

### 品質チェックジョブ
```yaml
code-quality:
  name: Code Quality Checks
  runs-on: ubuntu-latest
  needs: test
```

### コードフォーマットチェック
```yaml
- name: Check code formatting with Black
  run: |
    uv run black --check src/ test/
```

### リントチェック
```yaml
- name: Lint with flake8
  run: |
    uv run flake8 src/ test/ --count --select=E9,F63,F7,F82 --show-source --statistics
    uv run flake8 src/ test/ --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics
```

### 型チェック
```yaml
- name: Type check with mypy
  run: |
    uv run mypy src/ --ignore-missing-imports
```

## セキュリティスキャン

### セキュリティチェックジョブ
```yaml
security-scan:
  name: Security Scan
  runs-on: ubuntu-latest
  needs: test
```

### Banditによるセキュリティスキャン
```yaml
- name: Run Bandit security scan
  run: uv run bandit -r src/ -f json -o bandit-report.json

- name: Upload Bandit report
  uses: actions/upload-artifact@v4
  if: always()
  with:
    name: bandit-report
    path: bandit-report.json
    retention-days: 30
```

## 公開ワークフローの詳細実装

### トリガー条件
```yaml
# .github/workflows/publish.yml
on:
  release:
    types: [published]
  workflow_dispatch:  # 手動実行を許可
```

### ビルドジョブ
```yaml
build:
  name: Build Package
  runs-on: ubuntu-latest
  needs: []
```

### パッケージビルド
```yaml
- name: Set up Python
  uses: actions/setup-python@v4
  with:
    python-version: "3.10"

- name: Install build tools
  run: |
    python -m pip install --upgrade pip
    pip install build

- name: Build package
  run: python -m build

- name: Store distribution packages
  uses: actions/upload-artifact@v4
  with:
    name: python-package-distributions
    path: dist/
```

### PyPI公開ジョブ（セキュアな実装）
```yaml
publish:
  name: Publish to PyPI
  runs-on: ubuntu-latest
  needs: build
  environment: release
  permissions:
    id-token: write  # OIDCトークン用の権限
```

### OIDC認証を使用した安全な公開
```yaml
- name: Download distribution packages
  uses: actions/download-artifact@v4
  with:
    name: python-package-distributions
    path: dist/

- name: Publish to PyPI
  uses: pypa/gh-action-pypi-publish@release/v1
  with:
    packages-dir: dist/
```

### TestPyPI公開ジョブ（手動実行時のみ）
```yaml
publish-testpypi:
  name: Publish to TestPyPI
  runs-on: ubuntu-latest
  needs: build
  if: github.event_name == 'workflow_dispatch'  # 手動実行時のみ
```

## ベストプラクティス

### 1. セキュリティ対策
- **OIDC認証の使用**: APIトークンではなくOIDCを使用した安全な認証
- **環境保護**: 本番公開時の環境設定
- **最小権限の原則**: 必要な権限のみを付与

### 2. パフォーマンス最適化
- **キャッシュの活用**: 依存関係のキャッシュ
- **並列実行**: マトリックステストによる並列実行
- **成果物共有**: ビルド成果物の保存と再利用

### 3. 品質保証
- **多段階テスト**: 単体テスト、統合テスト、コード品質チェック
- **セキュリティスキャン**: 定期的なセキュリティ脆弱性チェック
- **カバレッジレポート**: テストカバレッジの可視化

### 4. メンテナンス性
- **明確なコメント**: ワークフローの目的と動作を明確に
- **定期的な更新**: 依存関係とワークフローの定期的な更新
- **エラーハンドリング**: 適切な失敗条件と通知設定

## トラブルシューティング

### よくある問題と解決策

1. **PostgreSQL接続エラー**
   ```bash
   # 接続テスト
   pg_isready -h localhost -p 5432 -U test_user
   
   # データベース初期化の確認
   PGPASSWORD=test_password psql -h localhost -p 5432 -U test_user -d mcp_test_db -c "SELECT 1;"
   ```

2. **依存関係の競合**
   ```bash
   # キャッシュのクリア
   rm -rf .venv/ dist/ build/ *.egg-info/
   
   # 依存関係の再インストール
   uv sync
   ```

3. **テストタイムアウト**
   - テスト環境のリソースを増やす
   - 長時間実行されるテストを分割
   - データベース接続のタイムアウト設定を調整

4. **ビルドエラー**
   ```bash
   # ビルド環境のクリーンアップ
   rm -rf dist/ build/
   
   # 再ビルド
   uv build
   ```

### デバッグ手法

1. **ローカルテスト**
   ```bash
   # ローカルでのワークフロー実行
   act -P ubuntu-latest=catthehacker/ubuntu:act-latest
   ```

2. **ステップバイステップのデバッグ**
   - GitHub Actionsのログを詳細に確認
   - 各ステップの出力をチェック
   - 環境変数の設定を確認

3. **再現環境の構築**
   ```bash
   # ローカルでのPostgreSQLセットアップ
   docker run --name postgres-test -e POSTGRES_DB=mcp_test_db -e POSTGRES_USER=test_user -e POSTGRES_PASSWORD=test_password -p 5432:5432 -d postgres:15
   ```

## 次のステップ

1. **ワークフローのカスタマイズ**: プロジェクトの要件に合わせてワークフローを調整
2. **通知の設定**: Slackやメールでの通知設定
3. **高度な機能の追加**: マトリックスビルド、キャッシュの最適化など
4. **セキュリティの強化**: 追加のセキュリティチェックの実装

このガイドに従って、安全で効率的なデプロイとリリースプロセスを構築してください。

---

*このガイドは実際のプロジェクト実装に基づいて作成されています。詳細な実装例は `.github/workflows/` ディレクトリを参照してください。*

**関連ガイド**: [パッケージ配布ガイド](package-distribution-guide.md) - PyPI/TestPyPIへの公開プロセスについて詳しく説明しています。
