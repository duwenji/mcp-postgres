# PostgreSQL MCP Server

A Model Context Protocol (MCP) server for PostgreSQL database operations. This server provides AI assistants with the ability to perform CRUD operations and manage PostgreSQL databases through a standardized interface.

## Features

- **Entity CRUD Operations**: Create, read, update, and delete entities in PostgreSQL tables
- **Dynamic Table Support**: Work with any table in your database without pre-configuration
- **Secure Connection Management**: Environment variable-based configuration with validation
- **Parameterized Queries**: Protection against SQL injection attacks
- **Flexible Querying**: Support for complex conditions and result limiting

## Available Tools

### CRUD Operations
- `create_entity`: Insert new rows into tables
- `read_entity`: Query tables with optional conditions
- `update_entity`: Update existing rows based on conditions
- `delete_entity`: Remove rows from tables

### Schema Operations
- `get_tables`: Get list of all tables in the database
- `get_table_schema`: Get detailed schema information for a specific table
- `get_database_info`: Get database metadata and version information

## Available Resources

### Database Resources
- `database://tables`: List of all tables in the database
- `database://info`: Database metadata and version information
- `database://schema/{table_name}`: Schema information for specific tables

## Quick Start

### Prerequisites

- Python 3.10 or higher
- PostgreSQL database (version 12 or higher)
- [uv](https://github.com/astral-sh/uv) package manager (latest version)

### Installation

1. **Configure your MCP client** (e.g., Claude Desktop):
   Add the server configuration to your MCP client settings using `uvx`:

   **Claude Desktop Configuration Example**:
   ```json
   {
     "mcpServers": {
       "postgres-mcp": {
         "command": "uvx",
         "args": ["mcp-postgres-duwenji"],
         "env": {
           "POSTGRES_HOST": "localhost",
           "POSTGRES_PORT": "5432",
           "POSTGRES_DB": "your_database",
           "POSTGRES_USER": "your_username",
           "POSTGRES_PASSWORD": "your_password",
           "POSTGRES_SSL_MODE": "prefer"
         }
       }
     }
   }
   ```



### Usage Examples

Once configured, you can use the MCP tools through your AI assistant:

**Create a new user**:
```json
{
  "table_name": "users",
  "data": {
    "name": "John Doe",
    "email": "john@example.com",
    "age": 30
  }
}
```

**Read users with conditions**:
```json
{
  "table_name": "users",
  "conditions": {
    "age": 30
  },
  "limit": 10
}
```

**Update user information**:
```json
{
  "table_name": "users",
  "conditions": {
    "id": 1
  },
  "updates": {
    "email": "newemail@example.com"
  }
}
```

**Delete users**:
```json
{
  "table_name": "users",
  "conditions": {
    "id": 1
  }
}
```

## Development

### Project Structure

```
mcp-postgres/
├── src/
│   └── mcp_postgres_duwenji/     # Main package
│       ├── __init__.py           # Package initialization
│       ├── main.py               # MCP server entry point
│       ├── config.py             # Configuration management
│       ├── database.py           # Database connection and operations
│       ├── resources.py          # Resource management
│       └── tools/                # MCP tool definitions
│           ├── __init__.py
│           ├── crud_tools.py     # CRUD operation tools
│           └── schema_tools.py   # Schema operation tools
├── test/                         # Testing related
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   ├── docker/                   # Docker test environment
│   └── docs/                     # Test documentation
├── docs/                         # Project documentation
├── examples/                     # Configuration examples
├── scripts/                      # Utility scripts
├── memory-bank/                  # Project memory bank
├── pyproject.toml                # Project configuration and dependencies
├── uv.lock                       # uv dependency lock file
├── .env.example                  # Environment variables template
├── README.md                     # English README
└── README_ja.md                  # Japanese README
```

### Running the Server

To run the server directly for testing:

```bash
uvx mcp-postgres-duwenji
```

### Adding New Tools

1. Create a new tool definition in `src/mcp_postgres_duwenji/tools/`
2. Add the tool handler function
3. Register the tool in `get_crud_tools()` and `get_crud_handlers()`
4. The tool will be automatically available through the MCP interface

## Security Considerations

- Always use environment variables for sensitive connection information
- The server uses parameterized queries to prevent SQL injection
- Limit database user permissions to only necessary operations
- Consider using SSL/TLS for database connections in production

## License

Apache 2.0
