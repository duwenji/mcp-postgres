# PostgreSQL MCP Server

A Model Context Protocol (MCP) server for PostgreSQL database operations. Provides AI assistants with standardized CRUD operations and database management capabilities.

**Status**: ✅ **COMPLETED** - Fully implemented, tested, and published to PyPI

## Features

- **CRUD Operations**: Create, read, update, and delete entities
- **Dynamic Table Support**: Work with any table without pre-configuration
- **Secure Connections**: Environment variable-based configuration with validation
- **Parameterized Queries**: SQL injection protection
- **Table Management**: Create, alter, and drop tables
- **Schema Information**: Detailed table schemas and database metadata
- **Comprehensive Testing**: Unit, integration, and Docker tests

## Available Tools

### CRUD Operations
- `create_entity`: Insert new rows into tables
- `read_entity`: Query tables with optional conditions
- `update_entity`: Update existing rows based on conditions
- `delete_entity`: Remove rows from tables
- `execute_sql_query`: Execute arbitrary SQL queries and return results

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
- `database://connection`: Database connection parameters (host, port, database, username, password, etc.)
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
           "POSTGRES_SSL_MODE": "prefer",
           "MCP_LOG_LEVEL": "INFO",
           "MCP_PROTOCOL_DEBUG": "true",
           "MCP_LOG_DIR": "C:\\Logs\\mcp-postgres"
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
           "MCP_PROTOCOL_DEBUG": "true",
           "MCP_LOG_DIR": "C:\\Logs\\mcp-postgres"
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
   - **Enable external access** (listen on all interfaces)
   - Enable debug logging for troubleshooting

   For detailed Docker setup instructions, see [Docker Auto Setup Guide](docs/docker-auto-setup-guide.md).

### External Program Access

When using Docker auto-setup, the PostgreSQL container is configured to allow external connections:
- **Listen address**: `*` (all interfaces)
- **Port**: Configurable via `MCP_DOCKER_PORT` (default: 5432)
- **Authentication**: Password-based authentication

External Python programs can use the connection information from the `database://connection` resource to connect directly to the PostgreSQL database.

## Configuration

### Environment Variables

The PostgreSQL MCP Server supports the following environment variables for configuration:

#### Database Connection Variables
- `POSTGRES_HOST`: PostgreSQL server hostname (default: localhost)
- `POSTGRES_PORT`: PostgreSQL server port (default: 5432)
- `POSTGRES_DB`: Database name (required)
- `POSTGRES_USER`: Database username (required)
- `POSTGRES_PASSWORD`: Database password (required)
- `POSTGRES_SSL_MODE`: SSL mode (default: prefer)

#### Docker Auto-Setup Variables
- `MCP_DOCKER_AUTO_SETUP`: Enable automatic Docker setup (true/false, default: false)
- `MCP_DOCKER_IMAGE`: PostgreSQL Docker image (default: postgres:16)
- `MCP_DOCKER_CONTAINER_NAME`: Docker container name (default: mcp-postgres-auto)
- `MCP_DOCKER_PORT`: Docker container port (default: 5432)
- `MCP_DOCKER_DATA_VOLUME`: Data volume name (default: mcp_postgres_data)
- `MCP_DOCKER_PASSWORD`: Database password for Docker setup (default: postgres)
- `MCP_DOCKER_DATABASE`: Database name for Docker setup (default: mcp-postgres-db)
- `MCP_DOCKER_USERNAME`: Database username for Docker setup (default: postgres)
- `MCP_DOCKER_MAX_WAIT_TIME`: Maximum wait time for container startup in seconds (default: 30)

#### Performance Monitoring Variables
- `MCP_SLOW_QUERY_THRESHOLD_MS`: Slow query threshold in milliseconds (default: 1000)
- `MCP_ENABLE_AUTO_EXPLAIN`: Enable auto_explain extension for query plan logging (true/false, default: true)

#### Logging and Debug Variables
- `MCP_LOG_LEVEL`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL, default: INFO)
- `MCP_PROTOCOL_DEBUG`: Enable MCP protocol debug logging (true/false, default: false)

### Environment Variable Usage Examples

#### Using .env File
Create a `.env` file in your project directory:

```bash
# Database Connection
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=my_database
POSTGRES_USER=my_username
POSTGRES_PASSWORD=my_password
POSTGRES_SSL_MODE=prefer

# Docker Auto-Setup
MCP_DOCKER_AUTO_SETUP=false
MCP_DOCKER_IMAGE=postgres:16
MCP_DOCKER_CONTAINER_NAME=mcp-postgres-auto
MCP_DOCKER_PORT=5432
MCP_DOCKER_DATA_VOLUME=mcp_postgres_data
MCP_DOCKER_PASSWORD=postgres
MCP_DOCKER_DATABASE=mcp-postgres-db
MCP_DOCKER_USERNAME=postgres
MCP_DOCKER_MAX_WAIT_TIME=30

# Performance Monitoring
MCP_SLOW_QUERY_THRESHOLD_MS=1000
MCP_ENABLE_AUTO_EXPLAIN=true

# Logging
MCP_LOG_LEVEL=INFO
MCP_PROTOCOL_DEBUG=false
```

#### Using System Environment Variables
Set environment variables directly in your shell:

```bash
# Windows PowerShell
$env:POSTGRES_HOST="localhost"
$env:POSTGRES_DB="my_database"
$env:POSTGRES_USER="my_username"
$env:POSTGRES_PASSWORD="my_password"

# Linux/macOS
export POSTGRES_HOST=localhost
export POSTGRES_DB=my_database
export POSTGRES_USER=my_username
export POSTGRES_PASSWORD=my_password
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

**Execute custom SQL query**:
```json
{
  "query": "SELECT u.name, COUNT(o.id) as order_count FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id, u.name HAVING COUNT(o.id) > 5",
  "limit": 100
}
```

**Execute parameterized SQL query**:
```json
{
  "query": "SELECT * FROM users WHERE age > %(min_age)s AND created_at > %(start_date)s",
  "params": {
    "min_age": 18,
    "start_date": "2024-01-01"
  },
  "limit": 50
}
```

## Development

### Project Structure

```
mcp-postgres/
├── src/mcp_postgres_duwenji/     # Main package
├── test/                         # Testing
├── docs/                         # Documentation
├── scripts/                      # Utility scripts
├── memory-bank/                  # Project memory bank
├── pyproject.toml                # Project configuration
└── README.md                     # English README
```

### Running the Server

To run the server directly for testing:

```bash
uvx mcp-postgres-duwenji
```

**Direct Execution with Environment Variables**:

You can also run the server directly with environment variables:

```bash
# Using .env file
uvx mcp-postgres-duwenji

# Using command-line environment variables (Linux/macOS)
POSTGRES_HOST=localhost POSTGRES_DB=my_database POSTGRES_USER=my_username POSTGRES_PASSWORD=my_password uvx mcp-postgres-duwenji

# Using command-line environment variables (Windows PowerShell)
$env:POSTGRES_HOST="localhost"; $env:POSTGRES_DB="my_database"; $env:POSTGRES_USER="my_username"; $env:POSTGRES_PASSWORD="my_password"; uvx mcp-postgres-duwenji
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
