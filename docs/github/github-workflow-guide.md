# GitHub Workflow 完全ガイド

## はじめに

GitHub Workflow（GitHub Actions）は、GitHubリポジトリでソフトウェア開発ワークフローを自動化するための強力なCI/CDプラットフォームです。コードのビルド、テスト、デプロイなどのタスクを自動化できます。

## 基本概念

### 1. ワークフロー (Workflow)
- 自動化されたプロセスを定義する設定ファイル
- リポジトリの `.github/workflows/` ディレクトリにYAML形式で配置
- 1つのリポジトリに複数のワークフローを定義可能

### 2. イベント (Events)
ワークフローをトリガーするアクション：
- **push**: コードのプッシュ時
- **pull_request**: プルリクエスト作成/更新時
- **release**: リリース公開時
- **schedule**: スケジュール実行
- **workflow_dispatch**: 手動実行
- **repository_dispatch**: 外部イベント

### 3. ジョブ (Jobs)
- ワークフロー内の実行単位
- 同じランナー上で順次または並列実行
- 依存関係を定義可能

### 4. ステップ (Steps)
- ジョブ内の個々のタスク
- シェルコマンドまたはアクションの実行

### 5. アクション (Actions)
- 再利用可能なコード単位
- コミュニティ提供またはカスタム作成

## ワークフロー構文

### 基本構造
```yaml
name: Workflow Name

on:
  event_type:
    conditions

jobs:
  job_id:
    name: Job Name
    runs-on: runner
    steps:
      - name: Step Name
        uses: action/name@version
      - name: Step Name
        run: command
```

### トリガー設定例
```yaml
# 複数のイベント
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  release:
    types: [ published ]
  workflow_dispatch:  # 手動実行
```

## このプロジェクトの実装例

### 公開ワークフロー分析 (publish.yml)

#### トリガー条件
```yaml
on:
  release:
    types: [published]  # リリース公開時
  workflow_dispatch:    # 手動実行可能
```

#### ジョブ構成
1. **テストジョブ**
   - PostgreSQLサービスを使用したテスト実行
   - uvを使用した依存関係管理
   - カバレッジレポート生成
   - Codecovへのレポートアップロード

2. **リントジョブ**
   - コード品質チェック
   - flake8, mypy, blackによる静的解析
   - uvを使用した依存関係管理

3. **ビルドジョブ**
   - パッケージビルド
   - 成果物の保存
   - testとlintジョブの完了を待機

4. **公開ジョブ**
   - PyPIへの公開
   - OIDC認証を使用した安全な公開
   - 環境保護の設定

5. **TestPyPI公開ジョブ**
   - 手動実行時のみTestPyPIへの公開
   - テスト環境でのパッケージ検証

#### サービスコンテナの活用
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

#### 実際の実装の特徴
- **uvの活用**: 高速なPythonパッケージ管理
- **OIDC認証**: PyPI公開時の安全な認証
- **条件付き実行**: TestPyPI公開は手動実行時のみ
- **成果物共有**: ビルド成果物の保存と再利用
- **環境保護**: 本番公開時の環境設定

#### 依存関係管理の実装
```yaml
- name: Install uv
  run: |
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "$HOME/.cargo/bin" >> $GITHUB_PATH

- name: Install dependencies
  run: |
    uv sync
```

#### セキュアな公開設定
```yaml
environment: release
permissions:
  id-token: write  # OIDCトークン用の権限
```

## ベストプラクティス

### 1. セキュリティ
- シークレットの適切な管理
- OIDC認証の活用
- 最小権限の原則

### 2. パフォーマンス
- キャッシュの活用
- マトリックスビルドの使用
- 不要なステップの削除

### 3. メンテナンス性
- 再利用可能なワークフローの作成
- 明確なコメント
- 定期的な更新

### 4. エラーハンドリング
- 適切な失敗条件の設定
- 通知の設定
- ログの確認

## 高度な機能

### 1. マトリックスビルド
```yaml
strategy:
  matrix:
    python-version: [3.8, 3.9, 3.10]
    os: [ubuntu-latest, windows-latest]
```

### 2. 条件付き実行
```yaml
if: github.event_name == 'workflow_dispatch'
```

### 3. 成果物の共有
```yaml
- uses: actions/upload-artifact@v4
  with:
    name: package-distributions
    path: dist/
```

### 4. 環境保護
```yaml
environment: 
  name: production
  url: https://example.com
```

## トラブルシューティング

### 一般的な問題
1. **パーミッションエラー**
   - ワークフローファイルの権限設定を確認
   - シークレットの設定を確認

2. **依存関係の問題**
   - キャッシュのクリア
   - 依存関係のバージョン固定

3. **タイムアウト**
   - ステップの分割
   - リソースの増加

### デバッグ手法
- `act` ツールでのローカルテスト
- ステップバイステップのログ確認
- 再現環境の構築

## 参考リソース

- [GitHub Actions 公式ドキュメント](https://docs.github.com/ja/actions)
- [GitHub Marketplace](https://github.com/marketplace?type=actions)
- [Awesome Actions](https://github.com/sdras/awesome-actions)

---

*このドキュメントはプロジェクトの具体的な実装例に基づいて作成されています。*
