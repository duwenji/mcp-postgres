# シンプル設定ガイド

このガイドでは、PostgreSQL MCPサーバを最も簡単に設定する方法を説明します。

## 方法1: PyPIからのインストール（推奨）

### 前提条件
- Python 3.10以上
- Clineまたは他のMCPクライアント

## UV指定での直接実行

### UVで直接実行 + 環境変数指定
```json
{
  "mcpServers": {
    "postgres": {
      "command": "uv",
      "args": ["run", "mcp-postgres-duwenji"],
      "env": {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_DB": "myapp",
        "POSTGRES_USER": "myuser",
        "POSTGRES_PASSWORD": "mypassword",
        "POSTGRES_SSL_MODE": "prefer",
        "POSTGRES_POOL_SIZE": "5",
        "POSTGRES_MAX_OVERFLOW": "10"
      }
    }
  }
}
```

### UV + 環境変数ファイル
```json
{
  "mcpServers": {
    "postgres": {
      "command": "uv",
      "args": ["run", "mcp-postgres-duwenji"],
      "envFile": "~/.mcp-postgres.env"
    }
  }
}
```
