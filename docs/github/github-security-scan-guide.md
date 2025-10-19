# GitHub Security Scan 完全ガイド

## はじめに

GitHub Security Scanは、コードのセキュリティ脆弱性を自動的に検出するための重要な機能です。このガイドでは、Banditを使用したPythonプロジェクトのセキュリティスキャン実装について詳しく説明します。

## セキュリティスキャンの重要性

### なぜセキュリティスキャンが必要か
- **早期発見**: 開発段階での脆弱性発見
- **コスト削減**: 本番環境での問題発生を防止
- **品質向上**: セキュアなコードの実装促進
- **コンプライアンス**: セキュリティ基準の遵守

## Bandit セキュリティスキャナー

### Banditとは
BanditはPythonコードのセキュリティ脆弱性を検出するための静的解析ツールです。

### 主な検出対象
- **SQLインジェクション**: 不適切なSQLクエリ構築
- **シェルインジェクション**: 危険なシェルコマンド実行
- **ハードコードされたパスワード**: コード内の認証情報
- **危険な関数の使用**: `eval()`, `exec()`などの使用
- **SSL/TLSの問題**: 安全でない暗号化設定

## 実装例

### このプロジェクトのSecurityScan実装

#### ワークフロー設定 (test.yml)
```yaml
security-scan:
  name: Security Scan
  runs-on: ubuntu-latest
  needs: test
  
  steps:
  - name: Checkout code
    uses: actions/checkout@v4

  - name: Install Bandit
    run: uv pip install bandit

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

### Banditコマンドオプション

#### 基本オプション
```bash
# 基本的なスキャン
bandit -r src/

# JSON形式で出力
bandit -r src/ -f json -o bandit-report.json

# 特定のテストを除外
bandit -r src/ --skip B101,B102

# カスタム設定ファイルの使用
bandit -r src/ -c .bandit.yml
```

#### 出力フォーマット
- **txt**: 標準テキスト形式
- **json**: JSON形式（自動化に最適）
- **html**: HTMLレポート
- **csv**: CSV形式

## トラブルシューティング

### よくある問題と解決策

#### 1. アクションが見つからないエラー
**問題**: `Unable to resolve action py-actions/bandit, repository not found`

**解決策**:
```yaml
# ❌ 誤った実装
- name: Run Bandit security scan
  uses: py-actions/bandit@v3.1.1  # このアクションは存在しない

# ✅ 正しい実装
- name: Install Bandit
  run: uv pip install bandit

- name: Run Bandit security scan
  run: uv run bandit -r src/ -f json -o bandit-report.json
```

#### 2. 依存関係の競合
**問題**: Banditのバージョン競合

**解決策**:
```yaml
- name: Install specific Bandit version
  run: uv pip install bandit==1.7.5
```

#### 3. 偽陽性の除外
**問題**: 誤検出の除外設定

**解決策**:
```yaml
- name: Run Bandit with exclusions
  run: uv run bandit -r src/ --skip B101,B601 -f json -o bandit-report.json
```

## 高度な設定

### カスタム設定ファイル (.bandit.yml)

```yaml
# .bandit.yml
skips: ['B101', 'B601']

tests:
  - B102
  - B103
  - B104

exclude_dirs:
  - '*/test/*'
  - '*/tests/*'
  - '*/migrations/*'

targets:
  - 'src/'
```

### マトリックススキャン

```yaml
security-scan:
  name: Security Scan
  runs-on: ubuntu-latest
  strategy:
    matrix:
      python-version: ['3.10', '3.11']
  
  steps:
  - name: Checkout code
    uses: actions/checkout@v4

  - name: Set up Python ${{ matrix.python-version }}
    uses: actions/setup-python@v4
    with:
      python-version: ${{ matrix.python-version }}

  - name: Install uv
    run: pip install uv

  - name: Install Bandit
    run: uv pip install bandit

  - name: Run Bandit security scan
    run: uv run bandit -r src/ -f json -o bandit-report-${{ matrix.python-version }}.json

  - name: Upload Bandit report
    uses: actions/upload-artifact@v4
    with:
      name: bandit-report-${{ matrix.python-version }}
      path: bandit-report-${{ matrix.python-version }}.json
```

## ベストプラクティス

### 1. 継続的スキャン
- すべてのプルリクエストで実行
- メインブランチへのプッシュで実行
- 定期的なスケジュール実行

### 2. 結果の活用
- レポートの自動アップロード
- 重大な問題の通知設定
- トレンド分析の実施

### 3. チーム教育
- 検出された問題の共有
- セキュアコーディングのトレーニング
- コードレビューでのセキュリティチェック

### 4. 統合と自動化
- CI/CDパイプラインへの統合
- 品質ゲートの設定
- 自動修正の検討

## 他のセキュリティツールとの統合

### 1. CodeQLとの連携
```yaml
- name: Initialize CodeQL
  uses: github/codeql-action/init@v3
  with:
    languages: python

- name: Autobuild
  uses: github/codeql-action/autobuild@v3

- name: Perform CodeQL Analysis
  uses: github/codeql-action/analyze@v3
```

### 2. 依存関係スキャン
```yaml
- name: Dependency Review
  uses: actions/dependency-review-action@v3
```

### 3. 総合的なセキュリティワークフロー

```yaml
name: Comprehensive Security Scan

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  schedule:
    - cron: '0 6 * * 1'  # 毎週月曜日6:00

jobs:
  bandit-scan:
    name: Bandit Security Scan
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Install Bandit
      run: pip install bandit

    - name: Run Bandit scan
      run: bandit -r src/ -f json -o bandit-report.json

    - name: Upload Bandit report
      uses: actions/upload-artifact@v4
      with:
        name: bandit-report
        path: bandit-report.json

  codeql-scan:
    name: CodeQL Analysis
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Initialize CodeQL
      uses: github/codeql-action/init@v3
      with:
        languages: python

    - name: Autobuild
      uses: github/codeql-action/autobuild@v3

    - name: Perform CodeQL Analysis
      uses: github/codeql-action/analyze@v3

  dependency-scan:
    name: Dependency Scan
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Run safety check
      run: pip install safety && safety check

    - name: Dependency Review
      uses: actions/dependency-review-action@v3
```

## モニタリングとレポート

### 1. ダッシュボードの構築
- セキュリティメトリクスの可視化
- トレンド分析
- 改善状況の追跡

### 2. 通知設定
- Slack/Teamsへの通知
- メール通知
- 重大な問題の即時通知

### 3. コンプライアンスレポート
- セキュリティ基準の遵守状況
- 監査用レポートの生成
- 定期的なレビュー

## 参考リソース

- [Bandit公式ドキュメント](https://bandit.readthedocs.io/)
- [GitHub Security](https://docs.github.com/ja/code-security)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://docs.python.org/3/library/security.html)

---

*このガイドは実際のプロジェクト実装と問題解決経験に基づいて作成されています。*
