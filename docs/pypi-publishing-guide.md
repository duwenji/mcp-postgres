# PyPI公開ガイド

このガイドでは、PostgreSQL MCPサーバをPyPIに公開する手順を説明します。

## 前提条件

- Python 3.10以上
- [uv](https://github.com/astral-sh/uv) パッケージマネージャー
- PyPIアカウント（[https://pypi.org/account/register/](https://pypi.org/account/register/)）
- テストPyPIアカウント（[https://test.pypi.org/account/register/](https://test.pypi.org/account/register/)）

## プロジェクト構造の確認

現在のプロジェクト構造がPyPI公開に適しているか確認します：

```bash
mcp-postgres/
├── src/
│   └── mcp_postgres/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       ├── resources.py
│       └── tools/
│           ├── __init__.py
│           ├── crud_tools.py
│           └── schema_tools.py
├── pyproject.toml
├── README.md
├── README_ja.md
├── LICENSE
└── .gitignore
```

## ステップ1: 設定ファイルの確認と更新

### pyproject.toml の確認

現在の `pyproject.toml` が公開用に適切に設定されているか確認します：

```toml
[project]
name = "mcp-postgres-duwenji"
version = "1.0.0"
description = "MCP server for PostgreSQL database operations"
authors = [
    { name = "mcp-postgres" },
    { name = "duwenji", email = "duwenji@gmail.com" },
]
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "build>=1.3.0",
    "mcp>=1.0.0",
    "psycopg2-binary>=2.9.0",
    "pydantic>=2.0.0",
    "python-dotenv>=1.0.0",
    "twine>=6.2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.0.0",
    "pytest-xdist>=3.0.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "mypy>=1.0.0",
    "freezegun>=1.0.0",
]

[project.scripts]
mcp-postgres = "mcp_postgres.main:main"

[build-system]
requires = ["uv_build >= 0.9.2, <0.10.0"]
build-backend = "uv_build"

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

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["test"]

[tool.uv]

[dependency-groups]
dev = [
    "pytest>=8.4.2",
    "pytest-cov>=7.0.0",
]
```

## ステップ2: 依存関係の確認

必要な依存関係がすべて `pyproject.toml` に含まれているか確認します：

```bash
# 依存関係のテスト
uv sync
uv run python -c "import mcp_postgres.main; print('Import successful')"
```

## ステップ3: テストの実行

公開前にすべてのテストが通ることを確認します：

```bash
# テストの実行
uv run pytest

# または個別のテスト実行
uv run pytest test/unit/
uv run pytest test/integration/
```

## ステップ4: ビルドの準備

### バージョン番号の更新

必要に応じてバージョン番号を更新します：

```toml
# pyproject.toml
version = "1.0.0"  # セマンティックバージョニングに従う
```

### READMEの確認

READMEファイルが完全で、適切な説明を含んでいることを確認します。

## ステップ5: ビルドとテスト公開

### ビルドシステムの理解

このプロジェクトでは以下のビルドツールを使用しています：

1. **uv_build (ビルドバックエンド)**
   - UVパッケージマネージャーのビルドシステム
   - `pyproject.toml` の `[build-system]` セクションで指定
   - ソースコードから配布パッケージ（.tar.gz と .whl）を生成
   - 依存関係の解決とパッケージング

2. **twine (アップロードツール)**
   - ビルドされたパッケージをPyPIにアップロード
   - 認証とセキュリティを管理
   - パッケージの検証と署名

**ワークフロー:**
```
ソースコード → uv_buildでビルド → 配布パッケージ → twineでアップロード → PyPI
```

### 1. ビルドツールのインストール

```bash
# ビルドツールのインストール
pip install build twine
# または uv を使用
uv add build twine
```

### 2. ディストリビューションのビルド

```bash
# ディストリビューションのビルド
python -m build
# または uv を使用
uv run python -m build
```

これにより `dist/` ディレクトリに以下のファイルが生成されます：
- `mcp-postgres-duwenji-1.0.0.tar.gz`
- `mcp_postgres_duwenji-1.0.0-py3-none-any.whl`

### 3. テストPyPIへのアップロード

まずテストPyPIで動作確認します：

```bash
# テストPyPIへのアップロード
uv run python -m twine upload --repository testpypi --verbose dist/*
```

認証情報の入力が求められます：
- ユーザー名: `__token__`
- パスワード: PyPI APIトークン

### 4. テストインストール

テストPyPIからインストールして動作確認：

```bash
# テスト環境でのインストール
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ mcp-postgres-duwenji

# 動作確認
mcp-postgres --help
```

## ステップ6: 本番PyPIへの公開

テストが成功したら本番PyPIへ公開：

```bash
# 本番PyPIへのアップロード
python -m twine upload --verbose dist/*
```

## ステップ7: APIトークンの設定

### PyPI APIトークンの作成

1. [PyPIアカウント](https://pypi.org/manage/account/)にログイン
2. 「API tokens」セクションで新しいトークンを作成
3. スコープを「Entire account」またはプロジェクト限定で設定
4. トークンを安全な場所に保存

### 環境変数でのトークン設定

```bash
# Linux/macOS
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-YourAPITokenHere

# Windows (PowerShell)
$env:TWINE_USERNAME="__token__"
$env:TWINE_PASSWORD="pypi-YourAPITokenHere"
```

## 自動化スクリプト

### 公開スクリプトの作成

`scripts/publish.sh` (Linux/macOS) または `scripts/publish.ps1` (Windows) を作成：

```bash
#!/bin/bash
# scripts/publish.sh

set -e

echo "Building distribution..."
python -m build

echo "Uploading to PyPI..."
python -m twine upload dist/*

echo "Publication complete!"
```

```powershell
# scripts/publish.ps1
param(
    [string]$Version = "patch"
)

Write-Host "Building distribution..."
python -m build

Write-Host "Uploading to PyPI..."
python -m twine upload dist/*

Write-Host "Publication complete!"
```

## GitHub Actionsでの自動公開

### .github/workflows/publish.yml の作成

```yaml
name: Publish Python Package

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: release
    permissions:
      id-token: write

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.10"
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    
    - name: Build package
      run: python -m build
    
    - name: Publish to PyPI
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
        password: ${{ secrets.PYPI_API_TOKEN }}
```

## バージョン管理のベストプラクティス

### セマンティックバージョニング

- **メジャーバージョン**: 後方互換性のない変更
- **マイナーバージョン**: 後方互換性のある新機能
- **パッチバージョン**: 後方互換性のあるバグ修正

### バージョン更新スクリプト

```python
# scripts/update_version.py
import re
import sys

def update_version(new_version):
    with open('pyproject.toml', 'r') as f:
        content = f.read()
    
    # バージョン番号の更新
    content = re.sub(
        r'version = "[^"]+"',
        f'version = "{new_version}"',
        content
    )
    
    with open('pyproject.toml', 'w') as f:
        f.write(content)
    
    print(f"Updated version to {new_version}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python update_version.py <new_version>")
        sys.exit(1)
    
    update_version(sys.argv[1])
```

## トラブルシューティング

### よくある問題

1. **ビルドエラー**
   ```bash
   # キャッシュのクリア
   rm -rf dist/ build/ *.egg-info/
   python -m build
   ```

2. **アップロードエラー**
   - APIトークンが正しいか確認
   - パッケージ名が重複していないか確認
   - ネットワーク接続を確認

3. **依存関係エラー**
   ```bash
   # 依存関係の確認
   uv tree
   pip check
   ```

### デバッグコマンド

```bash
# パッケージ情報の確認
python -m pip show mcp-postgres-duwenji

# インストール後のテスト
python -c "import mcp_postgres_duwenji; print('Import successful')"

# 依存関係の確認
pip list | grep mcp-postgres-duwenji

# UVを使用した依存関係の確認
uv tree
uv pip list
```

## セキュリティ考慮事項

1. **APIトークンの保護**
   - 公開リポジトリにコミットしない
   - 環境変数またはシークレットで管理
   - 定期的にローテーション

2. **コードレビュー**
   - 公開前にコードレビューを実施
   - 依存関係のセキュリティ脆弱性を確認

3. **署名の検討**
   - GPG署名を使用したパッケージ署名
   - ユーザーがパッケージの真正性を確認可能に

## メンテナンス

### 定期的な更新

- 依存関係の定期的な更新
- セキュリティ脆弱性の監視
- ユーザーフィードバックへの対応

### ドキュメントの更新

- READMEの定期的な更新
- 変更履歴の維持
- トラブルシューティングガイドの充実

このガイドに従って、安全かつ効率的にPyPIへの公開を行ってください。
