"""
Integration tests for database operations
"""

import os
import sys
import pytest
import asyncio

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from mcp_postgres_duwenji.config import PostgresConfig, load_config
from mcp_postgres_duwenji.database import (
    DatabaseManager,
    DatabaseConnection,
    DatabaseError,
)


@pytest.mark.integration
class TestDatabaseConnection:
    """Test database connection functionality"""

    def test_connection_success(self, test_database_config):
        """Test successful database connection"""
        config = PostgresConfig(**test_database_config)
        connection = DatabaseConnection(config)

        # Test connection
        result = connection.test_connection()
        assert result is True

    def test_connection_failure(self):
        """Test database connection failure with invalid config"""
        config = PostgresConfig(
            host="invalid-host",
            port=5432,
            database="invalid-db",
            username="invalid-user",
            password="invalid-pass",
        )
        connection = DatabaseConnection(config)

        # Test connection should fail
        result = connection.test_connection()
        assert result is False


@pytest.mark.integration
class TestDatabaseCRUD:
    """Test CRUD operations"""

    @pytest.fixture
    def db_manager(self, test_database_config, clean_test_database):
        """Create database manager for tests"""
        config = PostgresConfig(**test_database_config)
        manager = DatabaseManager(config)
        # Ensure connection is established
        manager.connection.connect()
        yield manager
        # Cleanup
        manager.connection.disconnect()

    def test_create_user(self, db_manager):
        """Test creating a new user"""
        user_data = {"username": "test_create_user", "email": "test_create@example.com"}

        result = db_manager.create_entity("users", user_data)

        assert result["success"] is True
        assert "created" in result
        assert result["created"]["username"] == "test_create_user"
        assert result["created"]["email"] == "test_create@example.com"

    def test_read_users(self, db_manager):
        """Test reading users from database"""
        result = db_manager.read_entity("users", limit=5)

        assert result["success"] is True
        assert "results" in result
        assert "count" in result
        assert isinstance(result["results"], list)
        assert result["count"] <= 5

    def test_read_users_with_conditions(self, db_manager):
        """Test reading users with specific conditions"""
        # First create a test user
        user_data = {
            "username": "test_condition_user",
            "email": "test_condition@example.com",
        }
        db_manager.create_entity("users", user_data)

        # Read with condition
        conditions = {"username": "test_condition_user"}
        result = db_manager.read_entity("users", conditions=conditions)

        assert result["success"] is True
        assert result["count"] >= 1
        assert result["results"][0]["username"] == "test_condition_user"

    def test_update_user(self, db_manager):
        """Test updating a user"""
        # First create a test user
        user_data = {"username": "test_update_user", "email": "test_update@example.com"}
        create_result = db_manager.create_entity("users", user_data)
        user_id = create_result["created"]["id"]

        # Update the user
        conditions = {"id": user_id}
        updates = {"email": "updated@example.com"}
        update_result = db_manager.update_entity("users", conditions, updates)

        assert update_result["success"] is True
        assert update_result["updated"]["email"] == "updated@example.com"
        assert update_result["affected_rows"] == 1

    def test_delete_user(self, db_manager):
        """Test deleting a user"""
        # First create a test user
        user_data = {"username": "test_delete_user", "email": "test_delete@example.com"}
        create_result = db_manager.create_entity("users", user_data)
        user_id = create_result["created"]["id"]

        # Delete the user
        conditions = {"id": user_id}
        delete_result = db_manager.delete_entity("users", conditions)

        assert delete_result["success"] is True
        assert delete_result["affected_rows"] == 1
        assert len(delete_result["deleted"]) == 1
        assert delete_result["deleted"][0]["id"] == user_id


@pytest.mark.integration
class TestDatabaseQueries:
    """Test various database queries"""

    @pytest.fixture
    def db_manager(self, test_database_config, clean_test_database):
        """Create database manager for tests"""
        config = PostgresConfig(**test_database_config)
        manager = DatabaseManager(config)
        manager.connection.connect()
        yield manager
        manager.connection.disconnect()

    def test_get_tables(self, db_manager):
        """Test getting list of tables"""
        result = db_manager.get_tables()

        assert result["success"] is True
        assert "tables" in result
        assert isinstance(result["tables"], list)
        # Should contain our test tables
        expected_tables = ["users", "products", "orders"]
        for table in expected_tables:
            assert table in result["tables"]

    def test_execute_custom_query(self, db_manager):
        """Test executing custom SQL queries"""
        query = "SELECT COUNT(*) as user_count FROM users"
        result = db_manager.connection.execute_query(query)

        assert isinstance(result, list)
        assert len(result) == 1
        assert "user_count" in result[0]
        assert isinstance(result[0]["user_count"], int)

    def test_execute_insert_query(self, db_manager):
        """Test executing INSERT query"""
        query = """
        INSERT INTO products (name, price, description) 
        VALUES (%(name)s, %(price)s, %(description)s)
        RETURNING *
        """
        params = {
            "name": "Test Product",
            "price": 49.99,
            "description": "Test product for integration testing",
        }

        result = db_manager.connection.execute_query(query, params)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["name"] == "Test Product"
        # PostgreSQL returns DECIMAL type, so we need to convert for comparison
        assert float(result[0]["price"]) == 49.99


