"""
Pytest configuration for PostgreSQL MCP Server tests
"""
import os
import pytest
import asyncio
from typing import AsyncGenerator, Dict, Any

# Configure test environment
os.environ["POSTGRES_HOST"] = os.getenv("POSTGRES_HOST", "localhost")
os.environ["POSTGRES_PORT"] = os.getenv("POSTGRES_PORT", "5433")
os.environ["POSTGRES_DB"] = os.getenv("POSTGRES_DB", "mcp_test_db")
os.environ["POSTGRES_USER"] = os.getenv("POSTGRES_USER", "test_user")
os.environ["POSTGRES_PASSWORD"] = os.getenv("POSTGRES_PASSWORD", "test_password")
os.environ["POSTGRES_SSL_MODE"] = os.getenv("POSTGRES_SSL_MODE", "disable")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_database_config() -> Dict[str, Any]:
    """Provide test database configuration."""
    return {
        "host": os.environ["POSTGRES_HOST"],
        "port": int(os.environ["POSTGRES_PORT"]),
        "database": os.environ["POSTGRES_DB"],
        "username": os.environ["POSTGRES_USER"],
        "password": os.environ["POSTGRES_PASSWORD"],
        "ssl_mode": os.environ["POSTGRES_SSL_MODE"],
    }


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test."""
    # Ensure test environment variables are set
    original_env = {}
    for key in ["POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB", 
                "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_SSL_MODE"]:
        original_env[key] = os.environ.get(key)
    
    yield
    
    # Restore original environment
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires database)"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test (no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test items based on markers and environment."""
    skip_integration = pytest.mark.skip(reason="integration tests require database")
    skip_slow = pytest.mark.skip(reason="slow test skipped by default")
    
    for item in items:
        if "integration" in item.keywords and not os.getenv("RUN_INTEGRATION_TESTS"):
            item.add_marker(skip_integration)
        if "slow" in item.keywords and not os.getenv("RUN_SLOW_TESTS"):
            item.add_marker(skip_slow)
