# GitHub ファイル構造と設定ファイルガイド

## はじめに

GitHubリポジトリでは、特定のファイルやディレクトリが特別な意味を持ち、リポジトリの動作や表示を制御します。このガイドでは、GitHubが認識する主要なファイルとその役割について説明します。

## 主要なGitHubファイル

### 1. `.github/` ディレクトリ
GitHub固有の設定ファイルを格納するディレクトリ

#### サブディレクトリ
- **workflows/**: GitHub Actionsワークフローファイル
- **ISSUE_TEMPLATE/**: イシューテンプレート
- **PULL_REQUEST_TEMPLATE/**: プルリクエストテンプレート

### 2. ルートレベルの設定ファイル

#### README.md
- リポジトリのメイン説明文書
- 自動的にリポジトリトップページに表示
- Markdown形式で記述

#### LICENSE
- ソフトウェアライセンス
- オープンソースプロジェクトでは必須

#### .gitignore
- Gitで追跡しないファイル/ディレクトリの指定
- 言語/フレームワーク固有のテンプレートが利用可能

#### CONTRIBUTING.md
- コントリビューションガイドライン
- プルリクエストの作成方法などを記載

#### CODE_OF_CONDUCT.md
- 行動規範
- コミュニティの健全な発展を促進

## GitHub Actions関連ファイル

### ワークフローファイル
- 場所: `.github/workflows/`
- 形式: YAML (.yml または .yaml)
- 命名規則: 意味のある名前（例: `ci.yml`, `deploy.yml`）

### このプロジェクトの例
```
.github/
└── workflows/
    └── publish.yml    # パッケージ公開ワークフロー
```

## イシューとプルリクエストの管理

### イシューテンプレート
- 場所: `.github/ISSUE_TEMPLATE/`
- 種類:
  - `bug_report.md` - バグ報告用
  - `feature_request.md` - 機能要望用
  - `config.yml` - テンプレート設定

### プルリクエストテンプレート
- 場所: `.github/PULL_REQUEST_TEMPLATE/`
- プルリクエスト作成時に自動入力

## セキュリティ関連ファイル

### SECURITY.md
- セキュリティポリシー
- 脆弱性報告の手順

### dependabot.yml
- 依存関係の自動更新設定
- 場所: `.github/dependabot.yml`

## プロジェクト管理ファイル

### PROJECTS.md
- プロジェクトの進捗状況
- ロードマップ

### CHANGELOG.md
- 変更履歴
- バージョンごとの変更点

### ROADMAP.md
- 開発ロードマップ
- 将来の計画

## コード品質関連

### .editorconfig
- エディタ設定の統一
- インデント、エンコーディングなど

### .pre-commit-config.yaml
- コミット前フックの設定
- コード品質チェックの自動化

## このプロジェクトのファイル構造

### 現在の構成
```
mcp-postgres/
├── .github/
│   └── workflows/
│       └── publish.yml          # パッケージ公開ワークフロー
├── README.md                    # プロジェクト説明
├── README_ja.md                # 日本語版README
├── LICENSE                     # MITライセンス
├── .gitignore                  # Git除外設定
├── CHANGELOG.md               # 変更履歴
├── pyproject.toml             # Pythonプロジェクト設定
├── uv.lock                    # 依存関係ロックファイル
└── docs/                      # ドキュメント
```

### 推奨される追加ファイル

#### 1. コントリビューションガイド
```markdown
# CONTRIBUTING.md

## 開発環境のセットアップ
1. リポジトリをクローン
2. 依存関係をインストール
3. テストを実行

## プルリクエストの作成
- 機能ブランチを作成
- テストを追加/更新
- ドキュメントを更新
```

#### 2. セキュリティポリシー
```markdown
# SECURITY.md

## 脆弱性の報告
問題を発見した場合は、以下の方法で報告してください：
1. プライベートな方法で連絡
2. 詳細な説明を提供
3. 再現手順を含める
```

## ベストプラクティス

### 1. ファイル命名
- 明確で一貫性のある名前
- 小文字とハイフンの使用（例: `code-of-conduct.md`）

### 2. ドキュメントの維持
- 定期的な更新
- 実際のコードとの整合性確認

### 3. 多言語対応
- 必要に応じて多言語ドキュメントの提供
- 明確な言語指定（例: `README_ja.md`）

### 4. バージョン管理
- 重要な変更の記録
- セマンティックバージョニングの遵守

## 自動化の活用

### GitHub Actionsの活用例
- 自動テスト実行
- コード品質チェック
- ドキュメント生成
- パッケージ公開

### このプロジェクトの自動化
```yaml
# .github/workflows/publish.yml
name: Publish Python Package

on:
  release:
    types: [published]
  workflow_dispatch:
```

## トラブルシューティング

### 一般的な問題
1. **ファイルが認識されない**
   - ファイル名の確認
   - 場所の確認
   - 権限の確認

2. **ワークフローが実行されない**
   - トリガー条件の確認
   - 構文エラーの確認

3. **テンプレートが表示されない**
   - ディレクトリ構造の確認
   - ファイル形式の確認

## 参考リソース

- [GitHub Docs - Creating a default community health file](https://docs.github.com/ja/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file)
- [GitHub Actions Documentation](https://docs.github.com/ja/actions)
- [Open Source Guides](https://opensource.guide/)

---

*このプロジェクトはPythonパッケージとして公開されるMCPサーバーであり、適切なGitHubファイル構造を実装しています。*
