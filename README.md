# PostgreSQL MCP Server

A Model Context Protocol (MCP) server for PostgreSQL database operations. This server provides AI assistants with the ability to perform CRUD operations and manage PostgreSQL databases through a standardized interface.

**Project Status**: ✅ **COMPLETED** - Fully implemented, tested, and published to PyPI

## Features

- **Entity CRUD Operations**: Create, read, update, and delete entities in PostgreSQL tables
- **Dynamic Table Support**: Work with any table in your database without pre-configuration
- **Secure Connection Management**: Environment variable-based configuration with validation
- **Parameterized Queries**: Protection against SQL injection attacks
- **Flexible Querying**: Support for complex conditions and result limiting
- **Table Management**: Create, alter, and drop tables dynamically
- **Schema Information**: Get detailed table schemas and database metadata
- **Comprehensive Testing**: Unit tests, integration tests, and Docker test environment

## Available Tools

### CRUD Operations
- `create_entity`: Insert new rows into tables
- `read_entity`: Query tables with optional conditions
- `update_entity`: Update existing rows based on conditions
- `delete_entity`: Remove rows from tables

### Table Management Operations
- `create_table`: Create new tables with specified schema
- `alter_table`: Modify existing table structures
- `drop_table`: Remove tables from database

### Schema Operations
- `get_tables`: Get list of all tables in the database
- `get_table_schema`: Get detailed schema information for a specific table
- `get_database_info`: Get database metadata and version information

## Available Resources

### Database Resources
- `database://tables`: List of all tables in the database
- `database://info`: Database metadata and version information
- `database://schema/{table_name}`: Schema information for specific tables

## Project Configuration (pyproject.toml)

This project uses the `pyproject.toml` file for configuration management. This is the latest Python package management standard that provides the following features:

### Main Configuration Sections

**Project Basic Information:**
- Package name: `mcp-postgres-duwenji`
- Version: `1.2.1`
- Required Python version: `>=3.10`

**Dependency Management:**
- **Required dependencies**: MCP protocol, PostgreSQL connection, configuration management, etc.
- **Development dependencies**: Testing, linting, formatting tools, etc.

**Build System:**
- **uv build**: Fast package building and dependency resolution
- **Entry point**: `mcp_postgres_duwenji` command to start the server

**Development Tool Configuration:**
- **Black**: Automatic code formatting (88 characters per line)
- **Mypy**: Strict type checking
- **Pytest**: Test framework
- **Flake8**: Code quality checking

### Practical Usage

```bash
# Install dependencies
uv sync --group dev

# Start server
uv run mcp_postgres_duwenji

# Run tests
uv run pytest

# Code formatting
uv run black src/

# Type checking
uv run mypy src/
```

## Quick Start

### Prerequisites

- Python 3.10 or higher
- PostgreSQL database (version 12 or higher)
- [uv](https://github.com/astral-sh/uv) package manager (latest version)

### Installation

1. **Install from PyPI**:
   ```bash
   uvx mcp-postgres-duwenji
   ```

2. **Configure your MCP client** (e.g., Claude Desktop):
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

   **Docker Automatic Setup Configuration**:

   For automatic PostgreSQL Docker container setup, use the following configuration:

   ```json
   {
     "mcpServers": {
       "postgres-mcp": {
         "disabled": false,
         "timeout": 60,
         "type": "stdio",
         "command": "uvx",
         "args": ["mcp-postgres-duwenji"],
         "env": {
           "MCP_DOCKER_AUTO_SETUP": "true",
           "MCP_DOCKER_IMAGE": "postgres:16",
           "MCP_DOCKER_CONTAINER_NAME": "mcp-postgres-auto",
           "MCP_DOCKER_PORT": "5432",
           "MCP_DOCKER_DATA_VOLUME": "mcp_postgres_data",
           "MCP_DOCKER_PASSWORD": "postgres",
           "MCP_DOCKER_DATABASE": "mcp-postgres-db",
           "MCP_DOCKER_USERNAME": "postgres",
           "MCP_DOCKER_MAX_WAIT_TIME": "30",
           "MCP_LOG_LEVEL": "INFO",
           "MCP_DEBUG": "true"
         }
       }
     }
   }
   ```

   This configuration will automatically:
   - Start a PostgreSQL Docker container when the MCP server starts
   - Use the specified Docker image (postgres:16)
   - Create a persistent data volume for data storage
   - Set up the database with the specified credentials
   - Enable debug logging for troubleshooting

   For detailed Docker setup instructions, see [Docker Auto Setup Guide](docs/docker-auto-setup-guide.md).



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
│           ├── schema_tools.py   # Schema operation tools
│           └── table_tools.py    # Table management tools
├── test/                         # Testing related
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   ├── docker/                   # Docker test environment
│   └── docs/                     # Test documentation
├── docs/                         # Project documentation
│   ├── code-quality-checks-guide.md      # Code quality tools guide
│   ├── linting-and-type-checking-guide.md # Linting and type checking guide
│   ├── pypi-publishing-guide.md          # PyPI publishing guide
│   └── github/                           # GitHub workflows and guides
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

### Code Quality Tools

This project uses comprehensive code quality tools:

- **Black**: Code formatting
- **Flake8**: Linting and style checking
- **MyPy**: Static type checking
- **Bandit**: Security scanning

See `docs/code-quality-checks-guide.md` and `docs/linting-and-type-checking-guide.md` for detailed usage instructions.

### Adding New Tools

1. Create a new tool definition in `src/mcp_postgres_duwenji/tools/`
2. Add the tool handler function
3. Register the tool in the appropriate handler function
4. The tool will be automatically available through the MCP interface

## Security Considerations

- Always use environment variables for sensitive connection information
- The server uses parameterized queries to prevent SQL injection
- Limit database user permissions to only necessary operations
- Consider using SSL/TLS for database connections in production

## License

Apache 2.0
