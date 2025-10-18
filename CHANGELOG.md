# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure and MCP server implementation
- Basic database connection management
- CRUD operation tools for PostgreSQL
- Configuration management with environment variables
- Comprehensive test environment setup

### Changed
- Package name from `mcp-postgres` to `mcp-postgres-duwenji` for PyPI compatibility
- Source directory structure to `src/mcp_postgres_duwenji/`
- Build system from hatchling to uv_build

### Fixed
- 403 Forbidden error during PyPI upload by using unique package name

## [1.0.0] - 2025-10-18

### Initial Release
- First version released on PyPI
- Basic MCP server structure
- PostgreSQL connection capabilities
- CRUD operation tools
- Configuration system

[Unreleased]: https://github.com/duwenji/mcp-postgres/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/duwenji/mcp-postgres/releases/tag/v1.0.1
[1.0.0]: https://github.com/duwenji/mcp-postgres/releases/tag/v1.0.0

## [1.0.1] - 2025-10-18

### Added
- Initial PyPI release with basic PostgreSQL MCP server functionality
- CRUD operations: create_entity, read_entity, update_entity, delete_entity
- Dynamic table support without pre-configuration
- Secure connection management with environment variables
- Parameterized queries for SQL injection protection

### Technical
- Python 3.10+ compatibility
- psycopg2-binary for PostgreSQL connectivity
- Pydantic for configuration validation
- MCP protocol implementation
- uv package manager support