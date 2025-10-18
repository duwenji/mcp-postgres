# uvビルドシステム移行ガイド

## 概要

このドキュメントは、PostgreSQL MCP Serverプロジェクトのビルドシステムをhatchlingからuv_buildに移行した際の仕組みと変更内容を説明します。

## 変更内容

### 1. ビルドシステムの更新

**変更前:**
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**変更後:**
```toml
[build-system]
requires = ["uv_build >= 0.9.2, <0.10.0"]
build-backend = "uv_build"
```

### 2. パッケージ構造の変更

**変更前の構造:**
```
src/
├── main.py
├── config.py
├── database.py
├── resources.py
└── tools/
    ├── __init__.py
    ├── crud_tools.py
    └── schema_tools.py
```

**変更後の構造:**
```
src/
└── mcp_postgres/
    ├── __init__.py
    ├── main.py
    ├── config.py
    ├── database.py
    ├── resources.py
    └── tools/
        ├── __init__.py
        ├── crud_tools.py
        └── schema_tools.py
```

### 3. スクリプトエントリーポイントの更新

**変更前:**
```toml
[project.scripts]
mcp-postgres = "src.main:main"
```

**変更後:**
```toml
[project.scripts]
mcp-postgres = "mcp_postgres.main:main"
```

## 仕組みの詳細

### なぜ `uv run mcp-postgres` が動作するようになったか

#### 1. パッケージ化の仕組み

**ビルドプロセス:**
```bash
uv build
# ↓ 以下のファイルが生成される
# dist/mcp_postgres-0.1.0-py3-none-any.whl
# dist/mcp_postgres-0.1.0.tar.gz
```

**インストールプロセス:**
```bash
uv pip install dist/mcp_postgres-0.1.0-py3-none-any.whl
# ↓ 以下の処理が行われる
# 1. パッケージの依存関係解決
# 2. パッケージファイルの展開
# 3. スクリプトエントリーポイントの登録
```

#### 2. スクリプト登録の仕組み

`pyproject.toml`の`[project.scripts]`セクションにより：

```toml
[project.scripts]
mcp-postgres = "mcp_postgres.main:main"
```

この設定により、パッケージインストール時に以下の処理が行われます：

1. **スクリプトファイルの生成**: `mcp-postgres`という実行可能ファイルが生成される
2. **PATHへの登録**: Pythonのスクリプトディレクトリに配置される
3. **エントリーポイントの設定**: `mcp_postgres.main`モジュールの`main`関数を実行するように設定

#### 3. uv run の動作

`uv run`コマンドは以下のように動作します：

```bash
uv run mcp-postgres
# ↓ 内部的には
# 1. 現在のuv環境でインストールされたパッケージを検索
# 2. 登録されたスクリプト`mcp-postgres`を実行
# 3. スクリプトは`mcp_postgres.main:main`を呼び出す
```

### パッケージ構造の重要性

#### 従来の方法の問題点

```bash
# 以前の実行方法
uv run python -m src.main
```

この方法の問題点：
- 開発環境に依存（`src`ディレクトリが存在する必要がある）
- パッケージとしてインストールされていない
- 本番環境での使用が困難

#### 新しい方法の利点

```bash
# 新しい実行方法
uv run mcp-postgres
```

利点：
- **標準化**: Pythonパッケージの標準的な実行方法
- **環境非依存**: どこにインストールされても同じ方法で実行可能
- **本番対応**: 本番環境での使用が容易
- **統合**: uvエコシステムとの完全な統合

## 技術的な詳細

### uv_buildの特徴

1. **高速ビルド**: uvの高速な依存関係解決を活用
2. **統合環境**: パッケージ管理とビルドシステムの統一
3. **シンプルな設定**: hatchlingよりも簡素な設定
4. **キャッシュ機能**: ビルド結果の効率的なキャッシュ

### パッケージ命名規則

- **パッケージ名**: `mcp-postgres`（ハイフン使用）
- **モジュール名**: `mcp_postgres`（アンダースコア使用）
- **スクリプト名**: `mcp-postgres`（ハイフン使用）

この命名規則はPythonの慣習に従っています。

## 移行の影響

### 開発ワークフローの変更

**変更前:**
```bash
# 開発中の実行
uv run python -m src.main

# テスト実行
uv run pytest
```

**変更後:**
```bash
# 開発中の実行
uv run mcp-postgres

# テスト実行（変更なし）
uv run pytest
```

### ドキュメントの更新

README.mdの実行方法を更新：
```markdown
### Running the Server

To run the server directly for testing:

```bash
uv run mcp-postgres
```
```

## 検証方法

### ビルドの検証

```bash
# ビルドテスト
uv build
# → dist/ ディレクトリにwheelファイルが生成される

# インストールテスト
uv pip install dist/mcp_postgres-0.1.0-py3-none-any.whl
# → 正常にインストールされる

# インポートテスト
uv run python -c "import mcp_postgres; print('Success')"
# → "Success" が表示される
```

### 実行の検証

```bash
# スクリプト実行テスト
uv run mcp-postgres --help
# → サーバーのヘルプが表示される（非同期関数のため実際の出力は異なる場合あり）
```

## トラブルシューティング

### よくある問題

1. **モジュールが見つからない**
   ```bash
   ModuleNotFoundError: No module named 'mcp_postgres'
   ```
   **解決策**: パッケージが正しくインストールされているか確認

2. **スクリプトが見つからない**
   ```bash
   Command 'mcp-postgres' not found
   ```
   **解決策**: `uv pip install`でパッケージを再インストール

3. **ビルドエラー**
   ```bash
   Error: Expected a Python module at: src\mcp_postgres\__init__.py
   ```
   **解決策**: パッケージ構造が正しいか確認

### デバッグ方法

```bash
# インストールされているパッケージの確認
uv pip list | grep mcp-postgres

# スクリプトの場所確認
uv run which mcp-postgres

# パッケージ情報の確認
uv run python -c "import mcp_postgres; print(mcp_postgres.__file__)"
```

## ベストプラクティス

### 開発時のワークフロー

1. **変更のテスト**:
   ```bash
   uv build && uv pip install dist/mcp_postgres-*.whl
   uv run mcp-postgres
   ```

2. **依存関係の更新**:
   ```bash
   uv sync
   uv build
   ```

3. **パッケージ公開準備**:
   ```bash
   uv build
   uv publish check  # 公開前のチェック
   ```

### 設定の管理

- `pyproject.toml`で全ての設定を一元管理
- 環境変数による設定の上書きをサポート
- 開発依存関係と本番依存関係を分離

## まとめ

この移行により、PostgreSQL MCP Serverプロジェクトは以下のメリットを得ました：

1. **標準化**: Pythonパッケージの標準的なビルド・実行方法
2. **効率化**: uvによる高速なビルドと依存関係解決
3. **統合**: 開発環境と本番環境の統一
4. **保守性**: シンプルで一貫性のある設定

この変更は、プロジェクトの成熟度と保守性を向上させる重要なステップです。
