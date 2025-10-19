# パッケージ配布ガイド

このガイドでは、PostgreSQL MCPサーバーをPyPIとTestPyPIに公開する手順を説明します。実際のプロジェクトで使用されている公開ワークフローと設定を基に、安全で効率的なパッケージ配布プロセスを解説します。

## はじめに

### このガイドの目的
- PyPIとTestPyPIへの安全なパッケージ公開
- バージョン管理と依存関係の適切な管理
- 自動化された公開プロセスの構築

### 前提条件
- Python 3.10以上
- [uv](https://github.com/astral-sh/uv) パッケージマネージャー
- PyPIアカウント（[https://pypi.org/account/register/](https://pypi.org/account/register/)）
- テストPyPIアカウント（[https://test.pypi.org/account/register/](https://test.pypi.org/account/register/)）

## プロジェクト構造の確認

### 公開に適したプロジェクト構造
```bash
mcp-postgres/
├── src/
│   └── mcp_postgres_duwenji/
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

## 設定ファイルの確認と更新

### pyproject.toml の設定確認

現在のプロジェクトで使用されている実際の設定：

```toml
[project]
name = "mcp-postgres-duwenji"
version = "0.0.1"
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
mcp_postgres_duwenji = "mcp_postgres_duwenji.main:cli_main"

[build-system]
requires = ["uv_build >= 0.9.2, <0.10.0"]
build-backend = "uv_build"
```

### 重要な設定項目

1. **パッケージ名**: `mcp-postgres-duwenji`
2. **バージョン**: セマンティックバージョニングに従う
3. **依存関係**: 実行時と開発時の依存関係を分離
4. **スクリプトエントリーポイント**: `mcp_postgres_duwenji` コマンドの定義
5. **ビルドシステム**: `uv_build` を使用

## ビルドシステムの理解

### 使用するビルドツール

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

## 手動公開プロセス

### ステップ1: 依存関係の確認

```bash
# 依存関係のテスト
uv sync
uv run python -c "import mcp_postgres_duwenji.main; print('Import successful')"
```

### ステップ2: テストの実行

```bash
# すべてのテストの実行
uv run pytest

# または個別のテスト実行
uv run pytest test/unit/
uv run pytest test/integration/
```

### ステップ3: ビルドの準備

#### バージョン番号の更新
必要に応じてバージョン番号を更新します：

```toml
# pyproject.toml
version = "0.0.1"  # セマンティックバージョニングに従う
```

#### READMEの確認
READMEファイルが完全で、適切な説明を含んでいることを確認します。

### ステップ4: ディストリビューションのビルド

```bash
# ディストリビューションのビルド
uv build
```

これにより `dist/` ディレクトリに以下のファイルが生成されます：
- `mcp-postgres-duwenji-1.0.1.tar.gz`
- `mcp_postgres_duwenji-1.0.1-py3-none-any.whl`

### ステップ5: テストPyPIへのアップロード

まずテストPyPIで動作確認します：

```bash
# テストPyPIへのアップロード
uv run python -m twine upload --repository testpypi --verbose dist/*
```

認証情報の入力が求められます：
- ユーザー名: `__token__`
- パスワード: PyPI APIトークン

### ステップ6: テストインストール

テストPyPIからインストールして動作確認：

```bash
# テスト環境でのインストール
uv pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ mcp-postgres-duwenji

# 動作確認
mcp_postgres_duwenji --help
```

### ステップ7: 本番PyPIへの公開

テストが成功したら本番PyPIへ公開：

```bash
# 本番PyPIへのアップロード
uv run python -m twine upload --verbose dist/*
```

## APIトークンの設定

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

## GitHub Actionsでの自動公開

### 事前設定の準備

GitHub Actionsでの自動公開を有効にするには、以下の事前設定が必要です：

#### 1. GitHubリポジトリの設定

**環境の作成**:
1. GitHubリポジトリで「Settings」→「Environments」に移動
2. 「New environment」をクリック
3. 環境名を `release` と入力して作成
4. 「Required reviewers」で承認者を設定（オプション）

**リポジトリの権限設定**:
1. 「Settings」→「Actions」→「General」に移動
2. 「Workflow permissions」で「Read and write permissions」を選択
3. 「Allow GitHub Actions to create and approve pull requests」を有効化

#### 2. PyPI Trusted Publisherの設定

このプロジェクトではOIDC認証を使用しているため、APIトークンではなくTrusted Publisherを設定します：

**PyPI Trusted Publisherの作成**:
1. [PyPIアカウント](https://pypi.org/manage/account/)にログイン
2. 「Your projects」から公開するプロジェクトを選択
3. 「Settings」→「Publishing」→「Add trusted publisher」をクリック
4. 以下の情報を入力：
   - **Owner**: GitHubリポジトリの所有者名（例: `duwenji`）
   - **Repository name**: GitHubリポジトリ名（例: `mcp-postgres`）
   - **Workflow name**: ワークフロー名（例: `publish.yml`）
   - **Environment name**: 環境名（例: `release`）
5. 「Add」をクリックしてTrusted Publisherを追加

**注意**: Trusted Publisherを設定すると、APIトークンは不要になります。GitHub Actionsが自動的にPyPIとの安全な認証を行います。

#### 3. TestPyPI Trusted Publisherの設定（オプション）

TestPyPIへの自動公開を行う場合、TestPyPIでもTrusted Publisherを設定できます：

**TestPyPI Trusted Publisherの作成**:
1. [TestPyPIアカウント](https://test.pypi.org/manage/account/)にログイン
2. 「Your projects」から公開するプロジェクトを選択
3. 「Settings」→「Publishing」→「Add trusted publisher」をクリック
4. 以下の情報を入力：
   - **Owner**: GitHubリポジトリの所有者名（例: `duwenji`）
   - **Repository name**: GitHubリポジトリ名（例: `mcp-postgres`）
   - **Workflow name**: ワークフロー名（例: `publish.yml`）
   - **Environment name**: 環境名（例: `release`）
5. 「Add」をクリックしてTrusted Publisherを追加

**注意**: TestPyPI Trusted Publisherを設定すると、TestPyPIへの自動公開もAPIトークン不要で実行できます。

### 実際の公開ワークフロー

このプロジェクトで使用されている実際の公開ワークフロー（`.github/workflows/publish.yml`）：

```yaml
name: Publish Python Package

on:
  release:
    types: [published]
  workflow_dispatch:  # 手動実行を許可

jobs:
  build:
    name: Build Package
    runs-on: ubuntu-latest
    needs: []
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
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

  publish:
    name: Publish to PyPI
    runs-on: ubuntu-latest
    needs: build
    environment: release
    permissions:
      id-token: write  # OIDCトークン用の権限
    
    steps:
    - name: Download distribution packages
      uses: actions/download-artifact@v4
      with:
        name: python-package-distributions
        path: dist/
    
    - name: Publish to PyPI
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
        packages-dir: dist/

  publish-testpypi:
    name: Publish to TestPyPI
    runs-on: ubuntu-latest
    needs: build
    if: github.event_name == 'workflow_dispatch'  # 手動実行時のみ
    
    steps:
    - name: Download distribution packages
      uses: actions/download-artifact@v4
      with:
        name: python-package-distributions
        path: dist/
    
    - name: Publish to TestPyPI
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
        packages-dir: dist/
        repository-url: https://test.pypi.org/legacy/
```

### ワークフローの特徴

1. **OIDC認証**: APIトークンではなくOIDCを使用した安全な認証
2. **環境保護**: 本番公開時の環境設定
3. **条件付き実行**: TestPyPI公開は手動実行時のみ
4. **成果物共有**: ビルド成果物の保存と再利用

## バージョン管理のベストプラクティス

### セマンティックバージョニング

- **メジャーバージョン**: 後方互換性のない変更
- **マイナーバージョン**: 後方互換性のある新機能
- **パッチバージョン**: 後方互換性のあるバグ修正

### バージョン更新スクリプト

実際のプロジェクトで使用されているバージョン更新スクリプト：

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

使用方法：
```bash
python scripts/update_version.py 1.0.2
```

## トラブルシューティング

### よくある問題

1. **ビルドエラー**
   ```bash
   # キャッシュのクリア
   rm -rf dist/ build/ *.egg-info/
   uv build
   ```

2. **アップロードエラー**
   - APIトークンが正しいか確認
   - パッケージ名が重複していないか確認
   - ネットワーク接続を確認

3. **依存関係エラー**
   ```bash
   # 依存関係の確認
   uv tree
   uv pip check
   ```

### デバッグコマンド

```bash
# パッケージ情報の確認
uv pip show mcp-postgres-duwenji

# インストール後のテスト
uv run python -c "import mcp_postgres_duwenji; print('Import successful')"

# 依存関係の確認
uv pip list | grep mcp-postgres-duwenji

# UVを使用した依存関係の確認
uv tree
uv pip list
```

## セキュリティ考慮事項

### 1. APIトークンの保護
- 公開リポジトリにコミットしない
- 環境変数またはシークレットで管理
- 定期的にローテーション

### 2. コードレビュー
- 公開前にコードレビューを実施
- 依存関係のセキュリティ脆弱性を確認

### 3. OIDC認証の活用
- GitHub ActionsでのOIDC認証を使用
- APIトークンよりも安全な認証方法

### 4. 環境保護
- 本番公開時の環境設定
- 手動承認プロセスの実装

## メンテナンス

### 定期的な更新
- 依存関係の定期的な更新
- セキュリティ脆弱性の監視
- ユーザーフィードバックへの対応

### ドキュメントの更新
- READMEの定期的な更新
- 変更履歴の維持
- トラブルシューティングガイドの充実

## 自動化スクリプト

### 公開スクリプトの作成

`scripts/publish.sh` (Linux/macOS) または `scripts/publish.ps1` (Windows) を作成：

```bash
#!/bin/bash
# scripts/publish.sh

set -e

echo "Building distribution..."
uv build

echo "Uploading to PyPI..."
uv run python -m twine upload dist/*

echo "Publication complete!"
```

```powershell
# scripts/publish.ps1
param(
    [string]$Version = "patch"
)

Write-Host "Building distribution..."
uv build

Write-Host "Uploading to PyPI..."
uv run python -m twine upload dist/*

Write-Host "Publication complete!"
```

## まとめ

このガイドに従って、安全かつ効率的にPyPIへの公開を行ってください。実際のプロジェクト実装を参考に、以下のポイントを重視してください：

1. **セキュリティ**: OIDC認証と環境保護の活用
2. **自動化**: GitHub Actionsを使用した自動公開
3. **品質**: 公開前の十分なテストと検証
4. **メンテナンス**: 定期的な更新とドキュメントの維持

---

*このガイドは実際のプロジェクト実装に基づいて作成されています。詳細な実装例は `.github/workflows/publish.yml` と `pyproject.toml` を参照してください。*

**関連ガイド**: [デプロイとリリースガイド](deployment-and-release-guide.md) - CI/CDパイプラインとテストプロセスについて詳しく説明しています。
