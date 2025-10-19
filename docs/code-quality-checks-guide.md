# コード品質チェック完全ガイド

## はじめに

このガイドでは、PostgreSQL MCP Serverプロジェクトで使用されているコード品質チェックツールの使用方法について詳しく説明します。プロジェクトの品質を維持するために、以下のツールが統合されています。

## 利用可能なコード品質ツール

### 1. コードフォーマッター - Black
- **目的**: 一貫性のあるコードフォーマット
- **設定ファイル**: `pyproject.toml` の `[tool.black]` セクション

### 2. リンター - Flake8
- **目的**: コードスタイルと潜在的な問題の検出
- **設定ファイル**: `.flake8`

### 3. タイプチェッカー - MyPy
- **目的**: 型注釈の検証と型安全性の確保
- **設定ファイル**: `pyproject.toml` の `[tool.mypy]` セクション

### 4. セキュリティスキャナー - Bandit
- **目的**: セキュリティ脆弱性の検出
- **設定ファイル**: `.bandit.yml`（オプション）

## ローカル環境での実行方法

### すべての品質チェックを一度に実行

```bash
# すべての品質チェックを実行
uv run black src/ test/
uv run flake8 src/ test/
uv run mypy src/
uv run bandit -r src/
```

### 個別の品質チェック実行

#### Black（コードフォーマット）
```bash
# コードのフォーマット
uv run black src/ test/

# フォーマットの確認（変更なし）
uv run black --check src/ test/

# 特定のファイルのみフォーマット
uv run black src/mcp_postgres_duwenji/main.py
```

#### Flake8（リンター）
```bash
# 基本的なリンター実行
uv run flake8 src/ test/

# 特定のエラーのみ表示
uv run flake8 --select E,W src/

# 統計情報の表示
uv run flake8 --statistics src/
```

#### MyPy（タイプチェック）
```bash
# 基本的なタイプチェック
uv run mypy src/

# 厳格なモード
uv run mypy --strict src/

# 特定のモジュールのみチェック
uv run mypy src/mcp_postgres_duwenji/config.py
```

#### Bandit（セキュリティスキャン）
```bash
# 基本的なセキュリティスキャン
uv run bandit -r src/

# JSON形式で出力
uv run bandit -r src/ -f json -o bandit-report.json

# 特定のテストを除外
uv run bandit -r src/ --skip B101,B102
```

## 設定ファイルの詳細

### Black設定 (`pyproject.toml`)
```toml
[tool.black]
line-length = 88
target-version = ['py310']
include = '\.pyi?$'
extend-exclude = '''
/(
  # 除外ディレクトリ
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''
```

### Flake8設定 (`.flake8`)
```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = 
    .git,
    __pycache__,
    build,
    dist,
    .venv,
    .eggs,
    *.egg-info
per-file-ignores =
    __init__.py: F401
```

### MyPy設定 (`pyproject.toml`)
```toml
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[[tool.mypy.overrides]]
module = [
    "tests.*",
    "test.*"
]
ignore_missing_imports = true
```

## GitHub Actionsでの自動実行

### 完全な品質チェックワークフロー

```yaml
name: Code Quality Checks

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  code-quality:
    name: Code Quality Checks
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Install uv
      run: pip install uv

    - name: Install dependencies
      run: uv sync --group dev

    - name: Run Black formatter
      run: uv run black --check src/ test/

    - name: Run Flake8 linter
      run: uv run flake8 src/ test/

    - name: Run MyPy type checker
      run: uv run mypy src/

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

## トラブルシューティング

### よくある問題と解決策

#### 1. Blackフォーマットエラー
**問題**: コードがBlackのフォーマットに準拠していない

**解決策**:
```bash
# 自動フォーマット
uv run black src/ test/

# フォーマット後の確認
uv run black --check src/ test/
```

#### 2. Flake8警告の抑制
**問題**: 特定の警告を抑制したい

**解決策**:
```python
# コード内での抑制
import os  # noqa: F401

# または設定ファイルで除外
# .flake8
extend-ignore = E203, W503, F401
```

#### 3. MyPy型エラー
**問題**: 型注釈のエラー

**解決策**:
```python
# 明示的な型注釈の追加
def get_user(user_id: int) -> Optional[User]:
    # 関数の実装
    pass

# 型の無視（必要な場合のみ）
result: Any = some_function()  # type: ignore
```

#### 4. Bandit偽陽性
**問題**: 誤検出のセキュリティ警告

**解決策**:
```bash
# 特定のテストを除外
uv run bandit -r src/ --skip B101,B601

# またはコード内で抑制
# nosecコメントを使用
password = "hardcoded"  # nosec
```

## ベストプラクティス

### 1. 開発ワークフローの統合
- コミット前フックの設定
- IDE統合（VS Code拡張機能など）
- 継続的インテグレーション

### 2. チームでの一貫性
- 共有の設定ファイル
- コードレビューでの品質チェック
- 定期的なツールの更新

### 3. 段階的な導入
- 新しいプロジェクトでは厳格な設定から開始
- 既存プロジェクトでは段階的に厳格化
- チームの合意形成

### 4. パフォーマンス最適化
- キャッシュの活用（MyPyキャッシュなど）
- 増分チェックの使用
- 並列実行の検討

## 参考リソース

- [Black公式ドキュメント](https://black.readthedocs.io/)
- [Flake8公式ドキュメント](https://flake8.pycqa.org/)
- [MyPy公式ドキュメント](https://mypy.readthedocs.io/)
- [Bandit公式ドキュメント](https://bandit.readthedocs.io/)
- [Pythonコードスタイルガイド（PEP 8）](https://www.python.org/dev/peps/pep-0008/)

---

*このガイドは実際のプロジェクト実装とベストプラクティスに基づいて作成されています。*
