@echo off
REM PostgreSQL MCP Server Test Runner Script for Windows

echo === PostgreSQL MCP Server Test Runner ===

REM Function to run unit tests
:run_unit_tests
echo [INFO] Running unit tests...
python -m pytest test/unit/ -v --tb=short --cov=src --cov-report=term-missing
goto :eof

REM Function to run integration tests
:run_integration_tests
echo [INFO] Running integration tests...
set RUN_INTEGRATION_TESTS=1
python -m pytest test/integration/ -v --tb=short -m integration
set RUN_INTEGRATION_TESTS=
goto :eof

REM Function to check Docker availability
:check_docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed or not in PATH
    exit /b 1
)

docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose is not installed or not in PATH
    exit /b 1
)

echo [SUCCESS] Docker and Docker Compose are available
goto :eof

REM Function to run all tests with Docker
:run_docker_tests
echo [INFO] Starting Docker test environment...
cd test\docker

REM Build and start services
docker-compose -f docker-compose.test.yml up --build -d

REM Wait for PostgreSQL to be ready
echo [INFO] Waiting for PostgreSQL to be ready...
timeout /t 10 /nobreak >nul

REM Run tests
echo [INFO] Running tests in Docker container...
docker-compose -f docker-compose.test.yml run --rm test-runner

REM Stop services
echo [INFO] Stopping Docker services...
docker-compose -f docker-compose.test.yml down

cd ..\..
goto :eof

REM Main execution
:main
setlocal enabledelayedexpansion

set "test_type=%~1"
if "%test_type%"=="" set "test_type=all"

echo [INFO] Test type: %test_type%

if "%test_type%"=="docker" (
    call :check_docker
    call :run_docker_tests
) else if "%test_type%"=="unit" (
    call :run_unit_tests
) else if "%test_type%"=="integration" (
    call :check_docker
    call :run_integration_tests
) else if "%test_type%"=="all" (
    call :check_docker
    call :run_unit_tests
    call :run_integration_tests
) else (
    echo [ERROR] Unknown test type: %test_type%
    echo [INFO] Available types: unit, integration, docker, all
    exit /b 1
)

echo [SUCCESS] Test execution completed!
goto :eof

REM Handle help
if "%1"=="--help" (
    echo Usage: %0 [test_type]
    echo.
    echo Available test types:
    echo   unit        - Run unit tests only
    echo   integration - Run integration tests only
    echo   docker      - Run all tests in Docker environment
    echo   all         - Run all tests ^(default^)
    echo.
    echo Examples:
    echo   %0 unit        # Run only unit tests
    echo   %0 integration # Run only integration tests
    echo   %0 docker      # Run tests in Docker
    echo   %0             # Run all tests
    exit /b 0
)

if "%1"=="-h" (
    call :help
    exit /b 0
)

REM Run main function
call :main %1
