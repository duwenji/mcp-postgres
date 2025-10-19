# GitHub Workflow Black Formatter 完全ガイド

## はじめに

BlackはPythonコードの自動フォーマッタで、一貫性のあるコードスタイルを強制します。GitHub ActionsでBlackを使用する際の一般的な問題と解決策について説明します。

## 問題の概要

### エラーメッセージ例
```
would reformat /path/to/file.py
Oh no! 💥 💔 💥
10 files would be reformatted, 2 files would be left unchanged.
Error: Process completed with exit code 1.
```

### 原因
- コードがBlackのフォーマットルールに準拠していない
- ワークフローでチェック対象のディレクトリが不足している
- ローカル環境とCI環境でのBlackバージョンの不一致

## このプロジェクトでの問題と解決

### 問題の詳細
ワークフローでは`src/`ディレクトリのみをチェックしていましたが、実際には`test/`ディレクトリもフォーマットが必要でした。

### 修正前
```yaml
- name: Run black check
  run: |
    uv run black --check src/
```

### 修正後
```yaml
- name: Run black check
  run: |
    uv run black --check src/ test/
```

## 解決手順

### ステップ1: 問題の特定
```bash
# ローカルでBlackを実行して問題を確認
uv run black --check src/ test/
```

### ステップ2: 自動フォーマットの実行
```bash
# 問題のあるファイルを自動修正
uv run black src/ test/
```

### ステップ3: ワークフローの修正
- チェック対象ディレクトリを`src/ test/`に変更
- すべてのPythonファイルがチェックされることを確認

### ステップ4: 検証
```bash
# 修正後の確認
uv run black --check src/ test/
```

## Blackの設定

### pyproject.tomlでの設定例
```toml
[tool.black]
target-version = ['py310']
line-length = 88
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
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

### 主要な設定オプション
- **target-version**: 対象Pythonバージョン
- **line-length**: 1行の最大文字数（デフォルト: 88）
- **include**: 対象ファイルの正規表現
- **exclude**: 除外するファイル/ディレクトリ

## ワークフローでのBlack実装

### 完全なlintジョブ例
```yaml
lint:
  name: Lint and Type Check
  runs-on: ubuntu-latest
  steps:
  - name: Checkout code
    uses: actions/checkout@v4
  
  - name: Set up Python
    uses: actions/setup-python@v4
    with:
      python-version: "3.10"
  
  - name: Install uv
    run: |
      curl -LsSf https://astral.sh/uv/install.sh | sh
      echo "$HOME/.cargo/bin" >> $GITHUB_PATH
  
  - name: Install dependencies
    run: |
      uv sync --extra dev
  
  - name: Run flake8
    run: |
      uv run flake8 src/ test/ --count --show-source --statistics
  
  - name: Run mypy
    run: |
      uv run mypy src/
  
  - name: Run black check
    run: |
      uv run black --check src/ test/
```

## トラブルシューティング

### 1. Blackが見つからないエラー
```bash
error: Failed to spawn: `black`
Caused by: program not found
```

**解決策**:
```yaml
- name: Install dependencies
  run: |
    uv sync --extra dev  # dev依存関係をインストール
```

### 2. バージョン不一致
ローカルとCI環境でBlackのバージョンが異なる場合、フォーマット結果が異なることがあります。

**解決策**:
```toml
# pyproject.toml
[project.optional-dependencies]
dev = [
    "black==23.0.0",  # バージョンを固定
]
```

### 3. 特定ファイルの除外
特定のファイルをBlackのチェックから除外する必要がある場合:

```toml
[tool.black]
extend-exclude = '''
/(
  | generated_code.py
  | legacy/
)/
'''
```

### 4. カスタム設定
プロジェクト固有の設定が必要な場合:

```toml
[tool.black]
line-length = 100
target-version = ['py311']
skip-string-normalization = true
```

## ベストプラクティス

### 1. 事前チェック
プルリクエストを作成する前にローカルで実行:
```bash
uv run black --check src/ test/
```

### 2. 自動フォーマット
開発中に定期的に実行:
```bash
uv run black src/ test/
```

### 3. エディタ統合
VS Codeなどのエディタで保存時に自動フォーマットを設定:
```json
{
  "editor.formatOnSave": true,
  "python.formatting.provider": "black"
}
```

### 4. プレコミットフック
pre-commitフックを使用して自動フォーマット:
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.0.0
    hooks:
      - id: black
```

## 高度な使用方法

### 差分のみのフォーマット
```bash
# ステージングされたファイルのみフォーマット
uv run black $(git diff --name-only --cached -- '*.py')
```

### 特定のディレクトリを除外
```bash
# migrationsディレクトリを除外
uv run black --exclude='.*/migrations/.*' src/ test/
```

### バージョン確認
```bash
uv run black --version
```

## このプロジェクトの設定

### 現在のBlack設定
```toml
[tool.black]
target-version = ['py310']
line-length = 88
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
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

### チェック対象
- `src/` - メインソースコード
- `test/` - テストコード

## 参考リソース

- [Black公式ドキュメント](https://black.readthedocs.io/)
- [Black GitHubリポジトリ](https://github.com/psf/black)
- [Python Code Style Guide](https://www.python.org/dev/peps/pep-0008/)

---

*このガイドは、実際のプロジェクトで発生したBlackフォーマッタの問題と解決経験に基づいて作成されています。*
