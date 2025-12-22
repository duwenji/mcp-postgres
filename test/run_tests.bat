@echo off
REM PostgreSQL MCP Server Test Runner Script for Windows

echo === PostgreSQL MCP Server Test Runner ===

REM Check for help options first
if "%1"=="--help" goto help
if "%1"=="-h" goto help

REM Main execution logic
setlocal enabledelayedexpansion

REM Set default test type
set TEST_TYPE=all
if not "%1"=="" set TEST_TYPE=%1

if "%TEST_TYPE%"=="unit" (
    echo [INFO] Running unit tests only...
    uv run python -m pytest test/unit/ -v --tb=short --cov=src --cov-report=term-missing
    exit /b 0
) else if "%TEST_TYPE%"=="integration" (
    echo [INFO] Running integration tests only...
    echo [INFO] Note: Integration tests require a running PostgreSQL database
    echo [INFO] Setting RUN_INTEGRATION_TESTS=1
    set RUN_INTEGRATION_TESTS=1
    uv run python -m pytest test/integration/ -v --tb=short
    exit /b 0
) else if "%TEST_TYPE%"=="all" (
    echo [INFO] Running unit tests...
    uv run python -m pytest test/unit/ -v --tb=short --cov=src --cov-report=term-missing
    echo.
    echo [INFO] Running integration tests...
    echo [INFO] Note: Integration tests require a running PostgreSQL database
    echo [INFO] Setting RUN_INTEGRATION_TESTS=1
    set RUN_INTEGRATION_TESTS=1
    uv run python -m pytest test/integration/ -v --tb=short
    exit /b 0
) else (
    echo [ERROR] Unknown test type: %TEST_TYPE%
    goto help
)

exit /b 0

:help
echo Usage: %0 [test_type]
echo.
echo Available test types:
echo   unit        - Run unit tests only
echo   integration - Run integration tests only (requires PostgreSQL)
echo   all         - Run all tests ^(default^)
echo.
echo Examples:
echo   %0 unit        # Run only unit tests
echo   %0 integration # Run only integration tests
echo   %0 all         # Run all tests
echo   %0             # Run all tests (default)
echo.
echo Integration Test Requirements:
echo   1. PostgreSQL database running on localhost:5432
echo   2. Test database: mcp_test_db
echo   3. Test user: test_user with password: test_password
echo   4. User must have SUPERUSER privileges
exit /b 0
