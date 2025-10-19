# リンターとタイプチェック完全ガイド

## はじめに

このガイドでは、PostgreSQL MCP Serverプロジェクトで使用されているリンター（Flake8）とタイプチェッカー（MyPy）の詳細な使用方法について説明します。これらのツールはコードの品質と保守性を高めるために不可欠です。

## Flake8 リンター

### Flake8とは

Flake8はPythonコードの品質をチェックするための包括的なツールで、以下のコンポーネントを統合しています：

- **PyFlakes**: 論理エラーの検出
- **pycodestyle**: PEP 8準拠のチェック
- **McCabe**: 循環的複雑度の測定

### 基本的な使用方法

```bash
# 基本的なリンター実行
uv run flake8 src/ test/

# 特定のディレクトリのみチェック
uv run flake8 src/mcp_postgres_duwenji/

# エラーのみ表示（警告を非表示）
uv run flake8 --select E src/

# 統計情報の表示
uv run flake8 --statistics src/
```

### 高度なオプション

```bash
# 最大行長の変更
uv run flake8 --max-line-length 100 src/

# 特定のエラーコードを無視
uv run flake8 --ignore E203,W503 src/

# 出力形式の変更
uv run flake8 --format=default src/  # デフォルト形式
uv run flake8 --format=pylint src/   # pylint形式
uv run flake8 --format=json src/     # JSON形式

# ファイルごとの統計
uv run flake8 --count src/
```

### エラーコードの説明

#### 一般的なエラーコード

**pycodestyle (E, W)**
- **E101**: インデントの混合（スペースとタブ）
- **E201/E202**: 括弧前後の余分な空白
- **E203**: コロン前後の空白
- **E301/E302/E303**: クラス/関数間の空行
- **E501**: 行が長すぎる（> 88文字）
- **W291**: 行末の余分な空白
- **W293**: 空白行に空白文字

**PyFlakes (F)**
- **F401**: 未使用のインポート
- **F402**: インポートのシャドウ
- **F403**: ワイルドカードインポートの使用
- **F404**: 将来のインポートの誤用
- **F811**: 関数の重複定義
- **F821**: 未定義の名前
- **F841**: 未使用のローカル変数

**McCabe (C901)**
- **C901**: 関数の循環的複雑度が高すぎる

### 設定ファイルの詳細

#### `.flake8` 設定例

```ini
[flake8]
# 基本設定
max-line-length = 88
exclude = 
    .git,
    __pycache__,
    build,
    dist,
    .venv,
    .eggs,
    *.egg-info,
    docs,
    examples

# 無視するエラー
ignore = 
    E203,  # コロン前後の空白
    W503,  # 行継続演算子前の演算子
    E501,  # 行が長すぎる（Blackが処理）

# ファイルごとの無視設定
per-file-ignores =
    __init__.py: F401  # __init__.pyでの未使用インポートを許可
    test_*.py: F401    # テストファイルでの未使用インポートを許可

# プラグイン設定
max-complexity = 10
```

## MyPy タイプチェッカー

### MyPyとは

MyPyはPythonの静的型チェッカーで、型注釈を使用してコードの型安全性を検証します。

### 基本的な使用方法

```bash
# 基本的なタイプチェック
uv run mypy src/

# 厳格モード
uv run mypy --strict src/

# 特定のモジュールのみチェック
uv run mypy src/mcp_postgres_duwenji/config.py

# キャッシュを使用
uv run mypy --cache-dir .mypy_cache src/

# インクリメンタルチェック
uv run mypy --incremental src/
```

### 高度なオプション

```bash
# 特定のエラーのみ表示
uv run mypy --warn-unused-ignores src/

# 厳格な等価性チェック
uv run mypy --strict-equality src/

# 未使用の設定を警告
uv run mypy --warn-unused-configs src/

# 任意の戻り値を警告
uv run mypy --warn-return-any src/

# 詳細なエラーレポート
uv run mypy --show-error-codes src/
```

### 型注釈の例

#### 基本的な型注釈

