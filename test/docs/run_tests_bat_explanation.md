# run_tests.bat 説明書

## 概要
`run_tests.bat` は PostgreSQL MCP Server のテストランナースクリプトです。Windows 環境で各種テストを実行するためのバッチファイルです。

## ファイル構造

### メイン関数
- `:main` - スクリプトのエントリーポイント
- コマンドライン引数に基づいてテストタイプを判別
- デフォルトでは `all` テストを実行

### テストタイプ
スクリプトは以下のテストタイプをサポート：

| テストタイプ | 説明 |
|-------------|------|
| `unit` | ユニットテストのみ実行 |
| `integration` | 統合テストのみ実行 |
| `docker` | Docker環境で全テスト実行 |
| `all` | 全テスト実行（デフォルト） |

## 関数詳細

### `:run_unit_tests`
- **目的**: ユニットテストの実行
- **使用ツール**: `pytest`
- **オプション**:
  - `-v`: 詳細出力
  - `--tb=short`: 短いトレースバック
  - `--cov=src`: カバレッジ計測（srcディレクトリ）
  - `--cov-report=term-missing`: カバレッジレポート表示

### `:run_integration_tests`
- **目的**: 統合テストの実行
- **前提条件**: Docker環境
- **環境変数**: `RUN_INTEGRATION_TESTS=1` を設定
- **マーカー**: `-m integration` で統合テストのみ実行

### `:check_docker`
- **目的**: Docker環境の確認
- **チェック項目**:
  - Dockerのインストール確認
  - Docker Composeのインストール確認
  - PATH設定の確認

### `:run_docker_tests`
- **目的**: Docker環境でのテスト実行
- **手順**:
  1. `test/docker` ディレクトリに移動
  2. `docker-compose.test.yml` でサービス構築・起動
  3. PostgreSQLの起動待機（10秒）
  4. テストコンテナでテスト実行
  5. サービス停止

## 使用方法

### 基本的な使用方法
```cmd
# 全テスト実行（デフォルト）
test\run_tests.bat

# ユニットテストのみ
test\run_tests.bat unit

# 統合テストのみ
test\run_tests.bat integration

# Docker環境で実行
test\run_tests.bat docker
```

### ヘルプ表示
```cmd
test\run_tests.bat --help
test\run_tests.bat -h
```

## 環境要件

### 必須ツール
- **Python**: pytest 実行用
- **Docker**: 統合テスト・Dockerテスト用
- **Docker Compose**: テスト環境構築用

### オプションツール
- **pytest-cov**: コードカバレッジ計測（オプション）

## ディレクトリ構造との連携

```
test/
├── run_tests.bat          # このスクリプト
├── unit/                  # ユニットテスト
├── integration/           # 統合テスト
├── docker/               # Dockerテスト環境
│   ├── docker-compose.test.yml
│   ├── Dockerfile.test
│   └── init-test-db.sql
└── docs/                 # ドキュメント（このファイル）
```

## エラーハンドリング

### 一般的なエラー
- **Docker未インストール**: エラーメッセージ表示後、終了
- **未知のテストタイプ**: 利用可能なタイプを表示
- **テスト失敗**: pytestの終了コードを返す

### 環境変数
- `RUN_INTEGRATION_TESTS`: 統合テスト実行時に設定
- テスト終了後にクリア

## ベストプラクティス

1. **テスト実行前**: Dockerが起動していることを確認
2. **開発時**: `unit` テストで素早いフィードバック
3. **CI/CD**: `all` または `docker` で包括的なテスト
4. **トラブルシューティング**: 各テストタイプを個別に実行

## 関連ファイル

- `test/run_tests.sh`: Linux/macOS用対応スクリプト
- `test/docker/docker-compose.test.yml`: テスト環境設定
- `test/requirements-test.txt`: テスト依存関係

## 注意事項

- Windows環境専用のスクリプトです
- 管理者権限が必要な場合があります（Docker関連）
- ネットワーク接続が必要（Dockerイメージ取得）