@pytest.mark.integration
class TestDatabaseErrorHandling:
    """Test database error handling"""

    @pytest.fixture
    def db_manager(self, test_database_config, clean_test_database):
        """Create database manager for tests"""
        config = PostgresConfig(**test_database_config)
        manager = DatabaseManager(config)
        manager.connection.connect()
        yield manager
        manager.connection.disconnect()

    def test_invalid_table_name(self, db_manager):
        """Test operations with invalid table name"""
        result = db_manager.read_entity("nonexistent_table")

        assert result["success"] is False
        assert "error" in result
        assert "nonexistent_table" in result["error"].lower()

    def test_invalid_column_name(self, db_manager):
        """Test operations with invalid column name"""
        conditions = {"invalid_column": "value"}
        result = db_manager.read_entity("users", conditions=conditions)

        assert result["success"] is False
        assert "error" in result

    def test_malformed_query(self, db_manager):
        """Test executing malformed SQL query"""
        query = "SELECT * FROM invalid_syntax"

        with pytest.raises(DatabaseError):
            db_manager.connection.execute_query(query)

    def test_empty_conditions(self, db_manager):
        """Test operations with empty conditions"""
        # Empty conditions should return all records (with limit)
        result = db_manager.read_entity("users", conditions={})

        assert result["success"] is True
        assert result["count"] <= 100  # Default limit


@pytest.mark.integration
class TestDatabaseTransactions:
    """Test database transaction behavior"""

    @pytest.fixture
    def db_manager(self, test_database_config, clean_test_database):
        """Create database manager for tests"""
        config = PostgresConfig(**test_database_config)
        manager = DatabaseManager(config)
        manager.connection.connect()
        yield manager
        manager.connection.disconnect()

    def test_transaction_rollback(self, db_manager):
        """Test that failed transactions are rolled back"""
        # Get initial count
        initial_result = db_manager.read_entity("users")
        initial_count = initial_result["count"]

        # Try to insert with invalid data (should fail)
        invalid_data = {"invalid_column": "value"}
        try:
            db_manager.create_entity("users", invalid_data)
        except Exception:
            pass  # Expected to fail

        # Count should remain the same
        final_result = db_manager.read_entity("users")
        final_count = final_result["count"]

        assert initial_count == final_count, "Transaction should have been rolled back"


