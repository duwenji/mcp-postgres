"""
Pytest configuration for PostgreSQL MCP Server tests
"""

import os
import sys
import pytest
import asyncio
from typing import Dict, Any

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

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
    for key in [
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_SSL_MODE",
    ]:
        original_env[key] = os.environ.get(key)

    yield

    # Restore original environment
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


@pytest.fixture(scope="session")
def clean_test_database(test_database_config):
    """Clean test database before running tests."""
    import sys
    import os

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
    from mcp_postgres_duwenji.database import DatabaseManager
    from mcp_postgres_duwenji.config import PostgresConfig

    config = PostgresConfig(**test_database_config)
    manager = DatabaseManager(config)

    try:
        # Connect to database
        manager.connection.connect()

        # Clean test data
        print("Cleaning test database...")

        # Delete test data in reverse order to respect foreign key constraints
        manager.connection.execute_query("DELETE FROM orders")
        manager.connection.execute_query("DELETE FROM products")
        manager.connection.execute_query("DELETE FROM users")

        # Reset sequences
        manager.connection.execute_query("ALTER SEQUENCE users_id_seq RESTART WITH 1")
        manager.connection.execute_query(
            "ALTER SEQUENCE products_id_seq RESTART WITH 1"
        )
        manager.connection.execute_query("ALTER SEQUENCE orders_id_seq RESTART WITH 1")

        print("Test database cleaned successfully")

    except Exception as e:
        print(f"Warning: Could not clean test database: {e}")
    finally:
        manager.connection.disconnect()


def pytest_configure(config):
    """Configure pytest."""
    import sys
    import os

    # Add src directory to Python path for imports
    src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires database)"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test (no external dependencies)"
    )
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config, items):
    """Modify test items based on markers and environment."""
    skip_integration = pytest.mark.skip(reason="integration tests require database")
    skip_slow = pytest.mark.skip(reason="slow test skipped by default")

    for item in items:
        if "integration" in item.keywords and not os.getenv("RUN_INTEGRATION_TESTS"):
            item.add_marker(skip_integration)
        if "slow" in item.keywords and not os.getenv("RUN_SLOW_TESTS"):
            item.add_marker(skip_slow)
