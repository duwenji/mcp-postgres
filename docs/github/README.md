# GitHub ドキュメント

このディレクトリには、GitHubの機能と使用方法に関する体系的な資料が含まれています。

## ドキュメント一覧

### 📋 [GitHub Workflow 完全ガイド](github-workflow-guide.md)
GitHub Actions（GitHub Workflow）の包括的なガイド：
- 基本概念と用語
- ワークフロー構文
- 実装例とベストプラクティス
- トラブルシューティング

### 🗂️ [GitHub ファイル構造と設定ファイルガイド](github-files-structure.md)
GitHubリポジトリのファイル構造と設定ファイルについて：
- 主要なGitHubファイルの役割
- プロジェクト管理ファイル
- セキュリティ関連ファイル
- ベストプラクティス

### 🐳 [GitHub Actions サービスコンテナ完全ガイド](github-services-containers-guide.md)
GitHub Actionsでのサービスコンテナ使用方法：
- サービスコンテナの基本概念
- PostgreSQL、MySQL、Redisなどの設定例
- ヘルスチェックとトラブルシューティング
- ベストプラクティスとセキュリティ

## このプロジェクトのGitHub実装

### 現在の構成
このプロジェクトでは以下のGitHub機能を実装しています：

#### 1. GitHub Actionsワークフロー
- **ファイル**: `.github/workflows/publish.yml`
- **目的**: Pythonパッケージの自動公開
- **トリガー**: リリース公開時、手動実行
- **機能**: テスト、リント、ビルド、PyPI公開、TestPyPI公開

#### 2. 主要なGitHubファイル
- `README.md` / `README_ja.md` - プロジェクト説明
- `LICENSE` - MITライセンス
- `.gitignore` - Git除外設定
- `CHANGELOG.md` - 変更履歴

### ワークフローの特徴

#### マルチステージ構成
```yaml
jobs:
  test:           # テスト実行（PostgreSQLサービス使用）
  lint:           # コード品質チェック
  build:          # パッケージビルド
  publish:        # PyPI公開（OIDC認証）
  publish-testpypi: # TestPyPI公開（手動実行時のみ）
```

#### サービスコンテナの活用
```yaml
services:
  postgres:  # テスト用PostgreSQL
```

#### セキュアな公開
```yaml
environment: release
permissions:
  id-token: write  # OIDC認証
```

## 学習リソース

### 公式ドキュメント
- [GitHub Actions 公式ドキュメント](https://docs.github.com/ja/actions)
- [GitHub Docs](https://docs.github.com/ja)

### 参考リンク
- [GitHub Marketplace](https://github.com/marketplace?type=actions)
- [Awesome Actions](https://github.com/sdras/awesome-actions)
- [Open Source Guides](https://opensource.guide/)

## 次のステップ

1. **基本を学ぶ**: [GitHub Workflow 完全ガイド](github-workflow-guide.md)から始める
2. **ファイル構造を理解**: [GitHub ファイル構造ガイド](github-files-structure.md)を読む
3. **実践**: 実際のワークフローファイルを参照
4. **カスタマイズ**: プロジェクトのニーズに合わせて調整

---

*これらのドキュメントは、実際のプロジェクト実装に基づいて作成されています。*