@pytest.mark.integration
class TestTableManagement:
    """Test table management operations"""

    @pytest.fixture
    def db_manager(self, test_database_config, clean_test_database):
        """Create database manager for tests"""
        config = PostgresConfig(**test_database_config)
        manager = DatabaseManager(config)
        manager.connection.connect()
        yield manager
        manager.connection.disconnect()

    def test_create_table(self, db_manager):
        """Test creating a new table"""
        table_name = "test_create_table"
        columns = [
            {"name": "id", "type": "SERIAL", "primary_key": True},
            {"name": "name", "type": "VARCHAR(100)", "nullable": False},
            {"name": "description", "type": "TEXT", "nullable": True},
            {"name": "created_at", "type": "TIMESTAMP", "default": "NOW()"},
        ]

        result = db_manager.create_table(table_name, columns)

        assert result["success"] is True
        assert f"Table {table_name} created successfully" in result["message"]

        # Verify table exists
        tables_result = db_manager.get_tables()
        assert table_name in tables_result["tables"]

    def test_create_table_if_not_exists(self, db_manager):
        """Test creating table with IF NOT EXISTS"""
        table_name = "test_if_not_exists"
        columns = [
            {"name": "id", "type": "INTEGER", "primary_key": True},
            {"name": "value", "type": "VARCHAR(50)"},
        ]

        # Create table first time
        result1 = db_manager.create_table(table_name, columns, if_not_exists=True)
        assert result1["success"] is True

        # Try to create again with IF NOT EXISTS (should succeed)
        result2 = db_manager.create_table(table_name, columns, if_not_exists=True)
        assert result2["success"] is True

    def test_alter_table_add_column(self, db_manager):
        """Test adding a column to existing table"""
        # First create a table
        table_name = "test_alter_table"
        columns = [
            {"name": "id", "type": "SERIAL", "primary_key": True},
            {"name": "name", "type": "VARCHAR(100)"},
        ]
        db_manager.create_table(table_name, columns)

        # Add a new column
        operations = [
            {
                "type": "add_column",
                "column_name": "email",
                "data_type": "VARCHAR(255)",
                "nullable": True,
            }
        ]

        result = db_manager.alter_table(table_name, operations)
        assert result["success"] is True

    def test_alter_table_drop_column(self, db_manager):
        """Test dropping a column from existing table"""
        # First create a table with multiple columns
        table_name = "test_drop_column"
        columns = [
            {"name": "id", "type": "SERIAL", "primary_key": True},
            {"name": "name", "type": "VARCHAR(100)"},
            {"name": "temp_column", "type": "VARCHAR(50)"},
        ]
        db_manager.create_table(table_name, columns)

        # Drop the temporary column
        operations = [
            {
                "type": "drop_column",
                "column_name": "temp_column",
            }
        ]

        result = db_manager.alter_table(table_name, operations)
        assert result["success"] is True

    def test_alter_table_rename_column(self, db_manager):
        """Test renaming a column"""
        # First create a table
        table_name = "test_rename_column"
        columns = [
            {"name": "id", "type": "SERIAL", "primary_key": True},
            {"name": "old_name", "type": "VARCHAR(100)"},
        ]
        db_manager.create_table(table_name, columns)

        # Rename the column
        operations = [
            {
                "type": "rename_column",
                "column_name": "old_name",
                "new_column_name": "new_name",
            }
        ]

        result = db_manager.alter_table(table_name, operations)
        assert result["success"] is True

    def test_alter_table_alter_column(self, db_manager):
        """Test altering column properties"""
        # First create a table
        table_name = "test_alter_column"
        columns = [
            {"name": "id", "type": "SERIAL", "primary_key": True},
            {"name": "description", "type": "VARCHAR(100)", "nullable": True},
        ]
        db_manager.create_table(table_name, columns)

        # Alter the column
        operations = [
            {
                "type": "alter_column",
                "column_name": "description",
                "data_type": "TEXT",
                "nullable": False,
            }
        ]

        result = db_manager.alter_table(table_name, operations)
        assert result["success"] is True

    def test_drop_table(self, db_manager):
        """Test dropping a table"""
        # First create a table
        table_name = "test_drop_table"
        columns = [
            {"name": "id", "type": "SERIAL", "primary_key": True},
            {"name": "data", "type": "VARCHAR(100)"},
        ]
        db_manager.create_table(table_name, columns)

        # Verify table exists
        tables_result = db_manager.get_tables()
        assert table_name in tables_result["tables"]

        # Drop the table
        result = db_manager.drop_table(table_name)
        assert result["success"] is True

        # Verify table no longer exists
        tables_result = db_manager.get_tables()
        assert table_name not in tables_result["tables"]

    def test_drop_table_if_exists(self, db_manager):
        """Test dropping non-existent table with IF EXISTS"""
        result = db_manager.drop_table("non_existent_table", if_exists=True)
        assert result["success"] is True

    def test_invalid_table_name(self, db_manager):
        """Test operations with invalid table name"""
        columns = [{"name": "id", "type": "INTEGER"}]
        
        with pytest.raises(DatabaseError):
            db_manager.create_table("invalid-table-name", columns)

    def test_invalid_column_name(self, db_manager):
        """Test operations with invalid column name"""
        table_name = "test_invalid_column"
        columns = [{"name": "invalid-column", "type": "INTEGER"}]
        
        with pytest.raises(DatabaseError):
            db_manager.create_table(table_name, columns)

    def test_empty_columns(self, db_manager):
        """Test creating table with no columns"""
        with pytest.raises(DatabaseError):
            db_manager.create_table("empty_table", [])

    def test_empty_operations(self, db_manager):
        """Test altering table with no operations"""
        table_name = "test_empty_ops"
        columns = [{"name": "id", "type": "INTEGER"}]
        db_manager.create_table(table_name, columns)
        
        with pytest.raises(DatabaseError):
            db_manager.alter_table(table_name, [])
