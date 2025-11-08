# VS Code Tasks ガイド

## 概要

このドキュメントでは、MCP PostgreSQLサーバープロジェクトで利用可能なVS Codeタスクの仕組みと使用方法について説明します。

## タスクの仕組み

### タスク設定ファイル
- **ファイル**: `.vscode/tasks.json`
- **目的**: VS Codeの統合タスクランナーを設定
- **バージョン**: 2.0.0（最新のタスクスキーマ）

### タスク実行方法
1. **コマンドパレット**: `Ctrl+Shift+P` → "Tasks: Run Task"
2. **ターミナルメニュー**: ターミナルパネルの「タスクの実行」ボタン
3. **ショートカット**: 一部のタスクはビルドタスクとして直接実行可能

## 利用可能なタスク

### 1. 依存関係管理

#### Install Dependencies
```bash
uv sync --group dev
```

**目的**:  
開発用依存関係をインストールします。

**使用タイミング**:  
- プロジェクトの初回セットアップ時
- 依存関係の変更後
- 新しい開発者による環境構築時

### 2. コード品質チェック

#### Format Code (Black)
```bash
uv run black src/ test/
```

**目的**:  
Pythonコードの自動フォーマットを実行します。

**設定**:  
`pyproject.toml`の`[tool.black]`セクションに基づく設定を使用します。

**特徴**:  
- 一貫したコードスタイルの維持
- 可読性の向上
- チームでのコーディング規約の統一

**使用タイミング**:  
- コード変更後
- コミット前
- プルリクエスト作成前

#### Lint Code (Flake8)
```bash
uv run flake8 src/ test/
```

**目的**:  
コードスタイルと品質のチェックを実行します。

**問題マッチャー**:  
`$flake8`（VS Codeがエラーを自動検出）

**使用タイミング**:  
- コード品質の確認時
- スタイルガイド違反の検出時
- コードレビュー前

#### Type Check (MyPy)
```bash
uv run mypy src/
```

**目的**:  
静的型チェックを実行します。

**設定**:  
`pyproject.toml`の`[tool.mypy]`セクションに基づく設定を使用します。

**問題マッチャー**:  
`$mypy`

**使用タイミング**:  
- 型関連のエラー検出時
- リファクタリング後
- 新しい機能実装後

#### Security Scan (Bandit)
```bash
uv run bandit -r src/
```

**目的**:  
セキュリティ脆弱性のスキャンを実行します。

**出力**:  
潜在的なセキュリティ問題のレポートを生成します。

**使用タイミング**:  
- セキュリティレビュー前
- 新しい外部ライブラリ導入後
- リリース前のセキュリティチェック

### 3. テスト実行

#### Run Tests
```bash
uv run pytest test/ -v
```

**目的**:  
基本的なテストスイートを実行します。

**問題マッチャー**:  
`$pytest`（VS Codeがテスト結果を自動解析）

**使用タイミング**:  
- 機能変更後の回帰テスト
- バグ修正後の確認
- 継続的インテグレーション

#### Run Tests with Coverage
```bash
uv run pytest test/ --cov=src/mcp_postgres_duwenji --cov-report=html --cov-report=term
```

**目的**:  
コードカバレッジ付きでテストを実行します。

**出力**:  
- ターミナルでのカバレッジレポート
- HTMLレポート（`htmlcov/`ディレクトリ）

**使用タイミング**:  
- カバレッジ目標の達成確認
- テスト不足の領域の特定
- 品質保証活動

### 4. ビルドと実行

#### Build Package
```bash
uv build
```

**目的**:  
配布用パッケージをビルドします。

**出力**:  
`dist/`ディレクトリにビルド済みパッケージを生成します。

**使用タイミング**:  
- リリース前のパッケージ作成
- PyPI公開前の確認
- 配布用バイナリの生成

#### Run MCP Server
```bash
uv run mcp-postgres-duwenji
```

**目的**:  
MCPサーバーをローカルで実行します。

**使用タイミング**:  
- 開発中の機能テスト
- デバッグ作業
- 統合テストの準備

### 5. 包括的チェック

#### Full Code Quality Check
**タイプ**: 複合タスク
**依存タスク**:
1. Format Code (Black)
2. Lint Code (Flake8) 
3. Type Check (MyPy)
4. Security Scan (Bandit)
5. Run Tests with Coverage

**目的**: 完全なコード品質チェックを一度に実行

## ワークフロー例

### 開発時の推奨ワークフロー

1. **コード変更前**:
   ```bash
   # 依存関係の確認
   Tasks: Run Task → Install Dependencies
   ```

2. **コード変更後**:
   ```bash
   # クイックチェック
   Tasks: Run Task → Format Code (Black)
   Tasks: Run Task → Lint Code (Flake8)
   ```

3. **コミット前**:
   ```bash
   # 完全な品質チェック
   Tasks: Run Task → Full Code Quality Check
   ```

4. **リリース前**:
   ```bash
   # パッケージビルド
   Tasks: Run Task → Build Package
   ```

### 問題マッチャーの仕組み

VS Codeは問題マッチャーを使用してタスク出力を解析します：

- **`$flake8`**: Flake8の出力形式を解析
- **`$mypy`**: MyPyの型エラーを検出
- **`$pytest`**: テスト結果を問題パネルに表示

## カスタマイズ方法

### 新しいタスクの追加

`.vscode/tasks.json`に新しいタスクオブジェクトを追加：

```json
{
    "label": "Custom Task",
    "type": "shell",
    "command": "uv",
    "args": ["run", "custom-command"],
    "group": "build"
}
```

### 既存タスクの変更

各タスクの主要設定項目：

- **`label`**: タスク名（必須）
- **`type`**: タスクタイプ（`shell`または`process`）
- **`command`**: 実行コマンド
- **`args`**: コマンド引数
- **`group`**: タスクグループ（`build`, `test`, `none`）
- **`presentation`**: 表示設定
- **`problemMatcher`**: 問題解析設定

## トラブルシューティング

### 一般的な問題

1. **タスクが見つからない**:
   - `.vscode/tasks.json`が正しい場所にあるか確認
   - VS Codeを再起動

2. **コマンドが実行できない**:
   - uvがインストールされているか確認
   - 仮想環境がアクティブか確認

3. **問題マッチャーが動作しない**:
   - 出力形式が正しいか確認
   - 問題パネルを確認

### デバッグ方法

1. **詳細出力の有効化**:
   ```json
   "presentation": {
       "echo": true,
       "reveal": "always"
   }
   ```

2. **タスク出力の確認**:
   - ターミナルパネルで出力を確認
   - 問題パネルでエラーを確認

## ベストプラクティス

1. **定期的な実行**:
   - コード変更ごとにフォーマットとリンターを実行
   - コミット前に完全な品質チェックを実行

2. **自動化**:
   - 保存時の自動フォーマットを検討
   - プリコミットフックの設定

3. **チームでの一貫性**:
   - すべての開発者が同じタスクを使用
   - コードスタイルの統一

このタスクシステムを使用することで、一貫したコード品質と効率的な開発ワークフローを維持できます。
