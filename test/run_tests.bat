@echo off
REM PostgreSQL MCP Server Test Runner Script for Windows

echo === PostgreSQL MCP Server Test Runner ===

REM Check for help options first
if "%1"=="--help" goto help
if "%1"=="-h" goto help

REM Main execution logic
setlocal enabledelayedexpansion

echo [INFO] Running unit tests...
uv run python -m pytest test/unit/ -v --tb=short --cov=src --cov-report=term-missing
exit /b 0

:help
echo Usage: %0 [test_type]
echo.
echo Available test types:
echo   unit        - Run unit tests only
echo   all         - Run all tests ^(default^)
echo.
echo Examples:
echo   %0 unit        # Run only unit tests
echo   %0             # Run all tests
exit /b 0
