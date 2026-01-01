# Concern-Based Filtering ガイド

このガイドでは、MCP (Model Context Protocol) サーバにおける Concern-Based Filtering 機能の実装方法について、lowlevel サーバと FastMCP サーバの両方のアプローチを説明します。

## 目次

1. [Concern-Based Filtering の概要](#concern-based-filtering-の概要)
2. [型定義とコアロジック](#型定義とコアロジック)
3. [Lowlevel サーバでの対応方法](#lowlevel-サーバでの対応方法)
4. [FastMCP サーバでの対応方法](#fastmcp-サーバでの対応方法)
5. [クライアント側の使用方法](#クライアント側の使用方法)
6. [実装例](#実装例)
7. [ベストプラクティスと注意点](#ベストプラクティスと注意点)

## Concern-Based Filtering の概要

### 機能の目的

Concern-Based Filtering は、クライアントの特定の関心事（concerns）に基づいて、サーバが提供するツール、リソース、プロンプトを動的にフィルタリングする機能です。これにより：

- **セキュリティ要件**: 高セキュリティ環境では特定のツールのみを表示
- **コスト考慮**: コストが高い操作を制限
- **パフォーマンス**: リソース集約的な操作をフィルタリング
- **カスタマイズ**: クライアントのニーズに応じた機能提供

### 基本概念

- **ConcernDefinition**: サーバがサポートする関心事の定義
  ```python
  ConcernDefinition(
      name="security",
      description="Security level required",
      values=["high", "medium", "low"],
      default="medium"
  )
  ```

- **ConcernConfiguration**: クライアントが設定する関心事の値マッピング
  ```python
  {"security": "high", "cost": "minimal"}
  ```

- **フィルタリングロジック**: プリミティブ（ツール/リソース/プロンプト）のメタデータに含まれる concern 設定と、クライアントの concern 設定を比較

## 型定義とコアロジック

### 主要な関数 (`src/mcp/shared/concerns.py`)

#### `filter_by_concerns()`
```python
def filter_by_concerns(
    primitives: list[T],
    concerns_config: types.ConcernConfiguration | None,
    concerns_map: dict[str, dict[str, str]] | None = None,
    declared_concerns: list[types.ConcernDefinition] | None = None,
) -> list[T]:
```
プリミティブのリストを concern 設定に基づいてフィルタリングします。

**特別な値「*」のサポート**: ConcernConfigurationのvalueが「*」の場合、そのconcernのvaluesに定義されたいずれかの値とマッチします。これは「いずれかの値で良い」という柔軟なマッチングを可能にします。

#### `create_concerns_map_from_primitives()`
```python
def create_concerns_map_from_primitives(
    primitives: list[T],
) -> dict[str, dict[str, str]]:
```
プリミティブから concern マッピングを作成します。

#### `extract_concerns_from_meta()`
```python
def extract_concerns_from_meta(primitive: types.BaseMetadata) -> dict[str, str] | None:
```
プリミティブの `_meta` フィールドから concern 設定を抽出します。

#### `filter_primitives_for_session()`
```python
def filter_primitives_for_session(
    primitives: list[T],
    session_concerns_config: types.ConcernConfiguration | None,
    primitive_concerns_map: dict[str, dict[str, str]] | None = None,
    declared_concerns: list[types.ConcernDefinition] | None = None,
) -> list[T]:
```
セッションの concern 設定に基づいてプリミティブをフィルタリングする便利なラッパー関数です。`declared_concerns`パラメータを渡すことで、ConcernDefinitionの情報を活用したバリデーションと「*」の特別なマッチングが有効になります。

### Concern のメタデータ形式

ツールやリソースに concern を関連付けるには、`_meta` フィールドを使用します：

```python
Tool(
    name="encrypt_data",
    description="Encrypt sensitive data with high security",
    inputSchema={"type": "object", "properties": {"data": {"type": "string"}}},
    meta={
        "concerns": {
            "security": "high",
            "cost": "minimal",
            "performance": "low",
        }
    },
)
```

### 特別な値「*」の使用方法

ConcernConfigurationでvalueに「*」を指定すると、そのconcernのvaluesに定義されたいずれかの値とマッチします。これは柔軟なフィルタリングを可能にします：

```python
# クライアント側の設定例
concerns_config = {
    "security": "high",      # セキュリティは「high」のみ許可
    "cost": "*",             # コストは「minimal」「moderate」「high」のいずれでもOK
    "performance": "high"    # パフォーマンスは「high」のみ許可
}

# サーバ側のツール定義例
tools = [
    Tool(
        name="tool1",
        meta={"concerns": {"security": "high", "cost": "minimal", "performance": "high"}}
        # マッチ: security=high, cost=minimal, performance=high
    ),
    Tool(
        name="tool2",
        meta={"concerns": {"security": "high", "cost": "moderate", "performance": "high"}}
        # マッチ: security=high, cost=moderate, performance=high
    ),
    Tool(
        name="tool3",
        meta={"concerns": {"security": "medium", "cost": "minimal", "performance": "high"}}
        # マッチしない: security=medium (highが必要)
    )
]
```

## Lowlevel サーバでの対応方法

### サーバの初期化と Concern の宣言

```python
from mcp.server.lowlevel.server import Server
import mcp.types as types

# サーバの作成
server = Server("example-server")

# Concern の宣言
server.declare_concerns([
    types.ConcernDefinition(
        name="security",
        description="Security level required for the operation",
        values=["high", "medium", "low"],
        default="medium"
    ),
    types.ConcernDefinition(
        name="cost",
        description="Estimated cost impact of using this primitive",
        values=["minimal", "moderate", "high"],
        default="moderate"
    )
])
```

### 自動フィルタリング

Lowlevel サーバでは、以下のハンドラで自動的にフィルタリングが行われます：

1. **`list_tools()`**: ツール一覧のフィルタリング
2. **`list_resources()`**: リソース一覧のフィルタリング  
3. **`list_prompts()`**: プロンプト一覧のフィルタリング

フィルタリングロジックは各ハンドラ内に組み込まれており、開発者が明示的に実装する必要はありません。

### Concern 更新の対応

Lowlevel サーバでは、`concerns/update` リクエストが自動的に処理されます。クライアントが `UpdateConcernsRequest` を送信すると、サーバセッションの `concerns_config` が更新され、登録されているコールバックが実行されます。

#### Concern 更新コールバックの登録

```python
# セッションにコールバックを登録する例
@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    # セッションを取得
    session = server.request_context.session
    
    # Concern 更新コールバックを登録
    def on_concerns_update(session, old_concerns, new_concerns):
        print(f"Concerns updated: {old_concerns} -> {new_concerns}")
        # 必要に応じてツールキャッシュを更新など
        
    session.add_concerns_update_callback(on_concerns_update)
    
    return tools_list
```

#### セッションからの Concern 設定の取得

ハンドラ内でセッションの concern 設定にアクセスするには：

```python
@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    try:
        session = server.request_context.session
        concerns_config = session.concerns_config
        if concerns_config:
            # concern 設定に基づいたカスタム処理
            pass
    except LookupError:
        # リクエストコンテキストが利用不可
        pass
    
    # ツールリストを返す（自動フィルタリング済み）
    return tools_list
```

### 完全な Lowlevel サーバ例

```python
import asyncio
import mcp.types as types
from mcp.server.lowlevel.server import Server
from mcp.server.stdio import stdio_server

# サーバの作成
server = Server("example-server")

# Concern の宣言
server.declare_concerns([
    types.ConcernDefinition(
        name="security",
        description="Security level required",
        values=["high", "medium", "low"],
        default="medium"
    )
])

# Concern 付きのツール定義
tools = [
    types.Tool(
        name="encrypt_data",
        description="Encrypt sensitive data with high security",
        inputSchema={"type": "object", "properties": {"data": {"type": "string"}}},
        meta={"concerns": {"security": "high"}}
    ),
    types.Tool(
        name="log_data",
        description="Log data with basic security",
        inputSchema={"type": "object", "properties": {"data": {"type": "string"}}},
        meta={"concerns": {"security": "medium"}}
    ),
    types.Tool(
        name="validate_data",
        description="Validate data without security concerns",
        inputSchema={"type": "object", "properties": {"data": {"type": "string"}}},
        # concern なし - すべての設定にマッチ
    )
]

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return tools

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=f"Executed {name}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

## FastMCP サーバでの対応方法

### サーバの初期化と Concern の宣言

```python
from mcp.server.fastmcp import FastMCP
import mcp.types as types

# FastMCP サーバの作成
server = FastMCP("example-server")

# Concern の宣言
server.declare_concerns([
    types.ConcernDefinition(
        name="security",
        description="Security level required",
        values=["high", "medium", "low"],
        default="medium"
    ),
    types.ConcernDefinition(
        name="cost",
        description="Cost impact",
        values=["minimal", "moderate", "high"],
        default="moderate"
    )
])
```

### Concern 更新コールバックの登録

FastMCP では、concern 設定が更新されたときのコールバックを登録できます：

```python
@server.on_concerns_update()
async def handle_concerns_update(ctx, old_concerns, new_concerns):
    """Concern 設定が更新されたときの処理"""
    if new_concerns.get("security") == "high":
        await ctx.info("Security level set to high - enabling enhanced logging")
    
    if old_concerns and new_concerns.get("cost") != old_concerns.get("cost"):
        await ctx.info(f"Cost concern changed from {old_concerns.get('cost')} to {new_concerns.get('cost')}")

@server.on_concerns_update()
def handle_concerns_update_sync(old_concerns, new_concerns):
    """同期関数でのコールバック（Context 不要）"""
    print(f"Concerns updated: {old_concerns} -> {new_concerns}")
```

### Concern 付きツールの定義

```python
@server.tool(
    name="encrypt_data",
    description="Encrypt sensitive data with high security",
    meta={
        "concerns": {
            "security": "high",
            "cost": "minimal",
            "performance": "low",
        }
    }
)
async def encrypt_data(data: str, ctx) -> str:
    """高セキュリティが必要なデータ暗号化ツール"""
    await ctx.info(f"Encrypting data with high security: {data[:50]}...")
    # 暗号化処理
    return f"encrypted_{data}"

@server.tool(
    name="log_data",
    description="Log data with basic security",
    meta={"concerns": {"security": "medium", "performance": "high"}}
)
async def log_data(data: str) -> str:
    """基本セキュリティのログ記録ツール"""
    return f"logged: {data}"

@server.tool(
    name="validate_data",
    description="Validate data without security concerns"
    # concern なし - すべての設定にマッチ
)
async def validate_data(data: str) -> str:
    """セキュリティ要件のないデータ検証ツール"""
    return f"validated: {data}"
```

### Concern 付きリソースの定義

```python
@server.resource(
    uri="resource://sensitive-data/{id}",
    name="sensitive_data",
    description="Access to sensitive data (high security required)",
    mime_type="application/json"
)
async def get_sensitive_data(id: str, ctx) -> str:
    """高セキュリティが必要なセンシティブデータリソース"""
    # concern は現時点ではリソースのメタデータとしてサポートされていませんが、
    # 将来的に追加される可能性があります
    return json.dumps({"id": id, "sensitive": True})

# リソースに concern を追加する場合（将来的なサポート）
resource = FunctionResource.from_function(
    fn=get_sensitive_data,
    uri="resource://sensitive-data/{id}",
    name="sensitive_data",
    meta={"concerns": {"security": "high"}}  # 将来的な機能
)
server.add_resource(resource)
```

### 完全な FastMCP サーバ例

```python
import asyncio
from mcp.server.fastmcp import FastMCP
import mcp.types as types

# FastMCP サーバの作成
server = FastMCP(
    name="concern-aware-server",
    instructions="This server demonstrates concern-based filtering",
    debug=True
)

# Concern の宣言
server.declare_concerns([
    types.ConcernDefinition(
        name="security",
        description="Security level required for operations",
        values=["high", "medium", "low"],
        default="medium"
    ),
    types.ConcernDefinition(
        name="cost",
        description="Cost impact of operations",
        values=["minimal", "moderate", "high"],
        default="moderate"
    ),
    types.ConcernDefinition(
        name="performance",
        description="Performance requirements",
        values=["high", "balanced", "low"],
        default="balanced"
    )
])

# Concern 更新コールバック
@server.on_concerns_update()
async def handle_concerns_update(ctx, old_concerns, new_concerns):
    if new_concerns:
        await ctx.info(f"Concerns updated: {new_concerns}")
    
    if new_concerns.get("security") == "high":
        await ctx.warning("High security mode enabled - some tools may be restricted")

# Concern 付きツール
@server.tool(
    meta={"concerns": {"security": "high", "cost": "minimal", "performance": "low"}}
)
async def encrypt_data(data: str, ctx) -> str:
    """High security encryption tool"""
    await ctx.info(f"Encrypting with high security: {data[:50]}...")
    return f"🔒{data}🔒"

@server.tool(
    meta={"concerns": {"security": "medium", "performance": "high"}}
)
async def process_data(data: str) -> str:
    """Medium security, high performance processing"""
    return f"Processed: {data.upper()}"

@server.tool()
async def validate_data(data: str) -> str:
    """No security concerns - always available"""
    if not data:
        return "Invalid: empty data"
    return f"Valid: {len(data)} characters"

# サーバの実行
if __name__ == "__main__":
    # stdio トランスポートで実行
    server.run(transport="stdio")
    
    # または HTTP トランスポートで実行
    # server.run(transport="streamable-http")
```

## クライアント側の使用方法

### Concern の一覧取得

```python
import asyncio
from mcp.client import Client

async def main():
    async with Client() as client:
        # サーバに接続
        await client.initialize()
        
        # Concern 定義の一覧取得
        concerns_result = await client.session.list_concerns()
        print("Server concerns:", concerns_result.concerns)
        
        # Concern 設定の更新
        await client.session.update_concerns({
            "security": "high",
            "cost": "minimal"
        })
        
        # ツール一覧の取得（フィルタリング済み）
        tools_result = await client.session.list_tools()
        print(f"Available tools with high security: {[t.name for t in tools_result.tools]}")

asyncio.run(main())
```

### Concern 設定の管理

クライアントはセッション中に concern 設定を動的に変更できます：

```python
# 初期設定
await session.update_concerns({"security": "medium"})

# ユーザー入力に基づいて設定を変更
user_security_preference = get_user_preference()  # "high", "medium", "low"
await session.update_concerns({"security": user_security_preference})

# 複数の concern を設定
await session.update_concerns({
    "security": "high",
    "cost": "minimal",
    "performance": "balanced"
})
```

## 実装例

### 例1: セキュリティレベルに基づくツールフィルタリング

```python
"""
セキュリティレベルに応じて利用可能なツールを制限する例
"""
import asyncio
import mcp.types as types
from mcp.server.lowlevel.server import Server
from mcp.server.stdio import stdio_server

server = Server("security-aware-server")

# セキュリティ concern の宣言
server.declare_concerns([
    types.ConcernDefinition(
        name="security",
        description="Required security level",
        values=["high", "medium", "low"],
        default="medium"
    )
])

# 様々なセキュリティレベルに対応したツール
tools = [
    types.Tool(
        name="read_public_data",
        description="Read publicly accessible data",
        inputSchema={"type": "object", "properties": {"query": {"type": "string"}}},
        meta={"concerns": {"security": "low"}}
    ),
    types.Tool(
        name="process_sensitive_data",
        description="Process sensitive data with medium security",
        inputSchema={"type": "object", "properties": {"data": {"type": "string"}}},
        meta={"concerns": {"security": "medium"}}
    ),
    types.Tool(
        name="encrypt_top_secret",
        description="Encrypt top secret data with high security",
        inputSchema={"type": "object", "properties": {"data": {"type": "string"}}},
        meta={"concerns": {"security": "high"}}
    )
]

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return tools

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=f"Executed {name}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

### 例2: 「*」を使用した柔軟なフィルタリング

```python
"""
「*」を使用して特定のconcernについて柔軟なマッチングを行う例
"""
import asyncio
import mcp.types as types
from mcp.server.lowlevel.server import Server
from mcp.server.stdio import stdio_server

server = Server("flexible-concern-server")

# 複数のconcernを宣言
server.declare_concerns([
    types.ConcernDefinition(
        name="security",
        description="Security level required",
        values=["high", "medium", "low"],
        default="medium"
    ),
    types.ConcernDefinition(
        name="cost",
        description="Cost impact",
        values=["minimal", "moderate", "high"],
        default="moderate"
    ),
    types.ConcernDefinition(
        name="performance",
        description="Performance requirements",
        values=["high", "balanced", "low"],
        default="balanced"
    )
])

# 様々なconcern設定を持つツール
tools = [
    types.Tool(
        name="free_fast_tool",
        description="Free and fast tool with low security",
        inputSchema={"type": "object", "properties": {"data": {"type": "string"}}},
        meta={"concerns": {"security": "low", "cost": "minimal", "performance": "high"}}
    ),
    types.Tool(
        name="secure_balanced_tool",
        description="Secure tool with balanced cost and performance",
        inputSchema={"type": "object", "properties": {"data": {"type": "string"}}},
        meta={"concerns": {"security": "high", "cost": "moderate", "performance": "balanced"}}
    ),
    types.Tool(
        name="expensive_high_perf_tool",
        description="Expensive high performance tool",
        inputSchema={"type": "object", "properties": {"data": {"type": "string"}}},
        meta={"concerns": {"security": "medium", "cost": "high", "performance": "high"}}
    ),
    types.Tool(
        name="no_cost_concern_tool",
        description="Tool without cost concern",
        inputSchema={"type": "object", "properties": {"data": {"type": "string"}}},
        meta={"concerns": {"security": "medium", "performance": "balanced"}}
        # cost concernが未設定 - すべてのcost設定にマッチ
    )
]

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return tools

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=f"Executed {name}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())

# クライアント側の使用例:
# 1. 高セキュリティ、コストは問わず、高パフォーマンスを要求
#    concerns_config = {"security": "high", "cost": "*", "performance": "high"}
#    → secure_balanced_tool のみ表示 (security=high, performance=balancedはperformance=highにマッチしない)
#
# 2. セキュリティは問わず、最小コスト、バランスドパフォーマンスを要求
#    concerns_config = {"security": "*", "cost": "minimal", "performance": "balanced"}
#    → free_fast_tool のみ表示 (performance=highはbalancedにマッチしない)
#
# 3. 中セキュリティ、高コスト、高パフォーマンスを要求
#    concerns_config = {"security": "medium", "cost": "high", "performance": "high"}
#    → expensive_high_perf_tool のみ表示
```

## ベストプラクティスと注意点

### ConcernDefinitionの設計

1. **値の粒度**: concernのvaluesは適切な粒度で設計してください。細かすぎると管理が難しくなり、粗すぎると効果的なフィルタリングができません。
2. **デフォルト値**: 必ずdefault値を設定し、クライアントが明示的に設定しない場合の挙動を明確にします。
3. **説明文**: descriptionフィールドを活用し、各concernの目的と値の意味を明確に文書化します。

### ConcernConfigurationの使用

1. **「*」の活用**: 特定のconcernについて厳密な要件がない場合は「*」を使用し、柔軟なマッチングを可能にします。
2. **部分的な設定**: すべてのconcernを設定する必要はありません。設定されていないconcernについては、プリミティブにそのconcernの設定がなければマッチします。
3. **動的更新**: セッション中にconcern設定を動的に更新し、ユーザーのニーズやコンテキストに応じて利用可能な機能を調整できます。

### パフォーマンス考慮事項

1. **Concernマップのキャッシュ**: `create_concerns_map_from_primitives()`の結果をキャッシュし、繰り返し計算を避けます。
2. **プリミティブ数の管理**: 大量のプリミティブがある場合、concernベースのフィルタリングはパフォーマンスに影響する可能性があります。必要に応じてインデックス化を検討してください。
3. **非同期処理**: 大規模なフィルタリング操作は非同期で実行することを検討してください。

### デバッグとテスト

1. **ロギング**: concernのマッチングロジックに詳細なロギングを追加し、フィルタリング動作をデバッグしやすくします。
2. **単体テスト**: `filter_by_concerns()`関数の単体テストを作成し、様々なconcern設定での挙動を検証します。
3. **統合テスト**: 実際のサーバ環境でのconcernベースフィルタリングの動作をテストします。

### 互換性と移行

1. **後方互換性**: concernを追加する際は、既存のプリミティブが引き続き動作することを確認します。
2. **段階的導入**: 大規模なシステムでは、concernベースフィルタリングを段階的に導入することを検討します。
3. **フォールバック**: concern設定が提供されない場合のデフォルト動作を明確に定義します。
