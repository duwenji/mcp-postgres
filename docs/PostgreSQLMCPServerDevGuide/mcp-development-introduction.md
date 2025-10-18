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

### 基本的なMCPサーバーの実装

```python
# src/my_mcp_server/main.py
import asyncio
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio

# サーバーの作成
server = Server("my-mcp-server")

@server.list_tools()
async def handle_list_tools() -> list:
    """利用可能なツールの一覧を返す"""
    return [
        {
            "name": "echo",
            "description": "入力されたテキストをそのまま返します",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "エコーするメッセージ"
                    }
                },
                "required": ["message"]
            }
        }
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list:
    """ツールの実行"""
    if name == "echo":
        message = arguments.get("message", "")
        return [{
            "type": "text",
            "text": f"エコー: {message}"
        }]
    else:
        raise ValueError(f"不明なツール: {name}")

async def main():
    # 標準入出力でサーバーを実行
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="my-mcp-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                )
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
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
requires = ["hatchling"]
build-backend = "hatchling.build"
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
# サーバーの実行テスト
my-mcp-server
```

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

この入門ガイドを基に、独自のMCPサーバー開発を始めてみましょう！
