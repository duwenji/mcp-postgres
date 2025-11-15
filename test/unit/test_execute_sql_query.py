"""
Unit tests for execute_sql_query tool
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.mcp_postgres_duwenji.tools.crud_tools import handle_execute_sql_query
from src.mcp_postgres_duwenji.database import DatabaseError


class TestExecuteSqlQuery:
    """Test cases for execute_sql_query tool"""

    @pytest.mark.asyncio
    async def test_execute_sql_query_success(self):
        """Test successful SQL query execution"""
        # Mock data
        mock_query = "SELECT * FROM users WHERE age > %(min_age)s"
        mock_params = {"min_age": 18}
        mock_limit = 100
        
        # Mock database result
        mock_result = {
            "success": True,
            "data": [
                {"id": 1, "name": "John", "age": 25},
                {"id": 2, "name": "Jane", "age": 30}
            ],
            "columns": ["id", "name", "age"],
            "row_count": 2,
            "query": mock_query + " LIMIT 100"
        }

        with patch('src.mcp_postgres_duwenji.tools.crud_tools.load_config') as mock_load_config, \
             patch('src.mcp_postgres_duwenji.tools.crud_tools.DatabaseManager') as mock_db_manager_class:
            
            # Mock config
            mock_config = Mock()
            mock_config.postgres = Mock()
            mock_load_config.return_value = mock_config
            
            # Mock database manager
            mock_db_manager = Mock()
            mock_db_manager_class.return_value = mock_db_manager
            mock_db_manager.execute_query.return_value = mock_result
            
            # Execute the handler
            result = await handle_execute_sql_query(mock_query, mock_params, mock_limit)
            
            # Assertions
            assert result["success"] is True
            assert result["data"] == mock_result["data"]
            assert result["columns"] == mock_result["columns"]
            assert result["row_count"] == mock_result["row_count"]
            
            # Verify database manager was called correctly
            mock_db_manager.connect.assert_called_once()
            mock_db_manager.execute_query.assert_called_once_with(mock_query, mock_params, mock_limit)
            mock_db_manager.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_sql_query_without_params(self):
        """Test SQL query execution without parameters"""
        # Mock data
        mock_query = "SELECT * FROM users"
        mock_limit = 50
        
        # Mock database result
        mock_result = {
            "success": True,
            "data": [
                {"id": 1, "name": "John"},
                {"id": 2, "name": "Jane"}
            ],
            "columns": ["id", "name"],
            "row_count": 2,
            "query": mock_query + " LIMIT 50"
        }

        with patch('src.mcp_postgres_duwenji.tools.crud_tools.load_config') as mock_load_config, \
             patch('src.mcp_postgres_duwenji.tools.crud_tools.DatabaseManager') as mock_db_manager_class:
            
            # Mock config
            mock_config = Mock()
            mock_config.postgres = Mock()
            mock_load_config.return_value = mock_config
            
            # Mock database manager
            mock_db_manager = Mock()
            mock_db_manager_class.return_value = mock_db_manager
            mock_db_manager.execute_query.return_value = mock_result
            
            # Execute the handler without parameters
            result = await handle_execute_sql_query(mock_query, None, mock_limit)
            
            # Assertions
            assert result["success"] is True
            assert result["data"] == mock_result["data"]
            
            # Verify database manager was called with None params
            mock_db_manager.execute_query.assert_called_once_with(mock_query, None, mock_limit)

    @pytest.mark.asyncio
    async def test_execute_sql_query_database_error(self):
        """Test SQL query execution with database error"""
        # Mock data
        mock_query = "SELECT * FROM non_existent_table"
        mock_params = {}
        mock_limit = 100
        
        # Mock database error
        mock_error = DatabaseError("Table 'non_existent_table' does not exist")

        with patch('src.mcp_postgres_duwenji.tools.crud_tools.load_config') as mock_load_config, \
             patch('src.mcp_postgres_duwenji.tools.crud_tools.DatabaseManager') as mock_db_manager_class:
            
            # Mock config
            mock_config = Mock()
            mock_config.postgres = Mock()
            mock_load_config.return_value = mock_config
            
            # Mock database manager to raise error
            mock_db_manager = Mock()
            mock_db_manager_class.return_value = mock_db_manager
            mock_db_manager.execute_query.side_effect = mock_error
            
            # Execute the handler
            result = await handle_execute_sql_query(mock_query, mock_params, mock_limit)
            
            # Assertions
            assert result["success"] is False
            assert "error" in result
            assert "Table 'non_existent_table' does not exist" in result["error"]
            
            # Verify database manager was called
            mock_db_manager.connect.assert_called_once()
            mock_db_manager.execute_query.assert_called_once_with(mock_query, mock_params, mock_limit)
            # disconnect() should be called even when there's an error
            mock_db_manager.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_sql_query_unexpected_error(self):
        """Test SQL query execution with unexpected error"""
        # Mock data
        mock_query = "SELECT * FROM users"
        mock_params = {}
        mock_limit = 100
        
        # Mock unexpected error
        mock_error = Exception("Unexpected system error")

        with patch('src.mcp_postgres_duwenji.tools.crud_tools.load_config') as mock_load_config, \
             patch('src.mcp_postgres_duwenji.tools.crud_tools.DatabaseManager') as mock_db_manager_class:
            
            # Mock config
            mock_config = Mock()
            mock_config.postgres = Mock()
            mock_load_config.return_value = mock_config
            
            # Mock database manager to raise unexpected error
            mock_db_manager = Mock()
            mock_db_manager_class.return_value = mock_db_manager
            mock_db_manager.execute_query.side_effect = mock_error
            
            # Execute the handler
            result = await handle_execute_sql_query(mock_query, mock_params, mock_limit)
            
            # Assertions
            assert result["success"] is False
            assert "error" in result
            assert "Internal server error" in result["error"]
            assert "Unexpected system error" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_sql_query_with_existing_limit(self):
        """Test SQL query that already has LIMIT clause"""
        # Mock data - query already has LIMIT
        mock_query = "SELECT * FROM users LIMIT 10"
        mock_params = {}
        mock_limit = 100  # This should be ignored since query already has LIMIT
        
        # Mock database result
        mock_result = {
            "success": True,
            "data": [{"id": 1, "name": "John"}],
            "columns": ["id", "name"],
            "row_count": 1,
            "query": mock_query  # Should remain unchanged
        }

        with patch('src.mcp_postgres_duwenji.tools.crud_tools.load_config') as mock_load_config, \
             patch('src.mcp_postgres_duwenji.tools.crud_tools.DatabaseManager') as mock_db_manager_class:
            
            # Mock config
            mock_config = Mock()
            mock_config.postgres = Mock()
            mock_load_config.return_value = mock_config
            
            # Mock database manager
            mock_db_manager = Mock()
            mock_db_manager_class.return_value = mock_db_manager
            mock_db_manager.execute_query.return_value = mock_result
            
            # Execute the handler
            result = await handle_execute_sql_query(mock_query, mock_params, mock_limit)
            
            # Assertions
            assert result["success"] is True
            assert result["query"] == mock_query  # Query should not be modified
            
            # Verify database manager was called with original query
            mock_db_manager.execute_query.assert_called_once_with(mock_query, mock_params, mock_limit)

    @pytest.mark.asyncio
    async def test_execute_sql_query_empty_result(self):
        """Test SQL query with empty result"""
        # Mock data
        mock_query = "SELECT * FROM users WHERE age > 100"
        mock_params = {}
        mock_limit = 100
        
        # Mock empty result
        mock_result = {
            "success": True,
            "data": [],
            "columns": [],
            "row_count": 0,
            "query": mock_query + " LIMIT 100"
        }

        with patch('src.mcp_postgres_duwenji.tools.crud_tools.load_config') as mock_load_config, \
             patch('src.mcp_postgres_duwenji.tools.crud_tools.DatabaseManager') as mock_db_manager_class:
            
            # Mock config
            mock_config = Mock()
            mock_config.postgres = Mock()
            mock_load_config.return_value = mock_config
            
            # Mock database manager
            mock_db_manager = Mock()
            mock_db_manager_class.return_value = mock_db_manager
            mock_db_manager.execute_query.return_value = mock_result
            
            # Execute the handler
            result = await handle_execute_sql_query(mock_query, mock_params, mock_limit)
            
            # Assertions
            assert result["success"] is True
            assert result["data"] == []
            assert result["row_count"] == 0
            assert result["columns"] == []

    def test_execute_sql_query_tool_definition(self):
        """Test that execute_sql_query tool is properly defined"""
        from src.mcp_postgres_duwenji.tools.crud_tools import execute_sql_query, get_crud_tools
        
        # Check tool definition
        assert execute_sql_query.name == "execute_sql_query"
        assert "Execute a SQL query and return results" in execute_sql_query.description
        
        # Check input schema
        schema = execute_sql_query.inputSchema
        assert schema["type"] == "object"
        assert "query" in schema["required"]
        assert "params" in schema["properties"]
        assert "limit" in schema["properties"]
        
        # Check tool is included in CRUD tools
        crud_tools = get_crud_tools()
        tool_names = [tool.name for tool in crud_tools]
        assert "execute_sql_query" in tool_names

    def test_execute_sql_query_handler_registration(self):
        """Test that execute_sql_query handler is properly registered"""
        from src.mcp_postgres_duwenji.tools.crud_tools import get_crud_handlers
        
        handlers = get_crud_handlers()
        assert "execute_sql_query" in handlers
        assert handlers["execute_sql_query"] == handle_execute_sql_query