```python
from typing import List, Dict, Optional, Union, Any

# 関数の型注釈
def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """ユーザー情報を取得する関数"""
    # 実装
    pass

# クラスの型注釈
class DatabaseConnection:
    def __init__(self, host: str, port: int = 5432) -> None:
        self.host = host
        self.port = port
    
    def connect(self) -> bool:
        """データベースに接続"""
        return True

# ジェネリック型
def process_items(items: List[str]) -> List[int]:
    """文字列リストを整数リストに変換"""
    return [int(item) for item in items]
```

#### 高度な型注釈

```python
from typing import TypeVar, Generic, Protocol, Callable
from dataclasses import dataclass

# 型変数
T = TypeVar('T')

class Repository(Generic[T]):
    def find_by_id(self, id: int) -> Optional[T]:
        pass
    
    def save(self, entity: T) -> T:
        pass

# プロトコル（構造的部分型）
class Connectable(Protocol):
    def connect(self) -> bool: ...
    def disconnect(self) -> None: ...

# コールバック型
Callback = Callable[[str, int], bool]

@dataclass
class User:
    id: int
    name: str
    email: str
```

### 設定ファイルの詳細

#### `pyproject.toml` のMyPy設定

```toml
[tool.mypy]
# 基本設定
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

# パフォーマンス設定
cache_dir = ".mypy_cache"
show_error_codes = true

# モジュールごとの設定
[[tool.mypy.overrides]]
module = [
    "tests.*",
    "test.*"
]
ignore_missing_imports = true
disallow_untyped_defs = false

[[tool.mypy.overrides]]
module = [
    "src.mcp_postgres_duwenji.config"
]
disallow_untyped_defs = true
```

## 統合ワークフロー

### 開発時のベストプラクティス

#### 1. 事前コミットフック

`.pre-commit-config.yaml` の例：

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        args: [--check]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        args: [--strict]
```

#### 2. VS Code設定

`.vscode/settings.json` の例：

```json
{
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "python.linting.flake8Args": [
    "--max-line-length=88",
    "--ignore=E203,W503"
  ],
  "python.linting.mypyArgs": [
    "--strict",
    "--show-error-codes"
  ]
}
```

### GitHub Actionsでの自動実行

```yaml
name: Linting and Type Checking

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  linting:
    name: Linting and Type Checking
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Install uv
      run: pip install uv

    - name: Install dependencies
      run: uv sync --group dev

    - name: Run Flake8
      run: uv run flake8 src/ test/

    - name: Run MyPy
      run: uv run mypy src/

    - name: Upload MyPy cache
      uses: actions/cache@v3
      if: always()
      with:
        path: .mypy_cache
        key: mypy-cache-${{ github.sha }}
        restore-keys: mypy-cache-
```

## トラブルシューティング

### Flake8の一般的な問題

#### 1. インポートエラー
```python
# 問題: 循環インポートによるF401
from . import module_a  # F401

# 解決策: 型注釈のみのインポート
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import module_a
```

#### 2. 長い行の処理
```python
# 問題: E501 行が長すぎる
result = very_long_function_name(param1, param2, param3, param4, param5, param6)

# 解決策: 複数行に分割
result = very_long_function_name(
    param1, param2, param3, 
    param4, param5, param6
)
```

### MyPyの一般的な問題

#### 1. 動的型付けの処理
```python
# 問題: 動的型付けによるエラー
def process_data(data):
    return data.get('value', 0)  # 型が不明

# 解決策: 型注釈の追加
from typing import Any, Dict

def process_data(data: Dict[str, Any]) -> int:
    return data.get('value', 0)
```

#### 2. オプショナル値の処理
```python
# 問題: オプショナル値の安全でないアクセス
def get_name(user: Optional[Dict]) -> str:
    return user['name']  # 危険: userがNoneの場合

# 解決策: 安全なアクセス
def get_name(user: Optional[Dict]) -> str:
    if user is None:
        return "Unknown"
    return user['name']
```

## 参考リソース

- [Flake8公式ドキュメント](https://flake8.pycqa.org/)
- [MyPy公式ドキュメント](https://mypy.readthedocs.io/)
- [Python型ヒント公式ドキュメント](https://docs.python.org/3/library/typing.html)
- [PEP 8 - Pythonコードスタイルガイド](https://www.python.org/dev/peps/pep-0008/)
- [PEP 484 - 型ヒント](https://www.python.org/dev/peps/pep-0484/)

---

*このガイドは実際のプロジェクト実装とベストプラクティスに基づいて作成されています。*
