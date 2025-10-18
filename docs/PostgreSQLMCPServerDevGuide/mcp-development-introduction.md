# MCPサーバー開発入門

このガイドでは、MCP（Model Context Protocol）サーバーの開発を始めるための基礎知識を説明します。

## MCPプロトコルとは

MCP（Model Context Protocol）は、AIアシスタントが外部のツールやリソースと安全に連携するための標準プロトコルです。

### 主な特徴
- **ツール**: AIが実行できる操作（例：データベースクエリ実行）
- **リソース**: AIが参照できる情報（例：データベーススキーマ）
- **プロトコル**: 標準化された通信方法

### なぜMCPサーバーを開発するのか
- AIアシスタントにカスタム機能を提供
- 安全なデータアクセスを実現
- 再利用可能なコンポーネントを作成

## 開発環境のセットアップ

### 前提条件
- Python 3.10以上
- パッケージマネージャー（uv推奨）
- コードエディター（VS Code推奨）

### 環境構築手順

#### Linux/macOS
```bash
# プロジェクトディレクトリの作成
mkdir my-mcp-server
cd my-mcp-server

# uvのインストール（推奨）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 仮想環境の作成と依存関係のインストール
uv init
uv add mcp
```

#### Windows
```powershell
# プロジェクトディレクトリの作成
mkdir my-mcp-server
cd my-mcp-server

# uvのインストール（PowerShellを使用）
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 仮想環境の作成と依存関係のインストール
uv init
uv add mcp
```

**注意**: WindowsではPowerShellを使用することを推奨します。コマンドプロンプトでも動作しますが、一部の機能で制限がある場合があります。

### 基本的なプロジェクト構造

```
my-mcp-server/
├── src/
│   └── my_mcp_server/
│       ├── __init__.py
│       ├── main.py
│       └── tools/
│           └── __init__.py
├── pyproject.toml
├── README.md
└── .gitignore
```

## 最初のMCPサーバー作成

### 実装パターンの説明

実際のPostgreSQL MCPサーバーでは、以下のパターンを使用しています：

1. **ツール定義とハンドラーの分離**: ツールの定義と実行ロジックを分離
2. **モジュール化**: 機能ごとにモジュールを分割
3. **レジストリパターン**: ツールとハンドラーを登録する統一された方法
4. **動的ツール登録**: 単一の`@server.call_tool()`デコレーターで複数ツールを処理

このパターンにより、コードの保守性と拡張性が向上します。

#### モジュール化のベストプラクティス

**実際のPostgreSQL MCPサーバーの構造**:
```
src/mcp_postgres_duwenji/
├── main.py              # サーバーコア
├── config.py            # 設定管理
├── database.py          # データベース接続
├── resources.py         # リソース管理
└── tools/
    ├── __init__.py
    ├── crud_tools.py    # CRUD操作ツール
    └── schema_tools.py  # スキーマ情報ツール
```

**各モジュールの役割**:
- **crud_tools.py**: データベースのCRUD操作ツール
- **schema_tools.py**: スキーマ情報取得ツール
- **resources.py**: 静的・動的リソース管理
- **main.py**: サーバー統合とツール登録

**利点**:
- 機能ごとの責務分離
- テストのしやすさ
- コードの再利用性
- チーム開発の効率化

### 基本的なMCPサーバーの実装

#### 1. ツール定義とハンドラーの分離

```python
# src/my_mcp_server/tools/echo_tools.py
from mcp import Tool
from typing import Dict, Any

# ツール定義
echo_tool = Tool(
    name="echo",
    description="入力されたテキストをそのまま返します",
    inputSchema={
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "エコーするメッセージ"
            }
        },
        "required": ["message"]
    }
)

# ツールハンドラー
async def handle_echo(message: str) -> Dict[str, Any]:
    """エコーツールのハンドラー"""
    return {
        "success": True,
        "result": f"エコー: {message}"
    }

# ツールレジストリ
def get_echo_tools() -> list:
    """エコーツールの一覧を取得"""
    return [echo_tool]

def get_echo_handlers() -> Dict[str, callable]:
    """エコーツールのハンドラーを取得"""
    return {
        "echo": handle_echo
    }
```

#### 2. メインサーバーの実装

