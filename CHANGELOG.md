# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Context-based Resource Management**: New `AppContext` class for centralized resource lifecycle management
- **Improved Lifespan Management**: Complete rewrite of `lifespan` function to handle resource initialization and cleanup
- **Type-safe Resource Access**: All server resources now accessed through context with proper type hints

### Changed
- **Global Variables Removal**: Eliminated `global_config`, `logger`, `global_pool_manager` global variables
- **Resource Initialization**: Moved resource initialization from `main()` to `lifespan` context manager
- **Shared Module Update**: Updated `shared.py` to support both context-based and legacy global variable access
- **Tool Handler Compatibility**: Maintained backward compatibility for all tool handlers

### Fixed
- **Resource Lifecycle**: Proper resource cleanup during server shutdown
- **Dependency Injection**: Improved testability through explicit resource passing
- **Code Organization**: Better separation of concerns with dedicated context module

## [1.1.0] - 2025-10-19

### Added
- **Table Management Tools**: Complete implementation of table creation, alteration, and deletion tools
  - `create_table`: Create new tables with column definitions
  - `alter_table`: Modify table structure (add/drop/rename/alter columns)
  - `drop_table`: Delete tables from database
- **Enhanced Schema Tools**: Improved database schema information retrieval
  - `get_table_schema`: Detailed table structure with constraints
  - `get_database_info`: Comprehensive database metadata
- **Comprehensive Testing Environment**: Full test suite implementation
  - Unit tests for configuration management
  - Integration tests for database operations
  - Docker-based test infrastructure
- **Memory Bank Documentation**: Complete project documentation system

### Changed
- **Package Name**: Renamed from `mcp-postgres` to `mcp-postgres-duwenji` for PyPI compatibility
- **Source Directory**: Updated from `src/mcp_postgres` to `src/mcp_postgres_duwenji`
- **Build System**: Migrated from hatchling to uv_build for improved packaging
- **Error Handling**: Enhanced error handling with detailed messages and logging

### Fixed
- **GitHub Actions**: Resolved flake8 execution errors in CI/CD pipeline
- **Security**: Implemented comprehensive SQL injection protection
- **Connection Pooling**: Optimized database connection management
- **Schema Information**: Fixed dynamic resource generation for table schemas

## [1.0.1] - 2025-10-18

### Fixed
- Package distribution issues and metadata corrections

## [1.0.0] - 2025-10-18

### Initial Release
- First version released on PyPI
- Basic MCP server structure
- PostgreSQL connection capabilities
- CRUD operation tools
- Configuration system

[Unreleased]: https://github.com/duwenji/mcp-postgres/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/duwenji/mcp-postgres/releases/tag/v1.1.0
[1.0.1]: https://github.com/duwenji/mcp-postgres/releases/tag/v1.0.1
[1.0.0]: https://github.com/duwenji/mcp-postgres/releases/tag/v1.0.0
