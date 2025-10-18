# pytest テストドキュメント

このディレクトリには、PostgreSQL MCP Serverプロジェクトのpytestに関する包括的なドキュメントが含まれています。

## ファイル構成

### 📚 主要ドキュメント

- **[pytest_concepts_and_usage.md](pytest_concepts_and_usage.md)** - pytestの包括的なコンセプトと使い方ガイド
  - pytestの基本概念
  - テストの書き方とベストプラクティス
  - Fixture、マーカー、モックの使用方法
  - プロジェクト固有の設定とワークフロー

- **[pytest_example_test.py](pytest_example_test.py)** - 実践的なテスト例
  - 様々なpytest機能の実装例
  - 実際に実行可能なテストコード
  - プロジェクトのテストパターンに基づいた例

- **[uv_build_migration_guide.md](uv_build_migration_guide.md)** - uvビルドシステム移行ガイド
  - hatchlingからuv_buildへの移行詳細
  - `uv run mcp-postgres`が動作する仕組み
  - パッケージ構造とスクリプト登録の技術的詳細

### 📋 補助ドキュメント

- **[run_tests_bat_explanation.md](run_tests_bat_explanation.md)** - テスト実行スクリプトの詳細説明

## クイックスタート

### 基本的なテスト実行

```bash
# すべてのテストを実行
uv run pytest

# ユニットテストのみ実行
uv run pytest test/unit/ -v

# 統合テストを実行（データベース環境が必要）
set RUN_INTEGRATION_TESTS=1
uv run pytest test/integration/ -v
```

### プロジェクトのテストスクリプト使用

```bash
# Windows
test\run_tests.bat unit          # ユニットテスト
test\run_tests.bat integration   # 統合テスト
test\run_tests.bat docker        # Docker環境で実行
test\run_tests.bat all           # 全テスト（デフォルト）

# Linux/macOS
test/run_tests.sh unit
test/run_tests.sh integration
test/run_tests.sh docker
test/run_tests.sh all
```

## 主要なコンセプト

### テストの種類

1. **ユニットテスト** (`test/unit/`)
   - 個々のコンポーネントのテスト
   - 外部依存関係なし
   - 高速なフィードバック

2. **統合テスト** (`test/integration/`)
   - コンポーネント間の連携テスト
   - 実際のデータベース接続
   - `@pytest.mark.integration` マーカー付き

### 重要なFixture

- `test_database_config` - テスト用データベース設定
- `event_loop` - 非同期テスト用イベントループ
- `setup_test_environment` - 自動環境設定

### カスタムマーカー

- `@pytest.mark.integration` - 統合テスト
- `@pytest.mark.unit` - ユニットテスト
- `@pytest.mark.slow` - 時間のかかるテスト

## 学習リソース

1. **公式ドキュメント**: [pytest.org](https://docs.pytest.org/)
2. **実践例**: [pytest_example_test.py](pytest_example_test.py) を参照
3. **詳細ガイド**: [pytest_concepts_and_usage.md](pytest_concepts_and_usage.md) を熟読

## トラブルシューティング

### よくある問題

1. **pytestが見つからない**
   ```bash
   uv run pytest --version  # 開発環境で実行
   ```

2. **統合テストがスキップされる**
   ```bash
   set RUN_INTEGRATION_TESTS=1
   ```

3. **データベース接続エラー**
   - Dockerが起動しているか確認
   - テスト用データベースが利用可能か確認

### デバッグのヒント

```bash
# 詳細な出力で実行
uv run pytest -v

# 最初の失敗で停止
uv run pytest -x

# 特定のテストのみ実行
uv run pytest test/unit/test_config.py::TestPostgresConfig::test_default_values
```

## 貢献ガイドライン

新しいテストを追加する際は：

1. 適切なディレクトリに配置（unit/integration）
2. 適切なマーカーを付与
3. 明確なテスト名とdocstringを記述
4. 必要なfixtureを使用
5. テストが独立していることを確認

---

このドキュメントがpytestの効果的な使用に役立つことを願っています！