```python
# src/my_mcp_server/main.py
import asyncio
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server

# ツールのインポート
from .tools.echo_tools import get_echo_tools, get_echo_handlers

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """MCPサーバーのメインエントリーポイント"""
    # MCPサーバーの作成
    server = Server("my-mcp-server")
    
    # ツールとハンドラーの取得
    echo_tools = get_echo_tools()
    echo_handlers = get_echo_handlers()
    
    # すべてのツールとハンドラーを結合
    all_tools = echo_tools
    all_handlers = {**echo_handlers}
    
    # ツールハンドラーの登録
    @server.call_tool()
    async def handle_tool_call(name: str, arguments: dict) -> dict:
        """ツール実行リクエストのハンドラー"""
        logger.info(f"Tool call: {name} with arguments: {arguments}")
        
        if name in all_handlers:
            handler = all_handlers[name]
            try:
                result = await handler(**arguments)
                logger.info(f"Tool {name} executed successfully")
                return result
            except Exception as e:
                logger.error(f"Tool {name} execution failed: {e}")
                return {"success": False, "error": str(e)}
        else:
            logger.error(f"Unknown tool: {name}")
            return {"success": False, "error": f"Unknown tool: {name}"}
    
    # ツール一覧の登録
    @server.list_tools()
    async def handle_list_tools() -> list:
        """利用可能なツールの一覧を返す"""
        logger.info("Listing available tools")
        return all_tools
    
    # サーバーの起動
    logger.info("Starting MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

def cli_main():
    """CLIエントリーポイント"""
    asyncio.run(main())

if __name__ == "__main__":
    cli_main()
```

### pyproject.tomlの設定

```toml
[project]
name = "my-mcp-server"
version = "1.0.0"
description = "My first MCP server"
authors = [
    { name = "Your Name", email = "your.email@example.com" },
]
requires-python = ">=3.10"
dependencies = [
    "mcp>=1.0.0",
]

[project.scripts]
my-mcp-server = "my_mcp_server.main:main"

[build-system]
requires = ["uv_build >= 0.9.2, <0.10.0"]
build-backend = "uv_build"
```

## サーバーのテスト

### ビルドとインストール

```bash
# パッケージのビルド
uv build

# ローカルインストール
uv pip install -e .
```

### 動作確認

```bash
# 方法1: インストール後のスクリプト実行
my-mcp-server

# 方法2: uv runを使用（インストール不要）
uv run my-mcp-server

# 実際のPostgreSQL MCPサーバーの場合
mcp_postgres_duwenji
```

#### 方法1の補足説明

**方法1** (`my-mcp-server`) は、パッケージをインストールした後に使用できる方法です。この方法の仕組み：

1. **スクリプト登録**: `pyproject.toml`の`[project.scripts]`セクションで定義されたコマンドがシステムに登録されます
2. **実行フロー**:
   - `uv pip install -e .` 実行時にスクリプトラッパーが生成されます
   - Windows: `Scripts\my-mcp-server.exe` が作成されます
   - Linux/macOS: `bin/my-mcp-server` が作成されます
   - これらのラッパーは正しいPython環境で指定された関数を実行します

3. **利点**:
   - シンプルなコマンド名だけで実行可能
   - 正しいPython環境で自動的に実行される
   - 開発中は`uv pip install -e .`で変更が即時反映される

4. **注意点**:
   - パッケージのインストールが必要（`uv pip install -e .`）
   - グローバル環境にインストールされる
   - 開発環境では方法2の`uv run`を使用する方が安全

**実際のPostgreSQL MCPサーバー**では、`mcp_postgres_duwenji`コマンドが`src/mcp_postgres_duwenji/main.py`の`cli_main()`関数を実行し、非同期サーバーを起動します。

## 次のステップ

この基本的なMCPサーバーが動作したら、以下のステップに進みましょう：

1. **より複雑なツールの実装**
2. **リソースの追加**
3. **エラーハンドリングの強化**
4. **設定管理の実装**

## よくある質問

### Q: MCPサーバーはどのようにAIアシスタントと連携しますか？
A: MCPクライアント（Clineなど）がサーバーを起動し、標準入出力を通じて通信します。

### Q: 非同期処理は必須ですか？
A: はい、MCPプロトコルは非同期通信を前提としています。

### Q: どのようなツールを実装すべきですか？
A: ユースケースに応じて、データベース操作、API呼び出し、ファイル操作などが一般的です。

## トラブルシューティング

### サーバーが起動しない場合
- Pythonのバージョンが3.10以上であることを確認
- 依存関係が正しくインストールされていることを確認
- スクリプトエントリーポイントが正しく設定されていることを確認

### ツールが認識されない場合
- ツール定義が正しい形式であることを確認
- ツール名が一意であることを確認
- 入力スキーマが正しく定義されていることを確認

### Windows固有の問題

#### uvインストールエラー
```powershell
# インストールスクリプトの実行がブロックされる場合
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### 環境変数の反映問題
- 新しいPowerShellセッションを開始
- 環境変数の設定後、コマンドプロンプトやPowerShellを再起動
- システムの環境変数設定を確認（コントロールパネル → システム → 詳細設定）

#### パス関連の問題
- ファイルパスにスペースが含まれている場合、引用符で囲む
- バックスラッシュとスラッシュの混在に注意
- 長いファイルパスによる問題を避けるため、プロジェクトを短いパスに配置

#### 権限関連の問題
- 管理者権限が必要な操作がある場合、PowerShellを管理者として実行
- ファイルやディレクトリの権限設定を確認

この入門ガイドを基に、独自のMCPサーバー開発を始めてみましょう！
