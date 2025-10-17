# PostgreSQL MCP Server テスト環境

このディレクトリには、PostgreSQL MCP Serverのテスト環境とテストケースが含まれています。

## テスト構造

```
test/
├── docker/                 # Dockerテスト環境
│   ├── Dockerfile.test     # テスト用Dockerイメージ定義
│   ├── docker-compose.test.yml  # テスト環境構成
│   └── init-test-db.sql    # テストデータベース初期化スクリプト
├── fixtures/               # テストデータ
├── unit/                   # 単体テスト
│   └── test_config.py      # 設定管理のテスト
├── integration/            # 統合テスト
│   └── test_database.py    # データベース操作のテスト
├── conftest.py             # pytest設定
├── requirements-test.txt   # テスト依存関係
├── run_tests.sh           # Linux/Macテストランナー
├── run_tests.bat          # Windowsテストランナー
└── README.md              # このファイル
```

## テストの実行方法

### 前提条件

- Python 3.8以上
- DockerとDocker Compose（統合テスト用）
- PostgreSQL 15（ローカルテスト用）

### テストの実行

#### 1. すべてのテストを実行（推奨）

**Linux/Mac:**
```bash
./test/run_tests.sh
```

**Windows:**
```cmd
test\run_tests.bat
```

#### 2. 特定のテストタイプを実行

**単体テストのみ:**
```bash
./test/run_tests.sh unit
```

**統合テストのみ:**
```bash
./test/run_tests.sh integration
```

**Docker環境でのテスト:**
```bash
./test/run_tests.sh docker
```

#### 3. 手動でのテスト実行

**単体テスト:**
```bash
python -m pytest test/unit/ -v
```

**統合テスト:**
```bash
RUN_INTEGRATION_TESTS=1 python -m pytest test/integration/ -v -m integration
```

**カバレッジ付きテスト:**
```bash
python -m pytest test/ -v --cov=src --cov-report=html
```

## Dockerテスト環境

### 環境構成

- **PostgreSQLコンテナ**: テスト用データベース（ポート5433）
- **テストランナーコンテナ**: pytest実行環境

### Docker環境の起動

```bash
cd test/docker
docker-compose -f docker-compose.test.yml up --build -d
```

### Docker環境でのテスト実行

```bash
cd test/docker
docker-compose -f docker-compose.test.yml run --rm test-runner
```

### Docker環境の停止

```bash
cd test/docker
docker-compose -f docker-compose.test.yml down
```

## テストデータベース

テスト環境では以下のテーブルが自動的に作成されます：

- **users**: ユーザー情報
- **products**: 商品情報
- **orders**: 注文情報

各テーブルにはサンプルデータが挿入されます。

## テストマーカー

pytestマーカーを使用してテストを分類しています：

- `@pytest.mark.unit`: 単体テスト（外部依存なし）
- `@pytest.mark.integration`: 統合テスト（データベース依存）
- `@pytest.mark.slow`: 実行時間の長いテスト

## 環境変数

テスト実行時に設定可能な環境変数：

```bash
# データベース接続設定
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=mcp_test_db
POSTGRES_USER=test_user
POSTGRES_PASSWORD=test_password
POSTGRES_SSL_MODE=disable

# テスト実行設定
RUN_INTEGRATION_TESTS=1  # 統合テストを有効化
RUN_SLOW_TESTS=1         # 遅いテストを有効化
```

## CI/CD連携

GitHub Actionsワークフローが設定されています：

- **プッシュ/プルリクエスト時に自動実行**
- **複数Pythonバージョンでのテスト**
- **Docker環境での統合テスト**
- **コード品質チェック**
- **セキュリティスキャン**

## テストの追加

### 単体テストの追加

1. `test/unit/` ディレクトリに新しいテストファイルを作成
2. テストクラスとメソッドを定義
3. 外部依存をモック化

例：
```python
# test/unit/test_new_feature.py
import pytest
from unittest.mock import patch

class TestNewFeature:
    def test_feature_behavior(self):
        # テスト実装
        pass
```

### 統合テストの追加

1. `test/integration/` ディレクトリに新しいテストファイルを作成
2. `@pytest.mark.integration` デコレータを追加
3. データベースフィクスチャを使用

例：
```python
# test/integration/test_new_integration.py
import pytest

@pytest.mark.integration
class TestNewIntegration:
    def test_database_operation(self, db_manager):
        # データベース操作のテスト
        pass
```

## トラブルシューティング

### データベース接続エラー

1. PostgreSQLが起動していることを確認
2. ポート5433が使用可能か確認
3. 環境変数が正しく設定されているか確認

### Docker関連のエラー

1. Dockerデーモンが起動していることを確認
2. 十分なメモリが利用可能か確認
3. ネットワーク設定を確認

### テストの失敗

1. テストデータベースが正しく初期化されているか確認
2. 依存関係が正しくインストールされているか確認
3. ログを確認して詳細なエラー情報を取得

## パフォーマンスチューニング

- テストデータベースにインデックスを追加
- テストケース間でデータを共有
- 非同期テストの適切な使用
- テストの並列実行

## 参考リンク

- [pytest公式ドキュメント](https://docs.pytest.org/)
- [Docker公式ドキュメント](https://docs.docker.com/)
- [PostgreSQL公式ドキュメント](https://www.postgresql.org/docs/)
